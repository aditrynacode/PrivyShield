from .regex_pii import detect_structured_pii, remove_overlaps

def detect_sensitive_regions(image, ner_predictor=None):
 
    """NOTE: run_ocr is imported here (not at module top) so that fuse_detections()
    below stays fully testable without PaddleOCR installed; only this
    function, which actually needs to run OCR, requires that dependency."""

    from .ocr_engine import run_ocr
    ocr_results = run_ocr(image)
    return fuse_detections(ocr_results, ner_predictor)

def fuse_detections(ocr_results, ner_predictor=None):

    flagged_regions = []
 
    for line in ocr_results:
        text = line["text"]
        line_detections = []
 
        regex_findings = remove_overlaps(detect_structured_pii(text))
        for f in regex_findings:
            line_detections.append({"type": f["type"], "text": f["text"], "source": "regex"})
 
        if ner_predictor is not None:
            ner_findings = ner_predictor.predict(text)
            for f in ner_findings:
                line_detections.append({"type": f["type"], "text": f["text"], "source": "ner"})
 
        if line_detections:
            flagged_regions.append({
                "bbox": line["bbox"],
                "text": text,
                "detections": line_detections,
            })
 
    return flagged_regions