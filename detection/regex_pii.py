import re
 
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
CREDIT_CARD_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b")
OTP_CONTEXT_RE = re.compile(r"\b\d{4,6}\b")
OTP_KEYWORDS = re.compile(r"\botp\b|\bverification code\b|\bone.?time.?password\b", re.IGNORECASE)
 
 
def luhn_valid(number_str: str) -> bool:

    digits = [int(d) for d in re.sub(r"[ -]", "", number_str)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0
 
def detect_structured_pii(text: str):

    findings = []
 
    for m in AADHAAR_RE.finditer(text):
        findings.append({"start": m.start(), "end": m.end(), "type": "AADHAAR", "text": m.group()})
 
    for m in PAN_RE.finditer(text):
        findings.append({"start": m.start(), "end": m.end(), "type": "PAN", "text": m.group()})
 
    for m in CREDIT_CARD_RE.finditer(text):
        if luhn_valid(m.group()):
            findings.append({"start": m.start(), "end": m.end(), "type": "CREDIT_CARD", "text": m.group()})
 
    for m in EMAIL_RE.finditer(text):
        findings.append({"start": m.start(), "end": m.end(), "type": "EMAIL", "text": m.group()})
 
    for m in PHONE_RE.finditer(text):
        findings.append({"start": m.start(), "end": m.end(), "type": "PHONE", "text": m.group()})
 
    if OTP_KEYWORDS.search(text):
        for m in OTP_CONTEXT_RE.finditer(text):
            
            overlaps_existing = any(
                m.start() < f["end"] and m.end() > f["start"] for f in findings
            )
            if not overlaps_existing:
                findings.append({"start": m.start(), "end": m.end(), "type": "OTP", "text": m.group()})
 
    return findings
 
def remove_overlaps(findings):

    findings = sorted(findings, key=lambda f: (f["start"], -(f["end"] - f["start"])))
    kept = []
    last_end = -1
    for f in findings:
        if f["start"] >= last_end:
            kept.append(f)
            last_end = f["end"]
    return kept