import argparse
import os
import pickle
import sys
 
import numpy as np
from PIL import Image, ImageDraw
 
from detection import detect_sensitive_regions, NERPredictor

CONFIDENCE_THRESHOLD = 0.95
REDACT_PAD = 4

def load_ner_predictor():
    with open("data/label_config.pkl", "rb") as f:
        label_config = pickle.load(f)
 
    return NERPredictor(
        onnx_path="models/ner_model.onnx",
        tokenizer_path="models/ner_model",
        id2label=label_config["id2label"],
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )

def redact_image(pil_image, ner_predictor):

    rgb_image = pil_image.convert("RGB")
    frame = np.array(rgb_image)  
 
    regions = detect_sensitive_regions(frame, ner_predictor=ner_predictor)
 
    redacted = rgb_image.copy()
    draw = ImageDraw.Draw(redacted)
 
    width, height = redacted.size
    for region in regions:
        x_min, y_min, x_max, y_max = region["bbox"]
        box = (
            max(0, x_min - REDACT_PAD),
            max(0, y_min - REDACT_PAD),
            min(width, x_max + REDACT_PAD),
            min(height, y_max + REDACT_PAD),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            continue

        draw.rectangle(box, fill="black")
 
    return redacted, len(regions)
 
 
def redact_image_file(input_path, output_path, ner_predictor):
    pil_image = Image.open(input_path)
    redacted, count = redact_image(pil_image, ner_predictor)
    redacted.save(output_path)
    return count
 
 
def redact_pdf_file(input_path, output_path, ner_predictor):
    import fitz 
 
    src = fitz.open(input_path)
    total_regions = 0
    zoom = 2.0  
    matrix = fitz.Matrix(zoom, zoom)
 
    out = fitz.open()
    for page in src:
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
 
        redacted, count = redact_image(img, ner_predictor)
        total_regions += count
 
        img_bytes = redacted.tobytes()
        new_page = out.new_page(width=page.rect.width, height=page.rect.height)

        img_stream = _pil_to_png_bytes(redacted)
        new_page.insert_image(page.rect, stream=img_stream)
 
    out.save(output_path)
    out.close()
    src.close()
    return total_regions
 
 
def _pil_to_png_bytes(pil_image):
    import io
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()
 
 
def main():
    parser = argparse.ArgumentParser(
        description="PrivyShield redaction export tool; blacks out detected PII in an image or PDF."
    )
    parser.add_argument("input", help="Path to input image (.png/.jpg) or PDF")
    parser.add_argument("output", help="Path to write the redacted output")
    args = parser.parse_args()
 
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)
 
    print("Loading NER model...")
    ner_predictor = load_ner_predictor()
 
    ext = os.path.splitext(args.input)[1].lower()
    print(f"Processing {args.input}...")
 
    if ext == ".pdf":
        count = redact_pdf_file(args.input, args.output, ner_predictor)
    else:
        count = redact_image_file(args.input, args.output, ner_predictor)
 
    print(f"Done — {count} sensitive region(s) redacted.")
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()