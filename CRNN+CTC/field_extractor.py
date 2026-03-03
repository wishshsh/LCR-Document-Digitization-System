"""
Philippine Civil Registry Field Extractor
==========================================
Extracts fields from Forms 97, 102, 103 using relative coordinate ratios.
Uses the trained CRNN+CTC model for OCR (not Tesseract).

Usage:
    python field_extractor.py --pdf FORM_102.pdf --form birth
    python field_extractor.py --pdf FORM_97.pdf  --form marriage --visualize
    python field_extractor.py --pdf FORM_103.pdf --form death    --output results.json
    python field_extractor.py --pdf FORM_102.pdf --form birth    --checkpoint checkpoints/best_model_iam.pth
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
# ─────────────────────────────────────────────
POPPLER_PATH = r"C:\Users\irish\OneDrive\Desktop\poppler-25.12.0\Library\bin"

# ─────────────────────────────────────────────
#  DEFAULT CHECKPOINT
# ─────────────────────────────────────────────
DEFAULT_CHECKPOINT = "checkpoints/best_model.pth"


# ══════════════════════════════════════════════════════════════
#  FIELD COORDINATE MAPS
#  Format: field_name: (x1, y1, x2, y2)  — all values 0.0–1.0
# ══════════════════════════════════════════════════════════════

BIRTH_FIELDS = {
    "province":             (0.038, 0.074, 0.495, 0.086),
    "registry_no":          (0.618, 0.074, 0.963, 0.086),
    "city_municipality":    (0.038, 0.088, 0.580, 0.100),
    "child_first_name":     (0.082, 0.109, 0.435, 0.121),
    "child_middle_name":    (0.435, 0.109, 0.682, 0.121),
    "child_last_name":      (0.682, 0.109, 0.963, 0.121),
    "sex":                  (0.038, 0.136, 0.082, 0.148),
    "dob_day":              (0.192, 0.136, 0.328, 0.148),
    "dob_month":            (0.328, 0.136, 0.492, 0.148),
    "dob_year":             (0.492, 0.136, 0.628, 0.148),
    "place_birth_hospital": (0.082, 0.150, 0.388, 0.163),
    "place_birth_city":     (0.388, 0.150, 0.622, 0.163),
    "place_birth_province": (0.622, 0.150, 0.820, 0.163),
    "weight_at_birth":      (0.820, 0.150, 0.963, 0.163),
    "type_of_birth":        (0.082, 0.166, 0.270, 0.178),
    "multiple_birth_order": (0.270, 0.166, 0.492, 0.178),
    "birth_order":          (0.492, 0.166, 0.700, 0.178),
    "birth_weight_grams":   (0.820, 0.178, 0.963, 0.192),
    "mother_first_name":    (0.082, 0.215, 0.390, 0.228),
    "mother_middle_name":   (0.390, 0.215, 0.635, 0.228),
    "mother_last_name":     (0.635, 0.215, 0.963, 0.228),
    "mother_citizenship":   (0.038, 0.232, 0.082, 0.244),
    "mother_religion":      (0.082, 0.232, 0.390, 0.244),
    "mother_occupation":    (0.492, 0.232, 0.700, 0.244),
    "mother_age_at_birth":  (0.820, 0.232, 0.963, 0.244),
    "mother_children_alive":        (0.082, 0.258, 0.212, 0.270),
    "mother_children_still_living": (0.212, 0.258, 0.362, 0.270),
    "mother_children_born_dead":    (0.362, 0.258, 0.492, 0.270),
    "mother_residence_house":    (0.082, 0.330, 0.262, 0.342),
    "mother_residence_city":     (0.388, 0.330, 0.632, 0.342),
    "mother_residence_province": (0.632, 0.330, 0.820, 0.342),
    "mother_residence_country":  (0.820, 0.330, 0.963, 0.342),
    "father_first_name":    (0.082, 0.356, 0.390, 0.368),
    "father_middle_name":   (0.390, 0.356, 0.635, 0.368),
    "father_last_name":     (0.635, 0.356, 0.963, 0.368),
    "father_citizenship":   (0.038, 0.380, 0.082, 0.392),
    "father_religion":      (0.082, 0.380, 0.390, 0.392),
    "father_occupation":    (0.492, 0.380, 0.700, 0.392),
    "father_age_at_birth":  (0.820, 0.380, 0.963, 0.392),
    "father_residence_house":    (0.082, 0.406, 0.262, 0.418),
    "father_residence_city":     (0.388, 0.406, 0.632, 0.418),
    "father_residence_province": (0.632, 0.406, 0.820, 0.418),
    "father_residence_country":  (0.820, 0.406, 0.963, 0.418),
    "parents_marriage_month":    (0.082, 0.442, 0.198, 0.454),
    "parents_marriage_day":      (0.198, 0.442, 0.270, 0.454),
    "parents_marriage_year":     (0.270, 0.442, 0.355, 0.454),
    "parents_marriage_city":     (0.355, 0.442, 0.555, 0.454),
    "parents_marriage_province": (0.555, 0.442, 0.750, 0.454),
    "parents_marriage_country":  (0.750, 0.442, 0.963, 0.454),
    "informant_name":         (0.082, 0.634, 0.390, 0.646),
    "informant_relationship": (0.082, 0.648, 0.390, 0.660),
    "informant_address":      (0.082, 0.662, 0.390, 0.674),
    "informant_date":         (0.082, 0.676, 0.390, 0.686),
}

DEATH_FIELDS = {
    "province":          (0.038, 0.108, 0.328, 0.120),
    "registry_no":       (0.355, 0.108, 0.560, 0.120),
    "city_municipality": (0.038, 0.122, 0.328, 0.134),
    "deceased_first_name":  (0.095, 0.146, 0.310, 0.158),
    "deceased_middle_name": (0.310, 0.146, 0.545, 0.158),
    "deceased_last_name":   (0.545, 0.146, 0.760, 0.158),
    "sex":        (0.038, 0.172, 0.090, 0.210),
    "religion":   (0.090, 0.172, 0.215, 0.196),
    "age_years":  (0.248, 0.182, 0.335, 0.196),
    "age_months": (0.380, 0.182, 0.455, 0.196),
    "age_days":   (0.455, 0.182, 0.528, 0.196),
    "place_death_hospital": (0.085, 0.206, 0.368, 0.220),
    "place_death_city":     (0.368, 0.206, 0.568, 0.220),
    "place_death_province": (0.568, 0.206, 0.760, 0.220),
    "dod_day":     (0.085, 0.232, 0.175, 0.246),
    "dod_month":   (0.175, 0.232, 0.278, 0.246),
    "dod_year":    (0.278, 0.232, 0.368, 0.246),
    "citizenship": (0.368, 0.232, 0.760, 0.246),
    "residence_house":    (0.085, 0.260, 0.262, 0.274),
    "residence_city":     (0.262, 0.260, 0.472, 0.274),
    "residence_province": (0.472, 0.260, 0.668, 0.274),
    "civil_status": (0.038, 0.288, 0.290, 0.328),
    "occupation":   (0.368, 0.288, 0.668, 0.328),
    "cause_immediate":  (0.150, 0.392, 0.580, 0.406),
    "cause_antecedent": (0.150, 0.418, 0.580, 0.432),
    "cause_underlying": (0.150, 0.444, 0.580, 0.458),
    "cause_other":      (0.085, 0.468, 0.668, 0.482),
    "informant_name":    (0.085, 0.800, 0.368, 0.814),
    "informant_address": (0.368, 0.800, 0.668, 0.814),
    "informant_date":    (0.085, 0.826, 0.250, 0.838),
}

MARRIAGE_FIELDS = {
    "province":          (0.100, 0.058, 0.490, 0.068),
    "city_municipality": (0.100, 0.070, 0.490, 0.080),
    "registry_no":       (0.688, 0.058, 0.963, 0.072),
    "husband_first_name":  (0.100, 0.108, 0.490, 0.120),
    "wife_first_name":     (0.510, 0.108, 0.963, 0.120),
    "husband_middle_name": (0.100, 0.130, 0.490, 0.142),
    "wife_middle_name":    (0.510, 0.130, 0.963, 0.142),
    "husband_last_name":   (0.100, 0.152, 0.490, 0.164),
    "wife_last_name":      (0.510, 0.152, 0.963, 0.164),
    "husband_dob_day":   (0.100, 0.174, 0.175, 0.188),
    "husband_dob_month": (0.175, 0.174, 0.268, 0.188),
    "husband_dob_year":  (0.268, 0.174, 0.362, 0.188),
    "husband_age":       (0.362, 0.174, 0.490, 0.188),
    "wife_dob_day":      (0.510, 0.174, 0.590, 0.188),
    "wife_dob_month":    (0.590, 0.174, 0.678, 0.188),
    "wife_dob_year":     (0.678, 0.174, 0.778, 0.188),
    "wife_age":          (0.778, 0.174, 0.963, 0.188),
    "husband_place_birth":          (0.100, 0.200, 0.212, 0.214),
    "husband_place_birth_city":     (0.212, 0.200, 0.362, 0.214),
    "husband_place_birth_province": (0.362, 0.200, 0.424, 0.214),
    "husband_place_birth_country":  (0.424, 0.200, 0.490, 0.214),
    "wife_place_birth":             (0.510, 0.200, 0.590, 0.214),
    "wife_place_birth_city":        (0.590, 0.200, 0.752, 0.214),
    "wife_place_birth_province":    (0.752, 0.200, 0.862, 0.214),
    "wife_place_birth_country":     (0.862, 0.200, 0.963, 0.214),
    "husband_sex":         (0.100, 0.226, 0.150, 0.238),
    "husband_citizenship": (0.150, 0.226, 0.490, 0.238),
    "wife_sex":            (0.510, 0.226, 0.560, 0.238),
    "wife_citizenship":    (0.560, 0.226, 0.963, 0.238),
    "husband_residence": (0.100, 0.252, 0.490, 0.282),
    "wife_residence":    (0.510, 0.252, 0.963, 0.282),
    "husband_religion": (0.100, 0.298, 0.490, 0.312),
    "wife_religion":    (0.510, 0.298, 0.963, 0.312),
    "husband_civil_status": (0.100, 0.326, 0.490, 0.338),
    "wife_civil_status":    (0.510, 0.326, 0.963, 0.338),
    "husband_father_first":  (0.100, 0.352, 0.242, 0.366),
    "husband_father_middle": (0.242, 0.352, 0.362, 0.366),
    "husband_father_last":   (0.362, 0.352, 0.490, 0.366),
    "wife_father_first":     (0.510, 0.352, 0.640, 0.366),
    "wife_father_middle":    (0.640, 0.352, 0.778, 0.366),
    "wife_father_last":      (0.778, 0.352, 0.963, 0.366),
    "husband_father_citizenship": (0.100, 0.378, 0.490, 0.390),
    "wife_father_citizenship":    (0.510, 0.378, 0.963, 0.390),
    "husband_mother_first":  (0.100, 0.404, 0.222, 0.416),
    "husband_mother_middle": (0.222, 0.404, 0.350, 0.416),
    "husband_mother_last":   (0.350, 0.404, 0.490, 0.416),
    "wife_mother_first":     (0.510, 0.404, 0.635, 0.416),
    "wife_mother_middle":    (0.635, 0.404, 0.778, 0.416),
    "wife_mother_last":      (0.778, 0.404, 0.963, 0.416),
    "husband_mother_citizenship": (0.100, 0.428, 0.490, 0.440),
    "wife_mother_citizenship":    (0.510, 0.428, 0.963, 0.440),
    "husband_consent_first":  (0.100, 0.452, 0.228, 0.466),
    "husband_consent_middle": (0.228, 0.452, 0.355, 0.466),
    "husband_consent_last":   (0.355, 0.452, 0.490, 0.466),
    "wife_consent_first":     (0.510, 0.452, 0.630, 0.466),
    "wife_consent_middle":    (0.630, 0.452, 0.778, 0.466),
    "wife_consent_last":      (0.778, 0.452, 0.963, 0.466),
    "husband_relationship": (0.100, 0.480, 0.490, 0.492),
    "wife_relationship":    (0.510, 0.480, 0.963, 0.492),
    "husband_residence2": (0.100, 0.502, 0.490, 0.514),
    "wife_residence2":    (0.510, 0.502, 0.963, 0.514),
    "husband_residence14": (0.100, 0.524, 0.490, 0.562),
    "wife_residence14":    (0.510, 0.524, 0.963, 0.562),
    "place_marriage_office":   (0.100, 0.582, 0.490, 0.594),
    "place_marriage_city":     (0.490, 0.582, 0.748, 0.594),
    "place_marriage_province": (0.748, 0.582, 0.963, 0.594),
    "place_marriage_venue":    (0.100, 0.596, 0.490, 0.608),
    "date_marriage_day":   (0.100, 0.622, 0.178, 0.634),
    "date_marriage_month": (0.178, 0.622, 0.310, 0.634),
    "date_marriage_year":  (0.310, 0.622, 0.412, 0.634),
    "time_marriage":       (0.650, 0.614, 0.963, 0.628),
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
#  Same pipeline as check_cer.py / inference.py:
#    crop → resize (grayscale) → binarize LAST
# ══════════════════════════════════════════════════════════════

class FieldNormalizer:
    """
    Normalizes a cropped field image for CRNN inference.
    Handles small field crops from scanned PDFs — applies
    denoising + adaptive binarization before passing to the model.
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
        import numpy as np
        img = np.array(pil_image.convert("RGB"))
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
    char_to_idx = c["char_to_idx"]
    idx_to_char = c["idx_to_char"]

    model = get_crnn_model(
        model_type=config.get("model_type", "standard"),
        img_height=img_h,
        num_chars=len(char_to_idx),
        hidden_size=config.get("hidden_size", 256),
        num_lstm_layers=config.get("num_lstm_layers", 2),
    ).to(device)
    model.load_state_dict(c["model_state_dict"])
    model.eval()

    val_cer = c.get("val_cer", None)
    print(f"  Model loaded  |  val_cer={val_cer:.2f}%  |  chars={len(char_to_idx)}")
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
    Empty fields (blank/no ink) are returned as empty string.
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

    model, idx_to_char, img_h, img_w = load_crnn_model(
        args.checkpoint, device)

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