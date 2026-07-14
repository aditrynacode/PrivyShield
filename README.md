# PrivyShield 🛡️

**An on-device AI tool that automatically detects and blurs sensitive information on your screen — Aadhaar numbers, PAN cards, credit cards, emails, phone numbers, OTPs, names, and addresses; in real time, completely offline.**

Built for **OSDHack 2026** (theme: On-Device AI), organized by the Open Source Developers Community (OSDC).

> **Status: Mid-hackathon checkpoint.** This README reflects where the project stands right now, the detection engine is built and working, the visual overlay is what I'm building next. I'll keep updating this file as the project progresses.

---

## The problem

We leak sensitive info from our screens constantly without realizing it; screen-sharing on a call with a banking tab open, sharing a screenshot for a support ticket that still shows a card number, that kind of thing. Most tools that could catch this would need to send your screen content to a cloud server to analyze it, which defeats the whole point when the content is *literally your Aadhaar number*.

## The idea

PrivyShield watches your screen locally and blurs sensitive information the moment it appears, using on-device OCR + AI, nothing ever leaves your machine. Not a screenshot, not a snippet of text, nothing.

I'm building it as layered protection, since sensitive data leaks from more than one place:

| Layer | Status | What it does |
|---|---|---|
| **Layer 1: Screen Shield** | Detection engine done, overlay UI in progress | Live screen capture → OCR → PII detection → blur overlay |
| **Layer 2: Clipboard Guard** | Planned | Warns you before pasting something sensitive you copied |
| **Layer 3: Screen-Share Mode** | Planned | Extra-aggressive blurring specifically for video calls |
| **Layer 4: Redaction Export Tool** | Planned | Drop in a screenshot/PDF, get back a redacted version |
| **Layer 5: Risk Dashboard** | Future idea | Local-only log of what's been flagged over time |

---

## What's actually working right now

The full **detection pipeline** for Layer 1 is built and tested end-to-end. Here's how it works, in order:

1. **Screen capture**: grabs the current screen as raw pixels using `mss` (deliberately not OpenCV, wasn't sure if using OpenCV is allowed)
2. **OCR**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) reads all visible text off the captured frame and gives back each detected line along with exactly where it is on screen (bounding box) and how confident it is
3. **Structured PII detection (regex)**: every OCR'd line gets checked against regex patterns for Aadhaar numbers, PAN cards, credit cards (validated with the Luhn algorithm to cut down false positives), emails, phone numbers, and OTP-like codes. These have fixed formats, so a trained model isn't necessary here — plain pattern matching is faster and just as reliable.
4. **Unstructured PII detection (my trained model)**: names and addresses *don't* follow a fixed format, so regex can't catch them. For this, I fine-tuned a `distilbert-base-uncased` model to do token classification (NER) specifically for `PERSON_NAME` and `ADDRESS` detection.
   - Trained on **7,500 synthetically generated, auto-labeled sentences**: I built a generator that combines realistic Indian names/addresses/cities into varied sentence templates and auto-labels the entity spans as it builds them, so there was no manual annotation involved at all
   - Exported to **ONNX** for fast local inference
   - Predictions below a confidence threshold get dropped, so the model doesn't over-flag things it's unsure about
5. **Fusion**: regex hits and NER hits both get merged per OCR line; if a line contains *any* sensitive detection, the whole line's bounding box gets flagged for blurring

Every one of these pieces runs **locally**, nothing gets sent anywhere. That's the whole point.

The piece that's *not* done yet is the actual visual overlay (a transparent always-on-top window that draws the blur on top of the real screen); that's what I'm building next.

---

## On-device AI, specifically

Two models, chained together, both running fully on-device:

- **PaddleOCR**: pretrained, downloaded once and cached locally, handles document orientation + text detection + text recognition
- **My custom NER model**: trained from scratch by me for this project specifically (not a generic off-the-shelf model), fine-tuned on synthetic data, exported to ONNX
  - Model weights: [Hugging Face link](https://huggingface.co/aditrynacode/privyshield-ner/tree/main)

## Tech stack

| Component | Tool |
|---|---|
| Screen capture | [`mss`](https://github.com/BoboTiG/python-mss) |
| OCR (pretrained) | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) |
| Structured PII | Python `re` + Luhn algorithm |
| Unstructured PII (my model) | Fine-tuned DistilBERT → ONNX |
| Blur/redaction | Pillow *(next up)* |
| Overlay UI | PyQt/PySide *(next up)* |
| Clipboard monitor | `pyperclip` *(planned)* |
| PDF handling | PyMuPDF *(planned)* |
| Local logging | `sqlite3` *(planned)* |

## Project structure

```
PrivyShield/
├── detection/              # The core detection engine (done)
│   ├── __init__.py
│   ├── capture.py          # Screen capture via mss
│   ├── ocr_engine.py       # PaddleOCR wrapper
│   ├── regex_pii.py        # Structured PII detectors + Luhn validation
│   ├── ner_inference.py    # ONNX NER model wrapper
│   ├── geometry.py         # Bounding box helpers
│   └── pipeline.py         # Fuses OCR + regex + NER together
├── NER/
│   ├── dataset_generator.py   # Synthetic training data generator
│   └── train.py     # NER training + ONNX export
├── models/                  # Trained model files (not committed — see Setup)
├── data/                    # Generated training data (not committed — see Setup)
├── app/                     # Overlay UI — in progress
├── README.md
└── LICENSE
```

## Setup

```bash
git clone https://github.com/aditrynacode/PrivyShield.git
cd PrivyShield
pip install -r requirements.txt
```

**Getting the model weights:** I didn't commit the trained model files directly to this repo (they're binary and bulky, and Git isn't great at handling that) — instead they're hosted on Hugging Face:

```bash
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='aditrynacode/privyshield-ner', filename='ner_model.onnx', local_dir='models/')"
```

Or you can reproduce the whole thing from scratch yourself:
```bash
python NER/dataset_generator.py
python NER/train.py
```

> **Heads up on first run:** PaddleOCR downloads its detection/recognition models (~200MB total) the very first time it runs, then caches them locally on your machine. Every run after that is fully offline; no internet connection needed for PrivyShield to actually work. This is a one-time setup cost, not a runtime dependency.

## Usage

The detection pipeline itself is fully functional right now; you can call it directly:

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

*(Full app usage instructions will go here once the overlay UI is wired up.)*

## Demo video

*(Coming as the project nears completion)*

## Screenshots

*(Coming soon)*

## License

*(Adding an OSI-compliant license shortly; MIT or Apache-2.0)*

## Known limitations (being upfront about this)

- The NER model is trained on synthetic data, so real-world OCR noise (typos, weird formatting) might trip it up more than my clean test cases did
- English only, for now
- Name/address detection is currently trained on synthetic data

## Where this could go

- Browser extension version
- Enterprise data-loss-prevention (DLP) tooling
- Multi-language support

---

Built by [Aditya](https://github.com/aditrynacode) for OSDHack 2026 🚀