# ============================================================
# spacyNER/ocr.py
# Converts scanned form images / PDFs → plain text for NER.
# ============================================================

import os
from PIL import Image, ImageFilter


def preprocess_image(image: Image.Image) -> Image.Image:
    """Grayscale + sharpen for better OCR accuracy."""
    return image.convert("L").filter(ImageFilter.SHARPEN)


def image_to_text(image_path: str) -> str:
    """Read a scanned image and return extracted text."""
    try:
        import pytesseract
    except ImportError:
        print("  ⚠️  Run: pip install pytesseract")
        return ""
    if not os.path.exists(image_path):
        print(f"  ❌ Not found: {image_path}")
        return ""
    img  = preprocess_image(Image.open(image_path))
    text = pytesseract.image_to_string(img, lang="eng")
    print(f"  ✅ OCR done: {image_path}")
    return text


def pdf_to_text(pdf_path: str) -> str:
    """Convert PDF pages to images then extract text."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        print("  ⚠️  Run: pip install pytesseract pdf2image")
        return ""
    if not os.path.exists(pdf_path):
        print(f"  ❌ Not found: {pdf_path}")
        return ""
    pages    = convert_from_path(pdf_path)
    all_text = []
    for i, page in enumerate(pages, 1):
        print(f"     Page {i}/{len(pages)}...")
        all_text.append(pytesseract.image_to_string(
            preprocess_image(page), lang="eng"
        ))
    return "\n\n".join(all_text)


def scan_form(file_path: str) -> str:
    """
    Auto-detect file type and extract text.
    Use this in main.py for real scanned forms.

    Example:
        text = scan_form("scanned/form_102.jpg")
        text = scan_form("scanned/form_103.pdf")
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return pdf_to_text(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
        return image_to_text(file_path)
    else:
        print(f"  ⚠️  Unsupported: {ext}")
        return ""
