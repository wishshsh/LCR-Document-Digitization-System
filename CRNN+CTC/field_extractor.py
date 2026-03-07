"""
Philippine Civil Registry Field Extractor
==========================================
Extracts fields from Forms 97, 102, 103 using relative coordinate ratios.
Uses the trained CRNN+CTC model for OCR (not Tesseract).

Usage:
    python field_extractor.py --pdf FORM_102.pdf --form birth
    python field_extractor.py --pdf FORM_97.pdf  --form marriage --visualize
    python field_extractor.py --pdf FORM_103.pdf --form death    --output results.json
    python field_extractor.py --pdf FORM_102.pdf --form birth    --checkpoint checkpoints/best_model.pth
"""

import argparse
import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

import torch

# ─────────────────────────────────────────────
#  POPPLER PATH — adjust if needed
#  Set to None if poppler is in your system PATH
# ─────────────────────────────────────────────
POPPLER_PATH = r"C:\Users\irish\OneDrive\Desktop\poppler-25.12.0\Library\bin"

# ─────────────────────────────────────────────
#  DEFAULT CHECKPOINT
# ─────────────────────────────────────────────
DEFAULT_CHECKPOINT = "checkpoints/best_model.pth"


# ══════════════════════════════════════════════════════════════
#  FIELD COORDINATE MAPS
#  Format: field_name: (x1, y1, x2, y2)  — all values 0.0–1.0
#  Calibrated against actual PDFs at 200 DPI:
#    Form 102 (Birth):    1700 × 2800 px
#    Form 103 (Death):    1700 × 2878 px
#    Form 97  (Marriage): 1700 × 2600 px
# ══════════════════════════════════════════════════════════════

BIRTH_FIELDS = {
    # ── Header ────────────────────────────────────────────────
    "province":               (0.08,  0.060, 0.48,  0.082),
    "registry_no":            (0.62,  0.060, 0.95,  0.082),
    "city_municipality":      (0.18,  0.082, 0.48,  0.102),

    # ── Item 1: Child Name ─────────────────────────────────────
    "child_first_name":       (0.14,  0.108, 0.42,  0.132),
    "child_middle_name":      (0.42,  0.108, 0.65,  0.132),
    "child_last_name":        (0.65,  0.108, 0.95,  0.132),

    # ── Items 2-3: Sex / Date of Birth ─────────────────────────
    "sex":                    (0.15,  0.138, 0.30,  0.162),
    "dob_day":                (0.42,  0.138, 0.52,  0.162),
    "dob_month":              (0.52,  0.138, 0.72,  0.162),
    "dob_year":               (0.72,  0.138, 0.95,  0.162),

    # ── Item 4: Place of Birth ─────────────────────────────────
    "place_birth_hospital":   (0.22,  0.165, 0.50,  0.190),
    "place_birth_city":       (0.50,  0.165, 0.68,  0.190),
    "place_birth_province":   (0.68,  0.165, 0.88,  0.190),

    # ── Items 5a / 6: Type of Birth / Weight ──────────────────
    "type_of_birth":          (0.15,  0.192, 0.32,  0.215),
    "weight_at_birth":        (0.74,  0.200, 0.95,  0.220),

    # ── MOTHER section ─────────────────────────────────────────
    # Item 7: Maiden Name (First / Middle / Last)
    "mother_first_name":      (0.14,  0.278, 0.40,  0.300),
    "mother_middle_name":     (0.40,  0.278, 0.63,  0.300),
    "mother_last_name":       (0.63,  0.278, 0.95,  0.300),

    # Item 8: Citizenship   Item 9: Religion
    "mother_citizenship":     (0.15,  0.302, 0.38,  0.325),
    "mother_religion":        (0.48,  0.302, 0.95,  0.325),

    # Item 11: Occupation   Item 12: Age at birth
    "mother_occupation":      (0.42,  0.348, 0.70,  0.370),
    "mother_age_at_birth":    (0.83,  0.348, 0.95,  0.370),

    # Item 13: Residence (House / City / Province)
    "mother_residence_house":    (0.22, 0.375, 0.44, 0.398),
    "mother_residence_city":     (0.44, 0.375, 0.64, 0.398),
    "mother_residence_province": (0.64, 0.375, 0.80, 0.398),

    # ── FATHER section ─────────────────────────────────────────
    # Item 14: Name (First / Middle / Last)
    "father_first_name":      (0.14,  0.468, 0.40,  0.492),
    "father_middle_name":     (0.40,  0.468, 0.63,  0.492),
    "father_last_name":       (0.63,  0.468, 0.95,  0.492),

    # Item 15: Citizenship   Item 16: Religion
    "father_citizenship":     (0.15,  0.495, 0.33,  0.518),
    "father_religion":        (0.33,  0.495, 0.58,  0.518),

    # Item 17: Occupation   Item 18: Age
    "father_occupation":      (0.42,  0.520, 0.70,  0.542),
    "father_age_at_birth":    (0.83,  0.520, 0.95,  0.542),

    # Item 19: Residence (House / City / Province)
    "father_residence_house":    (0.22, 0.545, 0.44, 0.568),
    "father_residence_city":     (0.44, 0.545, 0.64, 0.568),
    "father_residence_province": (0.64, 0.545, 0.80, 0.568),

    # ── Item 20: Marriage of Parents ───────────────────────────
    "parents_marriage_month":    (0.14, 0.608, 0.26, 0.628),
    "parents_marriage_day":      (0.26, 0.608, 0.36, 0.628),
    "parents_marriage_year":     (0.36, 0.608, 0.46, 0.628),
    "parents_marriage_city":     (0.52, 0.608, 0.68, 0.628),
    "parents_marriage_province": (0.68, 0.608, 0.82, 0.628),

    # ── Item 22: Informant ─────────────────────────────────────
    "informant_name":         (0.04,  0.748, 0.42,  0.768),
    "informant_date":         (0.04,  0.790, 0.22,  0.808),
}


DEATH_FIELDS = {
    # ── Header ────────────────────────────────────────────────
    "province":               (0.10,  0.127, 0.48,  0.150),
    "registry_no":            (0.58,  0.116, 0.78,  0.145),
    "city_municipality":      (0.18,  0.150, 0.50,  0.172),

    # ── Item 1: Name (First / Middle / Last) ──────────────────
    "deceased_first_name":    (0.12,  0.172, 0.36,  0.200),
    "deceased_middle_name":   (0.36,  0.172, 0.58,  0.200),
    "deceased_last_name":     (0.58,  0.172, 0.78,  0.200),

    # ── Items 2-4: Sex / Religion / Age ───────────────────────
    "sex":                    (0.08,  0.202, 0.18,  0.228),
    "religion":               (0.22,  0.202, 0.42,  0.228),
    "age_years":              (0.43,  0.202, 0.52,  0.228),

    # ── Item 5: Place of Death ────────────────────────────────
    "place_death_hospital":   (0.22,  0.228, 0.48,  0.255),
    "place_death_city":       (0.48,  0.228, 0.63,  0.255),
    "place_death_province":   (0.63,  0.228, 0.78,  0.255),

    # ── Item 6: Date of Death   Item 7: Citizenship ───────────
    "dod_day":                (0.20,  0.258, 0.30,  0.282),
    "dod_month":              (0.30,  0.258, 0.46,  0.282),
    "dod_year":               (0.46,  0.258, 0.60,  0.282),
    "citizenship":            (0.62,  0.258, 0.78,  0.282),

    # ── Item 8: Residence ─────────────────────────────────────
    "residence_house":        (0.22,  0.285, 0.46,  0.308),
    "residence_city":         (0.46,  0.285, 0.63,  0.308),
    "residence_province":     (0.63,  0.285, 0.78,  0.308),

    # ── Items 9-10: Civil Status / Occupation ─────────────────
    "civil_status":           (0.04,  0.315, 0.32,  0.348),
    "occupation":             (0.50,  0.315, 0.78,  0.348),

    # ── Item 17: Causes of Death ──────────────────────────────
    # Boxes sit on the actual fill underlines below each label (a, b, c, II)
    "cause_immediate":        (0.25,  0.411, 0.63,  0.420),
    "cause_antecedent":       (0.25,  0.431, 0.63,  0.441),
    "cause_underlying":       (0.25,  0.451, 0.63,  0.460),
    "cause_other":            (0.25,  0.471, 0.63,  0.481),

    # ── Item 25: Informant ────────────────────────────────────
    # Left col:  Signature / Name in Print / Relationship
    # Right col: Address   / (2nd line)    / Date
    "informant_name":         (0.04,  0.823, 0.38,  0.829),
    "informant_address":      (0.42,  0.817, 0.78,  0.823),
    "informant_date":         (0.42,  0.830, 0.62,  0.836),
}


MARRIAGE_FIELDS = {
    # ── Header ────────────────────────────────────────────────
    "province":               (0.08,  0.076, 0.44,  0.098),
    "registry_no":            (0.62,  0.076, 0.96,  0.098),
    "city_municipality":      (0.18,  0.098, 0.46,  0.118),

    # ── Item 1: Names of Contracting Parties ──────────────────
    # First names (HUSBAND left half / WIFE right half)
    "husband_first_name":     (0.14,  0.152, 0.42,  0.175),
    "wife_first_name":        (0.55,  0.152, 0.82,  0.175),
    # Middle names
    "husband_middle_name":    (0.14,  0.175, 0.42,  0.198),
    "wife_middle_name":       (0.55,  0.175, 0.82,  0.198),
    # Last names
    "husband_last_name":      (0.14,  0.198, 0.42,  0.220),
    "wife_last_name":         (0.55,  0.198, 0.82,  0.220),

    # ── Item 2a: Date of Birth / Age ──────────────────────────
    "husband_dob_day":        (0.14,  0.222, 0.22,  0.243),
    "husband_dob_month":      (0.22,  0.222, 0.32,  0.243),
    "husband_dob_year":       (0.32,  0.222, 0.40,  0.243),
    "husband_age":            (0.40,  0.222, 0.48,  0.243),
    "wife_dob_day":           (0.55,  0.222, 0.62,  0.243),
    "wife_dob_month":         (0.62,  0.222, 0.72,  0.243),
    "wife_dob_year":          (0.72,  0.222, 0.80,  0.243),
    "wife_age":               (0.80,  0.222, 0.88,  0.243),

    # ── Item 3: Place of Birth ────────────────────────────────
    "husband_place_birth_city":     (0.14, 0.245, 0.28, 0.265),
    "husband_place_birth_province": (0.28, 0.245, 0.40, 0.265),
    "wife_place_birth_city":        (0.55, 0.245, 0.68, 0.265),
    "wife_place_birth_province":    (0.68, 0.245, 0.80, 0.265),

    # ── Items 4a-b: Sex / Citizenship ─────────────────────────
    "husband_sex":            (0.14,  0.268, 0.24,  0.288),
    "husband_citizenship":    (0.24,  0.268, 0.46,  0.288),
    "wife_sex":               (0.55,  0.268, 0.64,  0.288),
    "wife_citizenship":       (0.64,  0.268, 0.82,  0.288),

    # ── Item 5: Residence ─────────────────────────────────────
    "husband_residence":      (0.14,  0.290, 0.46,  0.328),
    "wife_residence":         (0.55,  0.290, 0.96,  0.328),

    # ── Item 6: Religion ──────────────────────────────────────
    "husband_religion":       (0.14,  0.330, 0.46,  0.352),
    "wife_religion":          (0.55,  0.330, 0.96,  0.352),

    # ── Item 7: Civil Status ──────────────────────────────────
    "husband_civil_status":   (0.14,  0.353, 0.46,  0.373),
    "wife_civil_status":      (0.55,  0.353, 0.82,  0.373),

    # ── Item 8: Father Name ───────────────────────────────────
    "husband_father_first":   (0.14,  0.395, 0.26,  0.415),
    "husband_father_middle":  (0.26,  0.395, 0.37,  0.415),
    "husband_father_last":    (0.37,  0.395, 0.46,  0.415),
    "wife_father_first":      (0.55,  0.395, 0.66,  0.415),
    "wife_father_middle":     (0.66,  0.395, 0.76,  0.415),
    "wife_father_last":       (0.76,  0.395, 0.88,  0.415),

    # ── Item 10: Mother Name ──────────────────────────────────
    "husband_mother_first":   (0.14,  0.440, 0.26,  0.460),
    "husband_mother_middle":  (0.26,  0.440, 0.37,  0.460),
    "husband_mother_last":    (0.37,  0.440, 0.46,  0.460),
    "wife_mother_first":      (0.55,  0.440, 0.66,  0.460),
    "wife_mother_middle":     (0.66,  0.440, 0.76,  0.460),
    "wife_mother_last":       (0.76,  0.440, 0.88,  0.460),

    # ── Item 15: Place of Marriage ────────────────────────────
    "place_marriage_office":  (0.14,  0.620, 0.44,  0.642),
    "place_marriage_city":    (0.44,  0.620, 0.68,  0.642),
    "place_marriage_province":(0.68,  0.620, 0.88,  0.642),

    # ── Item 16: Date of Marriage ─────────────────────────────
    "date_marriage_day":      (0.14,  0.643, 0.24,  0.662),
    "date_marriage_month":    (0.24,  0.643, 0.38,  0.662),
    "date_marriage_year":     (0.38,  0.643, 0.48,  0.662),
}


# ─────────────────────────────────────────────
#  COLOUR PALETTE — for visualization
# ─────────────────────────────────────────────
COLOURS = [
    (255, 100, 100, 80), (100, 200, 100, 80), (100, 100, 255, 80),
    (255, 200,   0, 80), (200,   0, 200, 80), (  0, 200, 200, 80),
    (255, 140,   0, 80), (150,  50, 200, 80), (  0, 160,  80, 80),
    (220,  20,  60, 80), ( 30, 144, 255, 80), (255,  20, 147, 80),
]


# ══════════════════════════════════════════════════════════════
#  CRNN IMAGE NORMALIZER
# ══════════════════════════════════════════════════════════════

class FieldNormalizer:
    """
    Normalizes a cropped field image for CRNN inference.
    Handles small field crops from scanned PDFs.
    """
    def __init__(self, target_height=64, target_width=512):
        self.H = target_height
        self.W = target_width

    def _crop_to_text(self, gray):
        inv = cv2.bitwise_not(gray)
        _, thresh = cv2.threshold(inv, 20, 255, cv2.THRESH_BINARY)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) == 0:
            return gray
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        pad   = max(4, int((y_max - y_min) * 0.15))
        y_min = max(0, y_min - pad)
        x_min = max(0, x_min - pad)
        y_max = min(gray.shape[0] - 1, y_max + pad)
        x_max = min(gray.shape[1] - 1, x_max + pad)
        return gray[y_min:y_max+1, x_min:x_max+1]

    def _smart_resize(self, gray):
        h, w = gray.shape
        if h == 0 or w == 0:
            return np.ones((self.H, self.W), dtype=np.uint8) * 255
        scale = self.H / h
        new_w = int(w * scale)
        new_h = self.H
        if new_w > self.W:
            scale = self.W / w
            new_h = int(h * scale)
            new_w = self.W
        resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        canvas  = np.ones((self.H, self.W), dtype=np.uint8) * 255
        y_off   = (self.H - new_h) // 2
        x_off   = (self.W - new_w) // 2
        canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
        return canvas

    def _binarize(self, img):
        _, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        white_ratio = np.mean(otsu == 255)
        if white_ratio < 0.30 or white_ratio > 0.97:
            return cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2)
        return otsu

    def normalize(self, pil_image) -> np.ndarray:
        """Accept a PIL image crop, return normalized numpy array."""
        img  = np.array(pil_image.convert("RGB"))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        gray = self._crop_to_text(gray)
        gray = self._smart_resize(gray)
        return self._binarize(gray)

    def to_tensor(self, img: np.ndarray) -> torch.Tensor:
        return torch.FloatTensor(
            img.astype(np.float32) / 255.0
        ).unsqueeze(0).unsqueeze(0)


# ══════════════════════════════════════════════════════════════
#  CRNN MODEL LOADER
# ══════════════════════════════════════════════════════════════

def load_crnn_model(checkpoint_path: str, device: torch.device):
    """Load CRNN model and character maps from checkpoint."""
    sys.path.insert(0, str(Path(__file__).parent))
    from crnn_model import get_crnn_model

    print(f"  Loading CRNN model from: {checkpoint_path}")
    c = torch.load(checkpoint_path, map_location=device, weights_only=False)

    config      = c.get("config", {})
    img_h       = config.get("img_height", 64)
    img_w       = config.get("img_width",  512)
    idx_to_char = c["idx_to_char"]

    # Use actual weight shape — more reliable than saved char count
    num_chars = c["model_state_dict"]["fc.weight"].shape[0]

    model = get_crnn_model(
        model_type=config.get("model_type", "standard"),
        img_height=img_h,
        num_chars=num_chars,
        hidden_size=config.get("hidden_size", 128),       # FIXED: was 256 — must match trained model
        num_lstm_layers=config.get("num_lstm_layers", 1), # FIXED: was 2 — must match trained model
    ).to(device)
    model.load_state_dict(c["model_state_dict"])
    model.eval()

    val_cer = c.get("val_cer", None)
    cer_str = f"{val_cer:.2f}%" if val_cer is not None else "N/A"
    print(f"  Model loaded  |  val_cer={cer_str}  |  chars={num_chars}")
    return model, idx_to_char, img_h, img_w


# ══════════════════════════════════════════════════════════════
#  GREEDY CTC DECODE
# ══════════════════════════════════════════════════════════════

def greedy_decode(outputs: torch.Tensor, idx_to_char: dict) -> str:
    pred_indices = torch.argmax(outputs, dim=2).permute(1, 0)
    chars, prev = [], -1
    for idx in pred_indices[0]:
        idx = idx.item()
        if idx != 0 and idx != prev and idx in idx_to_char:
            chars.append(idx_to_char[idx])
        prev = idx
    return "".join(chars)


# ══════════════════════════════════════════════════════════════
#  CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════

def pdf_to_image(pdf_path: str, dpi: int = 200):
    """Convert first page of PDF to PIL Image."""
    from pdf2image import convert_from_path
    kwargs = {"dpi": dpi, "first_page": 1, "last_page": 1}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    pages = convert_from_path(pdf_path, **kwargs)
    return pages[0]


def extract_field_images(image, fields: dict) -> dict:
    """Crop each field region from the full-page PIL image."""
    w, h = image.size
    crops = {}
    for name, (x1, y1, x2, y2) in fields.items():
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        if px2 > px1 and py2 > py1:
            crops[name] = image.crop((px1, py1, px2, py2))
    return crops


def run_crnn_ocr(crops: dict, model, idx_to_char: dict,
                 img_h: int, img_w: int, device: torch.device) -> dict:
    """
    Run CRNN inference on each field crop.
    Returns dict of field_name → recognized text.
    """
    normalizer = FieldNormalizer(target_height=img_h, target_width=img_w)
    results    = {}

    with torch.no_grad():
        for name, pil_crop in crops.items():
            try:
                norm   = normalizer.normalize(pil_crop)
                tensor = normalizer.to_tensor(norm).to(device)
                output = model(tensor)
                text   = greedy_decode(output.cpu(), idx_to_char)
                results[name] = text
            except Exception as e:
                results[name] = f"[ERROR: {e}]"

    return results


def draw_fields(image, fields: dict, label_font_size: int = 12):
    """Draw semi-transparent boxes + labels for every field."""
    from PIL import Image as PILImage, ImageDraw, ImageFont
    overlay = PILImage.new("RGBA", image.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    w, h    = image.size

    try:
        font = ImageFont.truetype("arial.ttf", label_font_size)
    except Exception:
        font = ImageFont.load_default()

    for idx, (name, (x1, y1, x2, y2)) in enumerate(fields.items()):
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        colour   = COLOURS[idx % len(COLOURS)]
        draw.rectangle([px1, py1, px2, py2],
                       fill=colour, outline=colour[:3] + (200,), width=2)
        draw.text((px1 + 2, py1 + 1), name, fill=(0, 0, 0, 230), font=font)

    return PILImage.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PH Civil Registry Field Extractor — CRNN OCR")
    parser.add_argument("--pdf",        required=True,
                        help="Path to the scanned PDF")
    parser.add_argument("--form",       required=True,
                        choices=["birth", "death", "marriage"],
                        help="Form type")
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT,
                        help=f"CRNN checkpoint path (default: {DEFAULT_CHECKPOINT})")
    parser.add_argument("--visualize",  action="store_true",
                        help="Save annotated field-map image")
    parser.add_argument("--output",     default=None,
                        help="Save extracted fields to this JSON file")
    parser.add_argument("--poppler",    default=None,
                        help="Override Poppler bin path")
    parser.add_argument("--dpi",        type=int, default=200,
                        help="PDF render DPI (default: 200)")
    args = parser.parse_args()

    global POPPLER_PATH
    if args.poppler:
        POPPLER_PATH = args.poppler

    form_map = {
        "birth":    ("Form 102 — Certificate of Live Birth", BIRTH_FIELDS),
        "death":    ("Form 103 — Certificate of Death",      DEATH_FIELDS),
        "marriage": ("Form 97 — Certificate of Marriage",    MARRIAGE_FIELDS),
    }
    form_label, fields = form_map[args.form]

    print("\nPhilippine Civil Registry OCR — CRNN Field Extractor")
    print("=" * 65)
    print(f"  Form       : {form_label}")
    print(f"  File       : {args.pdf}")
    print(f"  Checkpoint : {args.checkpoint}")
    print(f"  DPI        : {args.dpi}")

    # ── 1. Load CRNN model ────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device     : {device}\n")

    if not os.path.exists(args.checkpoint):
        print(f"ERROR: Checkpoint not found: {args.checkpoint}")
        print("Make sure training is complete and best_model.pth exists.")
        sys.exit(1)

    model, idx_to_char, img_h, img_w = load_crnn_model(args.checkpoint, device)

    # ── 2. Convert PDF → image ────────────────────────────────
    print(f"\n  Converting PDF to image at {args.dpi} DPI...")
    try:
        page_image = pdf_to_image(args.pdf, dpi=args.dpi)
    except Exception as e:
        print(f"\nERROR converting PDF: {e}")
        print("""
If you see 'Unable to get page count' or 'pdftoppm not found':
  1. Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases
  2. Extract and set POPPLER_PATH at the top of this script.
     Example: POPPLER_PATH = r'C:\\Users\\irish\\Desktop\\poppler-24.08.0\\Library\\bin'
""")
        sys.exit(1)

    print(f"  Page size  : {page_image.width} × {page_image.height} px")

    # ── 3. Visualize field boxes (optional) ──────────────────
    if args.visualize:
        vis     = draw_fields(page_image, fields)
        out_jpg = Path(args.pdf).stem + "_field_map.jpg"
        vis.save(out_jpg, quality=90)
        print(f"\n  ✓ Field map saved → {out_jpg}")
        print("    Open this image to verify boxes align with form fields.")
        print("    If a box is misaligned, adjust the ratio values in BIRTH_FIELDS /")
        print("    DEATH_FIELDS / MARRIAGE_FIELDS at the top of this script.")

    # ── 4. Crop fields ────────────────────────────────────────
    print(f"\n  Cropping {len(fields)} fields...")
    crops = extract_field_images(page_image, fields)
    print(f"  ✓ {len(crops)} field crops extracted")

    # ── 5. Run CRNN OCR ───────────────────────────────────────
    print(f"\n  Running CRNN OCR on {len(crops)} fields...")
    results = run_crnn_ocr(crops, model, idx_to_char, img_h, img_w, device)

    # ── 6. Print results ──────────────────────────────────────
    print(f"\n{'─' * 65}")
    print(f"  {'FIELD':<40}  TEXT")
    print(f"{'─' * 65}")
    for field_name, text in results.items():
        display = text if text else "(empty)"
        print(f"  {field_name:<40}  {display}")
    print(f"{'─' * 65}")

    non_empty = sum(1 for t in results.values() if t.strip())
    print(f"\n  Fields recognized : {non_empty} / {len(results)}")

    # ── 7. Save JSON output (optional) ───────────────────────
    if args.output:
        output_data = {
            "form":   form_label,
            "file":   args.pdf,
            "fields": results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n  ✓ Results saved → {args.output}")

    print()


if __name__ == "__main__":
    main()