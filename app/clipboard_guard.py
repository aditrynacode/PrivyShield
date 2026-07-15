import threading
import time
import pyperclip
from detection import detect_structured_pii
from detection.regex_pii import remove_overlaps

POLL_INTERVAL_S = 0.75
CONFIDENCE_THRESHOLD = 0.95

def detect_text_pii(text, ner_predictor=None, confidence_threshold=CONFIDENCE_THRESHOLD):

    findings = []

    regex_findings = remove_overlaps(detect_structured_pii(text))
    for f in regex_findings:
        findings.append({"type": f["type"], "text": f["text"], "source": "regex"})

    if ner_predictor is not None:
        ner_findings = ner_predictor.predict(text)
        for f in ner_findings:
            if f["confidence"] >= confidence_threshold:
                findings.append({"type": f["type"], "text": f["text"], "source": "ner"})

    return findings

class ClipboardGuard:

    def __init__(self, ner_predictor=None, on_detection=None, poll_interval=POLL_INTERVAL_S):
        self.ner_predictor = ner_predictor
        self.on_detection = on_detection or self._default_notify
        self.poll_interval = poll_interval

        self._running = False
        self._thread = None
        self._last_seen = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self):

        try:
            self._last_seen = pyperclip.paste()
        except Exception:
            self._last_seen = None

        while self._running:
            try:
                current = pyperclip.paste()
            except Exception:
                current = None

            if current and current != self._last_seen:
                self._last_seen = current
                self._check(current)

            time.sleep(self.poll_interval)

    def _check(self, text):
        findings = detect_text_pii(text, ner_predictor=self.ner_predictor)
        if findings:
            self.on_detection(findings)

    @staticmethod
    def _default_notify(findings):
        types = sorted({f["type"] for f in findings})
        summary = ", ".join(types)

        try:
            from plyer import notification
            notification.notify(
                title="PrivyShield — sensitive clipboard content",
                message=f"Detected: {summary}. Be careful where you paste this.",
                app_name="PrivyShield",
                timeout=5,
            )
        except Exception:

            print(f"[PrivyShield] Sensitive content detected in clipboard: {summary}")

def main():
    import pickle
    from detection import NERPredictor

    with open("data/label_config.pkl", "rb") as f:
        label_config = pickle.load(f)

    ner_predictor = NERPredictor(
        onnx_path="models/ner_model.onnx",
        tokenizer_path="models/ner_model",
        id2label=label_config["id2label"],
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )

    guard = ClipboardGuard(ner_predictor=ner_predictor)
    print("PrivyShield clipboard guard running. Copy something sensitive to test. Ctrl+C to stop.")

    try:
        guard.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping clipboard guard...")
        guard.stop()

if __name__ == "__main__":
    main()