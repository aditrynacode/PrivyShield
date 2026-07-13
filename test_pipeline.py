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

if not regions:
    print("No sensitive regions detected.")
for r in regions:
    print(r["bbox"], [d["type"] for d in r["detections"]])