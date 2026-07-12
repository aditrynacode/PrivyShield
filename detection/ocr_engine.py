from paddleocr import PaddleOCR
from .geometry import box_to_bbox  # re-exported for backwards-compat imports
 
_ocr_engine = None

def get_ocr_engine():

    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr_engine

def run_ocr(image):

    engine = get_ocr_engine()
    result = engine.ocr(image, cls=True)
 
    detections = []
    if result and result[0]:
        for line in result[0]:
            box, (text, confidence) = line
            detections.append({
                "text": text,
                "box": box,
                "confidence": float(confidence),
            })
    return detections