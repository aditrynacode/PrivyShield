# PrivyShield 🛡️

**An on-device AI tool that automatically detects and blurs sensitive information on your screen: Aadhaar numbers, PAN cards, credit cards, emails, phone numbers, OTPs, names, and addresses; in real time, completely offline.**

Built for **OSDHack 2026** (theme: On-Device AI), organized by the Open Source Developers Community (OSDC).

---

## The problem

We leak sensitive info from our screens constantly without realizing it; screen-sharing on a call with a banking tab open, sharing a screenshot for a support ticket that still shows a card number, that kind of thing. Most tools that could catch this would need to send your screen content to a cloud server to analyze it, which defeats the whole point when the content is *literally your Aadhaar number*.

## The idea

PrivyShield watches your screen locally and blurs sensitive information the moment it appears, using on-device OCR + AI, nothing ever leaves your machine. Not a screenshot, not a snippet of text, nothing.

Sensitive data leaks from more than one place, so PrivyShield is built as layered protection:

| Layer | Status | What it does |
|---|---|---|
| **Layer 1: Screen Shield** | ✅ Done | Live screen capture → OCR → PII detection → live blur overlay, with a system tray toggle |
| **Layer 4: Redaction Export Tool** | ✅ Done | Drop in an image, get back a version with all detected PII blacked out |
| **Layer 2: Clipboard Guard** | ✅ Done | Warns you locally before you paste something sensitive you just copied |
| **Web Demo (Flask)** | ✅ Done | Local Flask web UI: upload a file to get a redacted copy back, and toggle the live overlay on/off, all from your browser, all local |
| **Layer 3: Screen-Share Mode** | 🗺️ Roadmap | Extra-aggressive blurring specifically tuned for video calls |
| **Layer 5: Risk Dashboard** | 🗺️ Roadmap | Local-only log of what kinds of PII get flagged over time, no content stored |

---

## How it works

1. **Screen capture**: grabs the current screen as raw pixels using `mss` (deliberately not OpenCV, since I wasn't sure if that dependency is allowed)
2. **OCR**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) reads all visible text off the captured frame and returns each detected line along with its bounding box and confidence
3. **Structured PII detection (regex)**: every OCR'd line is checked against patterns for Aadhaar numbers, PAN cards, credit cards (validated with the Luhn algorithm to cut false positives), emails, phone numbers, and OTP-like codes near an OTP/verification keyword. These have fixed formats, so a trained model isn't necessary here; plain pattern matching is faster and just as reliable.
4. **Unstructured PII detection (my trained model)**: names and addresses *don't* follow a fixed format, so regex can't catch them. I fine-tuned a `distilbert-base-uncased` model to do token classification (NER) specifically for `PERSON_NAME` and `ADDRESS` detection.
   - Trained on **7,500 synthetically generated, auto-labeled sentences**: a generator combines realistic Indian names/addresses/cities into varied sentence templates and auto-labels the entity spans as it builds them, so no manual annotation was involved
   - Exported to **ONNX** for fast local inference
   - Predictions below a confidence threshold are dropped, so the model doesn't over-flag things it's unsure about
5. **Fusion**: regex hits and NER hits are merged per OCR line; if a line contains *any* sensitive detection, its bounding box is flagged
6. **Overlay / redaction**: Layer 1 draws a live Gaussian blur over flagged regions on a transparent, click-through, always-on-top window; Layer 4 reuses the exact same detection pipeline on a static image or PDF and blacks out the flagged regions instead; the Web Demo reuses the same pipeline again, served through a local Flask app

Every piece runs **locally**, nothing gets sent anywhere. That's the whole point.

---

## On-device AI, specifically

Two models, chained together, both running fully on-device:

- **PaddleOCR**: pretrained, downloaded once and cached locally. Uses the `PP-OCRv5_mobile` detection + recognition models (deliberately the lightweight variant, not the larger `medium` models; see [Performance](#performance-notes) below for why) with document-photo preprocessing (orientation classification, unwarping) disabled, since a screen capture is already flat and upright and doesn't need it.
- **My custom NER model**, trained from scratch by me for this project specifically, not a generic off-the-shelf model. Fine-tuned `distilbert-base-uncased` on 7,500 synthetic examples, exported to ONNX.
  - Entity-level F1 (from `seqeval`, on the held-out test split): **[insert your number from `train.py`'s printed classification report here]**
  - Average inference time per line: **~14-15ms** (measured on the author's machine, CPU)
  - Model weights: [Hugging Face link](https://huggingface.co/aditrynacode/privyshield-ner/tree/main)

## Tech stack

| Component | Tool |
|---|---|
| Screen capture | [`mss`](https://github.com/BoboTiG/python-mss) |
| OCR (pretrained) | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) |
| Structured PII | Python `re` + Luhn algorithm |
| Unstructured PII (my model) | Fine-tuned DistilBERT → ONNX, served via `onnxruntime` |
| Blur / redaction | Pillow |
| Overlay UI | PyQt5 |
| Clipboard monitor | `pyperclip` |
| PDF handling | PyMuPDF |
| Web demo | Flask |

## Project structure

```
PrivyShield/
├── detection/               # Core detection engine
│   ├── __init__.py
│   ├── capture.py           # Screen capture via mss
│   ├── ocr_engine.py        # PaddleOCR wrapper
│   ├── regex_pii.py         # Structured PII detectors + Luhn validation
│   ├── ner_inference.py     # ONNX NER model wrapper
│   ├── geometry.py          # Bounding box helpers
│   └── pipeline.py          # Fuses OCR + regex + NER together
├── NER/
│   ├── dataset_generator.py # Synthetic training data generator
│   └── train.py             # NER training + ONNX export
├── app/                     # User-facing features
│   ├── __init__.py
│   ├── overlay.py           # Layer 1: live screen overlay + system tray
│   ├── redact.py            # Layer 4: redaction export (image)
│   ├── clipboard_guard.py   # Layer 2: clipboard monitor
│   └── web_demo.py          # Local Flask web UI: upload/redact files, toggle overlay
├── models/                  # Trained model files (not committed, see Setup)
├── data/                    # Generated training data (not committed, see Setup)
├── README.md
└── LICENSE
```

## Setup

This project uses two virtual environments due to a dependency conflict
between PyTorch and PaddlePaddle on Windows.

### Environment 1: Running the app (this is all most judges need)

Since the trained model weights are already hosted on Hugging Face (see below), you don't need to touch the training pipeline at all to run and evaluate PrivyShield, this environment is enough on its own.

```bash
git clone https://github.com/aditrynacode/PrivyShield.git
cd PrivyShield
python -m venv venv-app
venv-app\Scripts\activate
pip install -r requirements-app.txt
```

**Getting the model weights**: the trained NER model isn't committed to this repo (binary and bulky), it's hosted on Hugging Face:

```bash
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='aditrynacode/privyshield-ner', filename='ner_model.onnx', local_dir='models/')"
```

Then run:
```bash
python -m app.overlay
```

> **Heads up on first run:** PaddleOCR downloads its detection/recognition models the first time it runs, then caches them locally. Every run after that is fully offline, no internet connection needed for PrivyShield to actually work. This is a one-time setup cost, not a runtime dependency.

### Environment 2: Reproducing the NER model from scratch (optional)

Only needed if you specifically want to verify the training pipeline itself, not just run the app. Uses a **separate** virtual environment; see why below.

```bash
python -m venv venv-train
venv-train\Scripts\activate
pip install -r requirements-train.txt
python NER/dataset_generator.py
python NER/train.py
```

> **Why two environments?** `NER/train.py` needs PyTorch; the running app (`app/overlay.py`) only needs `onnxruntime` and doesn't need PyTorch at all. On Windows, having both `torch` and `paddlepaddle-gpu` installed together in one environment can cause a `cudnn` DLL loading conflict, since both packages pull in `nvidia-cudnn-cu12` but expect different versions. Splitting into two environments sidesteps this cleanly, and since most evaluators only need the app environment above (model weights are already hosted, not something you need to train yourself), this split adds essentially zero friction for actually running the project.

## Usage

**Web Demo (browser-based, local only):**
```bash
python -m app.web_demo
```
Hosts the project locally and prints a link in the terminal. Open that link in your browser to upload a screenshot or PDF and get back its redacted version, and to toggle the live overlay on or off, all without touching the command line again. Everything still runs on your machine; the Flask server only serves the local page, nothing is sent externally.

**Screen Shield (live overlay):**
```bash
python -m app.overlay
```
Runs full-screen, blurring detected PII live. Right-click the tray icon to hide/show the overlay, pause/resume detection, or quit.

**Redaction export (screenshot → redacted copy):**
```bash
python -m app.redact path/to/input.png path/to/output.png
```

**Clipboard Guard:**
```bash
python -m app.clipboard_guard
```
Runs in the background and gives a local notification if you copy something that looks sensitive.

Or call the detection pipeline directly:
```python
from detection import detect_sensitive_regions, NERPredictor, grab_screen
import pickle

with open("data/label_config.pkl", "rb") as f:
    label_config = pickle.load(f)

ner = NERPredictor(
    onnx_path="models/ner_model.onnx",
    tokenizer_path="models/ner_model",
    id2label=label_config["id2label"],
)

frame = grab_screen()
regions = detect_sensitive_regions(frame, ner_predictor=ner)
for r in regions:
    print(r["bbox"], [d["type"] for d in r["detections"]])
```

## Performance notes

OCR is the dominant cost in the pipeline (regex and NER inference are both fast; NER averages ~14-15ms per detected text line). Measured end-to-end pipeline time on the author's machine (CPU-only inference, `PP-OCRv5_mobile` models):

- A text-dense desktop (a busy IDE + terminal + browser): roughly 3-4 seconds per full detection pass
- Lighter screens with less visible text will refresh noticeably faster, since OCR/NER cost scales with the number of text lines on screen, not a fixed interval

The live overlay's capture loop adapts to this automatically: it never sleeps longer than necessary, but it also can't refresh faster than a full detection pass takes. GPU acceleration was attempted but hit an environment-specific dependency conflict (see the note above); it remains a good next step for meaningfully lowering this number.

## Screenshots

<img width="445" height="272" alt="Screenshot 2026-07-15 144939" src="https://github.com/user-attachments/assets/00206ad0-42ba-4ad8-884d-bbae86edb58b" />
<img width="1092" height="432" alt="Screenshot 2026-07-15 144317" src="https://github.com/user-attachments/assets/feb6bff0-6059-49a4-9d38-2df3cd34db88" />
<img width="426" height="278" alt="Screenshot 2026-07-15 144545" src="https://github.com/user-attachments/assets/001eab0a-51ed-4e46-a539-310bce438fda" />

## License

Apache-2.0

## Known limitations (being upfront about this)

- **English only**, for now
- **OCR latency scales with on-screen text volume**: a very text-dense screen takes several seconds to fully re-scan; this is inherent to running OCR + NER locally on CPU rather than a fixed refresh bug
- **GPU acceleration isn't currently used**: attempted during development but ran into a `torch`/`paddlepaddle-gpu` dependency conflict specific to the author's environment; reverted to a reliable CPU-only pipeline in the interest of shipping a working submission

## Where this could go

- Resolve the GPU dependency conflict and/or batch NER inference across all OCR lines in one call, for a meaningfully faster refresh rate
- Layer 3: a screen-share-specific mode with more aggressive blurring
- Layer 5: a local-only risk dashboard (counts and categories only, no content stored)
- Browser extension version
- Enterprise data-loss-prevention (DLP) tooling
- Multi-language support

---

Built by [Aditya](https://github.com/aditrynacode) for OSDHack 2026 🚀
