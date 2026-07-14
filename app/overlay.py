import sys
import time

from detection import detect_sensitive_regions, NERPredictor, grab_screen

from PIL import Image, ImageFilter
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QImage, QPixmap, QColor, QFont
 

CAPTURE_INTERVAL_MS = 1200 
BLUR_RADIUS = 18
CONFIDENCE_THRESHOLD = 0.95
 
 
class PrivyShieldOverlay(QWidget):
    def __init__(self, ner_predictor):
        super().__init__()
        self.ner_predictor = ner_predictor
        self.flagged_regions = []    
        self.last_frame = None        
        self.protected_count = 0     
 
        self._setup_window()
        self._setup_status_label()
        self._setup_capture_timer()
 
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
            f"🛡 PrivyShield active — {self.protected_count} item(s) protected"
        )
 
    def _setup_capture_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture_and_detect)
        self.timer.start(CAPTURE_INTERVAL_MS)
        self.capture_and_detect() 
 
    def capture_and_detect(self):

        frame = grab_screen()
        self.last_frame = Image.fromarray(frame)
 
        regions = detect_sensitive_regions(frame, ner_predictor=self.ner_predictor)

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

        width = max(1, x_max - x_min)
        height = max(1, y_max - y_min)
 
        pad = 4
        crop_box = (
            max(0, x_min - pad),
            max(0, y_min - pad),
            x_max + pad,
            y_max + pad,
        )
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