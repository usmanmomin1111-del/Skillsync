"""
Module 1 & 2 from the PPT: Text Extraction + Formatting Check.
"""
import re
from PyPDF2 import PdfReader

EXPECTED_SECTIONS = ["education", "experience", "skills", "projects", "certifications"]


def extract_text_from_pdf(file_stream) -> str:
    """Extract raw text from an uploaded PDF resume (Module 1: Text Extraction)."""
    if hasattr(file_stream, "seek"):
        file_stream.seek(0)
    reader = PdfReader(file_stream)
    text_parts = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        text_parts.append(extracted)
    return "\n".join(text_parts)


def check_formatting(text: str) -> dict:
    """Rule-based formatting checks (Module 2: Formatting Check)."""
    lower = text.lower()
    found_sections = [s for s in EXPECTED_SECTIONS if s in lower]
    missing_sections = [s for s in EXPECTED_SECTIONS if s not in found_sections]

    word_count = len(text.split())
    bullet_count = len(re.findall(r"(?m)^\s*[•\-\*]\s+", text))
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))
    has_phone = bool(re.search(r"(\+?\d[\d\-\s]{8,}\d)", text))

    issues = []
    if word_count < 150:
        issues.append("Resume content looks quite short — consider adding more detail on projects/experience.")
    if not bullet_count:
        issues.append("No bullet points detected — use bullets to make achievements scannable.")
    if not has_email:
        issues.append("No email address detected — make sure contact info is present.")
    if not has_phone:
        issues.append("No phone number detected.")
    for s in missing_sections:
        issues.append(f"Missing a clearly labeled '{s.title()}' section.")

    return {
        "word_count": word_count,
        "bullet_count": bullet_count,
        "has_email": has_email,
        "has_phone": has_phone,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
        "issues": issues,
    }
