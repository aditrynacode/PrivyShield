import base64
import io
import os
import subprocess
import sys
 
from flask import Flask, request, render_template_string, redirect, url_for
from PIL import Image
 
from app.redact import load_ner_predictor, redact_image
 
app = Flask(__name__)
 
_ner_predictor = None
_overlay_process = None  
_clipboard_process = None  
 
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
 
def get_predictor():
    global _ner_predictor
    if _ner_predictor is None:
        _ner_predictor = load_ner_predictor()
    return _ner_predictor
 
 
def _overlay_is_running():
    global _overlay_process
    if _overlay_process is None:
        return False
    if _overlay_process.poll() is not None:
        _overlay_process = None
        return False
    return True
 
 
def _start_overlay():
    global _overlay_process
    if _overlay_is_running():
        return
    _overlay_process = subprocess.Popen(
        [sys.executable, "-m", "app.overlay"],
        cwd=PROJECT_ROOT,
    )
 
 
def _stop_overlay():
    global _overlay_process
    if not _overlay_is_running():
        return
    _overlay_process.terminate()
    try:
        _overlay_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _overlay_process.kill()
    _overlay_process = None
 
 
def _clipboard_is_running():
    global _clipboard_process
    if _clipboard_process is None:
        return False
    if _clipboard_process.poll() is not None:
        _clipboard_process = None
        return False
    return True
 
 
def _start_clipboard():
    global _clipboard_process
    if _clipboard_is_running():
        return
    _clipboard_process = subprocess.Popen(
        [sys.executable, "-m", "app.clipboard_guard"],
        cwd=PROJECT_ROOT,
    )
 
 
def _stop_clipboard():
    global _clipboard_process
    if not _clipboard_is_running():
        return
    _clipboard_process.terminate()
    try:
        _clipboard_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _clipboard_process.kill()
    _clipboard_process = None
 
 
PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PrivyShield</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,700..900&family=PT+Serif:wght@400;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0c1519;          /* Chinese Black */
    --surface: #162127;      /* Dark Jungle Green */
    --surface-alt: #3a3534;  /* Jet */
    --border: #2d2622;
    --text: #ece4da;
    --muted: #a89a8c;
    --safe: #cf9d7b;         /* Antique Brass, main accent */
    --flag: #c08a5c;         /* Coffee, lightened for legibility on dark */
    --sensitive: #b3563a;    /* terracotta, kept in the same warm family */
  }
 
  * { box-sizing: border-box; }
 
  body {
    background: var(--bg);
    color: var(--text);
    font-family: "PT Serif", serif;
    margin: 0;
    line-height: 1.75;
    letter-spacing: 0.01em;
  }
 
  .wrap { max-width: 880px; margin: 0 auto; padding: 64px 24px 84px; }
 
  .eyebrow {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.75rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--safe);
    margin-bottom: 12px;
  }
 
  h1 {
    font-family: "Bodoni Moda", serif;
    font-weight: 900;
    font-size: 3.1rem;
    letter-spacing: 0.005em;
    margin: 0 0 18px;
  }
 
  h2 {
    font-family: "Bodoni Moda", serif;
    font-weight: 800;
    font-size: 1.35rem;
    letter-spacing: 0.005em;
    margin: 0 0 20px;
  }
 
  .tagline { color: var(--muted); font-size: 1.08rem; max-width: 60ch; margin: 0 0 32px; letter-spacing: 0.015em; }
 
  .tag {
    display: inline-block;
    font-family: "JetBrains Mono", monospace;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid var(--border);
    color: var(--muted);
    margin: 0 8px 8px 0;
  }
 
  .tag-row { margin-bottom: 44px; }
 
  section { margin-bottom: 58px; }
 
  section > p { color: var(--muted); max-width: 68ch; }
 
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 22px;
  }
 
  .flow {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    font-family: "JetBrains Mono", monospace;
    font-size: 0.82rem;
    color: var(--muted);
  }
 
  .flow .step {
    background: var(--surface-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    color: var(--text);
  }
 
  .flow .arrow { color: var(--border); }
 
  .layers { display: flex; flex-direction: column; gap: 10px; }
 
  .layer-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
  }
 
  .layer-row .name { font-weight: 500; }
  .layer-row .desc { color: var(--muted); font-size: 0.9rem; margin-top: 2px; }
 
  .status {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    padding: 4px 10px;
    border-radius: 100px;
    white-space: nowrap;
    flex-shrink: 0;
  }
 
  .status.done { color: var(--safe); border: 1px solid var(--safe); }
  .status.roadmap { color: var(--flag); border: 1px solid var(--flag); }
 
  .divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 56px 0 48px;
  }
 
  .overlay-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }
 
  .overlay-card + .overlay-card { margin-top: 14px; }
 
  .overlay-card .status-line { font-size: 0.9rem; margin-top: 4px; }
  .overlay-card .status-line.on { color: var(--safe); }
  .overlay-card .status-line.off { color: var(--muted); }
 
  button {
    font-family: "PT Serif", serif;
    font-weight: 700;
    font-size: 0.92rem;
    background: var(--safe);
    color: #23140c;
    border: none;
    padding: 10px 18px;
    border-radius: 7px;
    cursor: pointer;
  }
 
  button:hover { opacity: 0.9; }
  button.stop { background: var(--sensitive); color: #fbe9e2; }
 
  form.upload-form {
    border: 1px dashed var(--border);
    border-radius: 10px;
    padding: 26px;
    text-align: center;
    margin-top: 18px;
  }
 
  input[type=file] { color: var(--muted); font-size: 0.9rem; }
  form.upload-form button { margin-top: 14px; }
 
  .error {
    background: #241211;
    border: 1px solid #4a2422;
    color: #f0b2af;
    padding: 10px 14px;
    border-radius: 8px;
    margin-top: 16px;
  }
 
  .count {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.82rem;
    color: var(--safe);
    margin: 20px 0 12px;
  }
 
  .results { display: flex; gap: 18px; flex-wrap: wrap; }
  .results .col { flex: 1; min-width: 260px; }
  .results .col h3 { font-size: 0.8rem; color: var(--muted); font-weight: 500; margin-bottom: 8px; }
  .results .col img { width: 100%; border-radius: 8px; border: 1px solid var(--border); display: block; }
 
  footer { color: var(--muted); font-size: 0.82rem; margin-top: 60px; }
  footer a { color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
 
  <div class="eyebrow">OSDHack 2026 &middot; On-Device AI</div>
  <h1>PrivyShield</h1>
  <p class="tagline">
    Watches your screen locally and blurs sensitive information the moment it appears:
    Aadhaar numbers, PAN cards, credit cards, emails, phone numbers, OTPs, names, and addresses.
    Nothing leaves the machine.
  </p>
  <div class="tag-row">
    <span class="tag">AADHAAR</span>
    <span class="tag">PAN</span>
    <span class="tag">CREDIT_CARD</span>
    <span class="tag">EMAIL</span>
    <span class="tag">PHONE</span>
    <span class="tag">OTP</span>
    <span class="tag">PERSON_NAME</span>
    <span class="tag">ADDRESS</span>
  </div>
 
  <section>
    <h2>The problem</h2>
    <p>
      Sensitive information leaks off screens more often than people notice: a banking tab open
      during a screen share, a support screenshot that still shows a card number. Most tools that
      could catch this need to send screen content to a server, which is a poor tradeoff when the
      content is an Aadhaar number.
    </p>
  </section>
 
  <section>
    <h2>How it works</h2>
    <div class="card">
      <div class="flow">
        <div class="step">screen capture</div>
        <div class="arrow">&rsaquo;</div>
        <div class="step">OCR (PaddleOCR)</div>
        <div class="arrow">&rsaquo;</div>
        <div class="step">regex PII</div>
        <div class="arrow">+</div>
        <div class="step">NER model</div>
        <div class="arrow">&rsaquo;</div>
        <div class="step">fuse detections</div>
        <div class="arrow">&rsaquo;</div>
        <div class="step">blur / redact</div>
      </div>
    </div>
    <p style="margin-top:16px;">
      Structured PII (card numbers, emails, phone numbers) has a fixed shape, so plain pattern
      matching handles it, with the Luhn checksum cutting down false positives on card numbers.
      Names and addresses don't have a fixed shape, so those are caught by a DistilBERT model
      fine-tuned on 7,500 synthetic sentences and exported to ONNX for fast local inference.
    </p>
  </section>
 
  <section>
    <h2>Layers of protection</h2>
    <div class="layers">
      <div class="layer-row">
        <div>
          <div class="name">Screen Shield</div>
          <div class="desc">Live capture, OCR, PII detection, and a live blur overlay.</div>
        </div>
        <div class="status done">done</div>
      </div>
      <div class="layer-row">
        <div>
          <div class="name">Redaction Export</div>
          <div class="desc">Drop in a screenshot or PDF, get back a copy with PII blacked out.</div>
        </div>
        <div class="status done">done</div>
      </div>
      <div class="layer-row">
        <div>
          <div class="name">Clipboard Guard</div>
          <div class="desc">Warns you locally before you paste something sensitive you just copied.</div>
        </div>
        <div class="status done">done</div>
      </div>
      <div class="layer-row">
        <div>
          <div class="name">Screen-Share Mode</div>
          <div class="desc">Heavier blurring tuned specifically for video calls.</div>
        </div>
        <div class="status roadmap">roadmap</div>
      </div>
      <div class="layer-row">
        <div>
          <div class="name">Risk Dashboard</div>
          <div class="desc">Local-only log of what kinds of PII get flagged over time. No content stored.</div>
        </div>
        <div class="status roadmap">roadmap</div>
      </div>
    </div>
  </section>
 
  <section>
    <h2>Tech stack</h2>
    <div class="tag-row">
      <span class="tag">mss</span>
      <span class="tag">PaddleOCR</span>
      <span class="tag">Python re + Luhn</span>
      <span class="tag">DistilBERT &rarr; ONNX</span>
      <span class="tag">onnxruntime</span>
      <span class="tag">Pillow</span>
      <span class="tag">PyQt5</span>
      <span class="tag">pyperclip</span>
      <span class="tag">PyMuPDF</span>
    </div>
  </section>
 
  <hr class="divider">
 
  <div class="eyebrow">Try it</div>
  <h2 style="font-size:1.3rem; margin-bottom:22px;">Run the pipeline yourself</h2>
 
  <div class="card overlay-card">
    <div>
      <div class="name">Live screen overlay</div>
      <div class="status-line {{ 'on' if overlay_running else 'off' }}">
        {{ 'Running. Blurring your screen live.' if overlay_running else 'Not running.' }}
      </div>
    </div>
    <form method="post" action="{{ url_for('toggle_overlay') }}">
      <button type="submit" class="{{ 'stop' if overlay_running else '' }}">
        {{ 'Stop overlay' if overlay_running else 'Start overlay' }}
      </button>
    </form>
  </div>
 
  <div class="card overlay-card">
    <div>
      <div class="name">Clipboard Guard</div>
      <div class="status-line {{ 'on' if clipboard_running else 'off' }}">
        {{ 'Running. Watching your clipboard.' if clipboard_running else 'Not running.' }}
      </div>
    </div>
    <form method="post" action="{{ url_for('toggle_clipboard') }}">
      <button type="submit" class="{{ 'stop' if clipboard_running else '' }}">
        {{ 'Stop clipboard guard' if clipboard_running else 'Start clipboard guard' }}
      </button>
    </form>
  </div>
 
  <form class="upload-form" method="post" enctype="multipart/form-data">
    <div style="color: var(--muted); font-size: 0.9rem; margin-bottom: 4px;">
      Upload a screenshot or image to test detection and redaction directly.
    </div>
    <input type="file" name="image" accept="image/*" required>
    <br>
    <button type="submit">Detect and redact</button>
  </form>
 
  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}
 
  {% if result %}
    <div class="count">{{ count }} sensitive region(s) redacted</div>
    <div class="results">
      <div class="col"><h3>Original</h3><img src="data:image/png;base64,{{ original_b64 }}"></div>
      <div class="col"><h3>Redacted</h3><img src="data:image/png;base64,{{ redacted_b64 }}"></div>
    </div>
  {% endif %}
 
  <footer>
    Apache-2.0. Built by Aditya for OSDHack 2026, organized by the Open Source Developers Community.
  </footer>
 
</div>
</body>
</html>
"""
 
 
def _to_b64_png(pil_image):
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
 
 
@app.route("/", methods=["GET", "POST"])
def index():
    overlay_running = _overlay_is_running()
    clipboard_running = _clipboard_is_running()
 
    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            return render_template_string(
                PAGE,
                result=False,
                error="Choose an image first.",
                overlay_running=overlay_running,
                clipboard_running=clipboard_running,
            )
 
        try:
            original = Image.open(file.stream).convert("RGB")
        except Exception:
            return render_template_string(
                PAGE,
                result=False,
                error="Couldn't read that file as an image.",
                overlay_running=overlay_running,
                clipboard_running=clipboard_running,
            )
 
        redacted, count = redact_image(original, get_predictor())
 
        return render_template_string(
            PAGE,
            result=True,
            error=None,
            count=count,
            original_b64=_to_b64_png(original),
            redacted_b64=_to_b64_png(redacted),
            overlay_running=overlay_running,
            clipboard_running=clipboard_running,
        )
 
    return render_template_string(
        PAGE,
        result=False,
        error=None,
        overlay_running=overlay_running,
        clipboard_running=clipboard_running,
    )
 
 
@app.route("/toggle_overlay", methods=["POST"])
def toggle_overlay():
    if _overlay_is_running():
        _stop_overlay()
    else:
        _start_overlay()
    return redirect(url_for("index"))
 
 
@app.route("/toggle_clipboard", methods=["POST"])
def toggle_clipboard():
    if _clipboard_is_running():
        _stop_clipboard()
    else:
        _start_clipboard()
    return redirect(url_for("index"))
 
 
if __name__ == "__main__":
    print("Loading NER model...")
    get_predictor()
    print("Ready. Open http://127.0.0.1:5000")
    app.run(debug=False, port=5000)