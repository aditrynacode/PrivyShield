import sys
import time

from detection import detect_sensitive_regions, NERPredictor, grab_screen

from PIL import Image, ImageFilter
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QImage, QPixmap, QFont


CAPTURE_INTERVAL_MS = 1200
BLUR_RADIUS = 18
CONFIDENCE_THRESHOLD = 0.95


class DetectionWorker(QThread):
    """
    Runs grab_screen() + detect_sensitive_regions() on a background thread
    so the GUI thread (and therefore click-through + paintEvent) never blocks.
    Emits result_ready(regions, frame) which Qt automatically delivers on the
    main thread via a queued connection, since the receiver lives there.
    """
    result_ready = pyqtSignal(object, object)  # (regions, frame_ndarray)

    def __init__(self, ner_predictor, interval_ms):
        super().__init__()
        self.ner_predictor = ner_predictor
        self.interval_s = interval_ms / 1000.0
        self._running = True

    def run(self):
        while self._running:
            start = time.time()

            frame = grab_screen()
            regions = detect_sensitive_regions(frame, ner_predictor=self.ner_predictor)

            if self._running:
                self.result_ready.emit(regions, frame)

            elapsed = time.time() - start
            sleep_time = max(0.0, self.interval_s - elapsed)
            # sleep in small chunks so stop() feels responsive instead of
            # waiting out a full interval before the thread actually exits
            slept = 0.0
            while self._running and slept < sleep_time:
                chunk = min(0.05, sleep_time - slept)
                time.sleep(chunk)
                slept += chunk

    def stop(self):
        self._running = False
        self.wait()


class PrivyShieldOverlay(QWidget):
    def __init__(self, ner_predictor):
        super().__init__()
        self.flagged_regions = []
        self.last_frame = None
        self.protected_count = 0

        self._setup_window()
        self._setup_status_label()

        self.worker = DetectionWorker(ner_predictor, CAPTURE_INTERVAL_MS)
        self.worker.result_ready.connect(self._on_detection_result)
        self.worker.start()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # keeps it out of the taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # click-through

        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

    def _setup_status_label(self):
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet(
            "background-color: rgba(20, 20, 20, 180); color: white; "
            "padding: 6px 10px; border-radius: 6px; font-size: 12px;"
        )
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.move(20, 20)
        self._update_status_text()
        self.status_label.adjustSize()

    def _update_status_text(self):
        self.status_label.setText(
            f"\U0001F6E1 PrivyShield active — {self.protected_count} item(s) protected"
        )

    def _on_detection_result(self, regions, frame):
        # This slot runs on the MAIN thread even though it was emitted from
        # the worker thread — Qt queues cross-thread signals automatically.
        # This is the ONLY place per cycle where Qt state is touched.
        self.last_frame = Image.fromarray(frame)
        self.flagged_regions = regions
        self.protected_count = max(self.protected_count, len(regions))

        self._update_status_text()
        self.status_label.adjustSize()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if self.last_frame is not None:
            for region in self.flagged_regions:
                x_min, y_min, x_max, y_max = region["bbox"]
                self._draw_blurred_patch(painter, x_min, y_min, x_max, y_max)

    def _draw_blurred_patch(self, painter, x_min, y_min, x_max, y_max):
        pad = 4
        crop_box = (
            max(0, x_min - pad),
            max(0, y_min - pad),
            min(self.last_frame.width, x_max + pad),
            min(self.last_frame.height, y_max + pad),
        )
        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            return  # degenerate box, skip

        patch = self.last_frame.crop(crop_box)
        blurred = patch.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))

        qimage = self._pil_to_qimage(blurred)
        pixmap = QPixmap.fromImage(qimage)
        painter.drawPixmap(crop_box[0], crop_box[1], pixmap)

    @staticmethod
    def _pil_to_qimage(pil_image):
        pil_image = pil_image.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        return qimage.copy()

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


def main():
    import pickle

    with open("data/label_config.pkl", "rb") as f:
        label_config = pickle.load(f)

    ner = NERPredictor(
        onnx_path="models/ner_model.onnx",
        tokenizer_path="models/ner_model",
        id2label=label_config["id2label"],
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )

    app = QApplication(sys.argv)
    overlay = PrivyShieldOverlay(ner_predictor=ner)
    overlay.showFullScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()