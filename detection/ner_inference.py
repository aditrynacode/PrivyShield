import onnxruntime as ort
from transformers import AutoTokenizer

MAX_LENGTH = 64

class NERPredictor:
    def __init__(self, onnx_path, tokenizer_path, id2label, confidence_threshold=0.75):
        self.session = ort.InferenceSession(onnx_path)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.id2label = id2label
        self.confidence_threshold = confidence_threshold
 
    def predict(self, text: str):

        encoding = self.tokenizer(
            text,
            return_offsets_mapping=True,
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
            return_tensors="np",
        )
        offsets = encoding.pop("offset_mapping")[0]
 
        onnx_inputs = {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
        }
        logits = self.session.run(None, onnx_inputs)[0][0]
 
        exp = _np_exp(logits)
        probs = exp / exp.sum(axis=-1, keepdims=True)
        pred_ids = probs.argmax(axis=-1)
        confidences = probs.max(axis=-1)
 
        return group_entity_spans(pred_ids, confidences, offsets, text, self.id2label, self.confidence_threshold)

def group_entity_spans(pred_ids, confidences, offsets, text, id2label, confidence_threshold):

    entities = []
    current = None 
 
    for pred_id, conf, (tok_start, tok_end) in zip(pred_ids, confidences, offsets):
        if tok_start == tok_end:
            continue
        label = id2label[int(pred_id)]
 
        if label == "O" or conf < confidence_threshold:
            if current is not None:
                entities.append(_finalize(current, text))
                current = None
            continue
 
        tag, ent_type = label.split("-", 1)
        if tag == "B" or current is None or current["type"] != ent_type:
            if current is not None:
                entities.append(_finalize(current, text))
            current = {"start": tok_start, "end": tok_end, "type": ent_type, "confidences": [conf]}
        else:
            current["end"] = tok_end
            current["confidences"].append(conf)
 
    if current is not None:
        entities.append(_finalize(current, text))
 
    return entities
 
def _finalize(span, text):
    return {
        "start": span["start"],
        "end": span["end"],
        "type": span["type"],
        "text": text[span["start"]:span["end"]],
        "confidence": float(sum(span["confidences"]) / len(span["confidences"])),
    }
 
def _np_exp(x):
    import numpy as np
    x = x - x.max(axis=-1, keepdims=True)
    return np.exp(x)