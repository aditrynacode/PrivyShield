from paddleocr import PaddleOCR
 
_ocr_engine = None
 
def get_ocr_engine():

    global _ocr_engine
    if _ocr_engine is None:

        _ocr_engine = PaddleOCR(use_textline_orientation=True, lang="en", enable_mkldnn=False)
    return _ocr_engine
 
 
def run_ocr(image):

    engine = get_ocr_engine()
    pages = engine.predict(image)
 
    detections = []
    for page in pages:
        texts = page.get("rec_texts", [])
        boxes = page.get("rec_boxes", [])
        scores = page.get("rec_scores", [])
        for text, box, score in zip(texts, boxes, scores):
            x_min, y_min, x_max, y_max = box
            detections.append({
                "text": text,
                "bbox": (int(x_min), int(y_min), int(x_max), int(y_max)),
                "confidence": float(score),
            })
    return detections