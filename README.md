# 🛡️ PrivyShield

PrivyShield is an AI-powered screen privacy tool that runs completely offline to detect and mask sensitive information displayed on your screen in real time. The project is designed to prevent accidental exposure of personal or confidential information during screen sharing, recordings, presentations, or live demonstrations.

> **Privacy first. Everything runs locally. No cloud processing. No data leaves your device.**

---

## Features

-  Real-time detection of sensitive information
-  Detects personal names using a custom NER model
-  Detects addresses using OCR + NER
-  Screen/image processing pipeline
-  Automatic masking of detected regions
-  Fully offline inference
-  Modular architecture for easy extension

---

## Project Structure

```
PrivyShield/
│
├── detection/          # OCR, NER and detection pipeline
├── training/           # Model training scripts
├── models/             # Trained model weights
├── datasets/           # Dataset generation utilities
├── utils/              # Helper functions
├── test_pipeline.py    # Example inference script
├── requirements.txt
└── README.md
```

---

## Current Pipeline

```
Input Image / Screen
        │
        ▼
     PaddleOCR
        │
        ▼
Extracted Text + Bounding Boxes
        │
        ▼
Custom BERT NER Model
        │
        ▼
Sensitive Entity Detection
        │
        ▼
Bounding Box Generation
        │
        ▼
Blur / Mask Sensitive Regions
```

---

## Tech Stack

- Python
- PyTorch
- Hugging Face Transformers
- PaddleOCR
- OpenCV
- NumPy

---

## Current Capabilities

Currently supported entity types:

- Person Names
- Addresses

More entity types will be added in future releases.

---

## Installation

Clone the repository

```bash
git clone https://github.com/aditrynacode/PrivyShield.git
cd PrivyShield
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

Run the example pipeline

```bash
python test_pipeline.py
```

---

## Roadmap

- [x] OCR integration
- [x] Custom NER model
- [x] Person name detection
- [x] Address detection
- [x] End-to-end detection pipeline
- [ ] Real-time desktop capture
- [ ] Live screen masking
- [ ] Additional sensitive entity types
- [ ] GUI application
- [ ] Cross-platform support
- [ ] Browser extension
- [ ] Performance optimization

---

## Motivation

Screen sharing has become a part of everyday work, but it often exposes private information unintentionally. PrivyShield aims to act as a real-time privacy layer by automatically detecting and hiding sensitive content before it can be seen by others.

---

## Disclaimer

This project is under active development. Features, APIs, and project structure may change frequently.

---

## License

This project is licensed under the MIT License.