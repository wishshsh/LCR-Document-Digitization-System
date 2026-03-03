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
    # Header
    "province":             (0.038, 0.068, 0.490, 0.088),
    "registry_no":          (0.618, 0.068, 0.963, 0.088),
    "city_municipality":    (0.038, 0.100, 0.580, 0.122),
    # Item 1: Child Name (grid row y=136-174 => ratio 0.133-0.170)
    "child_first_name":     (0.082, 0.145, 0.435, 0.163),
    "child_middle_name":    (0.435, 0.145, 0.682, 0.163),
    "child_last_name":      (0.682, 0.145, 0.963, 0.163),
    # Items 2-3: Sex / Date of Birth (y=174-197 => 0.170-0.192)
    "sex":                  (0.038, 0.175, 0.195, 0.191),
    "dob_day":              (0.290, 0.175, 0.415, 0.191),
    "dob_month":            (0.415, 0.175, 0.600, 0.191),
    "dob_year":             (0.600, 0.175, 0.963, 0.191),
    # Item 4: Place of Birth (y=208-240 => 0.203-0.234)
    "place_birth_hospital": (0.082, 0.210, 0.388, 0.228),
    "place_birth_city":     (0.388, 0.210, 0.622, 0.228),
    "place_birth_province": (0.622, 0.210, 0.820, 0.228),
    "weight_at_birth":      (0.820, 0.210, 0.963, 0.228),
    # Items 5-6: Type/Order/Weight (y=197-208 => 0.192-0.203)
    "type_of_birth":        (0.082, 0.193, 0.270, 0.208),
    "multiple_birth_order": (0.270, 0.193, 0.492, 0.208),
    "birth_order":          (0.492, 0.193, 0.700, 0.208),
    "birth_weight_grams":   (0.820, 0.228, 0.963, 0.240),
    # Item 7: Mother Maiden Name (y=240-265 => 0.234-0.259)
    "mother_first_name":    (0.082, 0.238, 0.390, 0.254),
    "mother_middle_name":   (0.390, 0.238, 0.635, 0.254),
    "mother_last_name":     (0.635, 0.238, 0.963, 0.254),
    # Items 8-12: Mother details (y=265-340 => 0.259-0.332)
    "mother_citizenship":   (0.038, 0.262, 0.130, 0.278),
    "mother_religion":      (0.130, 0.262, 0.490, 0.278),
    "mother_occupation":    (0.492, 0.262, 0.730, 0.278),
    "mother_age_at_birth":  (0.820, 0.262, 0.963, 0.278),
    # Items 10a-c: Children count (y=340-364 => 0.332-0.355)
    "mother_children_alive":        (0.082, 0.334, 0.245, 0.350),
    "mother_children_still_living": (0.245, 0.334, 0.388, 0.350),
    "mother_children_born_dead":    (0.388, 0.334, 0.492, 0.350),
    # Item 13: Mother Residence (y=364-390 => 0.355-0.381)
    "mother_residence_house":    (0.082, 0.358, 0.262, 0.374),
    "mother_residence_city":     (0.262, 0.358, 0.490, 0.374),
    "mother_residence_province": (0.490, 0.358, 0.680, 0.374),
    "mother_residence_country":  (0.680, 0.358, 0.963, 0.374),
    # Item 14: Father Name (y=390-415 => 0.381-0.405)
    "father_first_name":    (0.082, 0.383, 0.390, 0.400),
    "father_middle_name":   (0.390, 0.383, 0.635, 0.400),
    "father_last_name":     (0.635, 0.383, 0.963, 0.400),
    # Items 15-18: Father details (y=415-438 => 0.405-0.428)
    "father_citizenship":   (0.038, 0.408, 0.130, 0.424),
    "father_religion":      (0.130, 0.408, 0.390, 0.424),
    "father_occupation":    (0.490, 0.408, 0.730, 0.424),
    "father_age_at_birth":  (0.820, 0.408, 0.963, 0.424),
    # Item 19: Father Residence (y=464-510 => 0.453-0.498)
    "father_residence_house":    (0.082, 0.455, 0.262, 0.472),
    "father_residence_city":     (0.262, 0.455, 0.490, 0.472),
    "father_residence_province": (0.490, 0.455, 0.680, 0.472),
    "father_residence_country":  (0.680, 0.455, 0.963, 0.472),
    # Item 20a: Marriage of Parents (y=510-578 => 0.498-0.565)
    "parents_marriage_month":    (0.082, 0.502, 0.198, 0.518),
    "parents_marriage_day":      (0.198, 0.502, 0.270, 0.518),
    "parents_marriage_year":     (0.270, 0.502, 0.355, 0.518),
    "parents_marriage_city":     (0.355, 0.502, 0.555, 0.518),
    "parents_marriage_province": (0.555, 0.502, 0.750, 0.518),
    "parents_marriage_country":  (0.750, 0.502, 0.963, 0.518),
    # Item 22: Informant (y=656+ => 0.641+)
    "informant_name":         (0.082, 0.645, 0.390, 0.660),
    "informant_address":      (0.082, 0.660, 0.390, 0.675),
    "informant_date":         (0.082, 0.675, 0.250, 0.688),
}

DEATH_FIELDS = {
    # Header (below instruction text)
    "province":          (0.038, 0.078, 0.328, 0.096),
    "registry_no":       (0.420, 0.078, 0.700, 0.096),
    "city_municipality": (0.038, 0.096, 0.328, 0.114),
    # Item 1: Name + Sex (y=181 => 0.177)
    "deceased_first_name":  (0.095, 0.180, 0.310, 0.198),
    "deceased_middle_name": (0.310, 0.180, 0.545, 0.198),
    "deceased_last_name":   (0.545, 0.180, 0.760, 0.198),
    "sex":                  (0.760, 0.180, 0.963, 0.198),
    # Items 3-5: Dates / Age (y=~220-276)
    "dod_day":   (0.038, 0.224, 0.148, 0.242),
    "dod_month": (0.148, 0.224, 0.280, 0.242),
    "dod_year":  (0.280, 0.224, 0.390, 0.242),
    "dob_day":   (0.390, 0.224, 0.480, 0.242),
    "dob_month": (0.480, 0.224, 0.590, 0.242),
    "dob_year":  (0.590, 0.224, 0.680, 0.242),
    "age_years": (0.680, 0.224, 0.760, 0.242),
    # Item 6: Place of Death (y=276 => 0.270)
    "place_death_full": (0.038, 0.272, 0.700, 0.302),
    # Item 7: Civil Status (y=320 => 0.313)
    "civil_status": (0.038, 0.316, 0.380, 0.346),
    # Items 8-9: Religion / Citizenship (y=361 => 0.352)
    "religion":    (0.038, 0.354, 0.380, 0.374),
    "citizenship": (0.380, 0.354, 0.700, 0.374),
    # Item 9 cont: Residence
    "residence_full": (0.038, 0.380, 0.700, 0.406),
    # Items 11-13: Occupation / Father / Mother (y=479 => 0.468)
    "occupation":  (0.038, 0.470, 0.310, 0.490),
    "father_name": (0.310, 0.470, 0.630, 0.490),
    "mother_name": (0.630, 0.470, 0.963, 0.490),
    # Item 19b: Causes of Death (y=537 => 0.524)
    "cause_immediate":  (0.168, 0.540, 0.580, 0.558),
    "cause_antecedent": (0.168, 0.572, 0.580, 0.590),
    "cause_underlying": (0.168, 0.604, 0.580, 0.622),
    "cause_other":      (0.038, 0.636, 0.700, 0.658),
    # Item 26: Informant (y=835 => 0.815)
    "informant_name":    (0.038, 0.820, 0.310, 0.838),
    "informant_address": (0.038, 0.856, 0.580, 0.872),
    "informant_date":    (0.038, 0.874, 0.250, 0.888),
}

MARRIAGE_FIELDS = {
    # Header
    "province":          (0.100, 0.068, 0.490, 0.082),
    "city_municipality": (0.100, 0.082, 0.490, 0.100),
    "registry_no":       (0.688, 0.068, 0.963, 0.082),
    # Item 1: Names (y=135-184 => 0.132-0.180, 3 sub-rows)
    "husband_first_name":  (0.100, 0.134, 0.490, 0.150),
    "wife_first_name":     (0.510, 0.134, 0.963, 0.150),
    "husband_middle_name": (0.100, 0.152, 0.490, 0.166),
    "wife_middle_name":    (0.510, 0.152, 0.963, 0.166),
    "husband_last_name":   (0.100, 0.168, 0.490, 0.182),
    "wife_last_name":      (0.510, 0.168, 0.963, 0.182),
    # Items 2a-b: DOB / Age (y=184-210 => 0.180-0.205)
    "husband_dob_day":   (0.100, 0.182, 0.175, 0.198),
    "husband_dob_month": (0.175, 0.182, 0.268, 0.198),
    "husband_dob_year":  (0.268, 0.182, 0.362, 0.198),
    "husband_age":       (0.362, 0.182, 0.490, 0.198),
    "wife_dob_day":      (0.510, 0.182, 0.590, 0.198),
    "wife_dob_month":    (0.590, 0.182, 0.678, 0.198),
    "wife_dob_year":     (0.678, 0.182, 0.778, 0.198),
    "wife_age":          (0.778, 0.182, 0.963, 0.198),
    # Item 3: Place of Birth (y=210-234 => 0.205-0.229)
    "husband_place_birth_city":     (0.100, 0.207, 0.268, 0.226),
    "husband_place_birth_province": (0.268, 0.207, 0.390, 0.226),
    "husband_place_birth_country":  (0.390, 0.207, 0.490, 0.226),
    "wife_place_birth_city":        (0.510, 0.207, 0.678, 0.226),
    "wife_place_birth_province":    (0.678, 0.207, 0.820, 0.226),
    "wife_place_birth_country":     (0.820, 0.207, 0.963, 0.226),
    # Items 4a-b: Sex / Citizenship (y=234-266 => 0.229-0.260)
    "husband_sex":         (0.100, 0.231, 0.175, 0.250),
    "husband_citizenship": (0.175, 0.231, 0.490, 0.250),
    "wife_sex":            (0.510, 0.231, 0.590, 0.250),
    "wife_citizenship":    (0.590, 0.231, 0.963, 0.250),
    # Item 5: Residence (y=266-329 => 0.260-0.321)
    "husband_residence": (0.100, 0.262, 0.490, 0.318),
    "wife_residence":    (0.510, 0.262, 0.963, 0.318),
    # Item 6: Religion (y=329-377 => 0.321-0.368)
    "husband_religion": (0.100, 0.323, 0.490, 0.356),
    "wife_religion":    (0.510, 0.323, 0.963, 0.356),
    # Item 7: Civil Status (y=377-444 => 0.368-0.434)
    "husband_civil_status": (0.100, 0.370, 0.490, 0.430),
    "wife_civil_status":    (0.510, 0.370, 0.963, 0.430),
    # Item 8: Father Names (y=444-489 => 0.434-0.478)
    "husband_father_first":  (0.100, 0.436, 0.242, 0.455),
    "husband_father_middle": (0.242, 0.436, 0.362, 0.455),
    "husband_father_last":   (0.362, 0.436, 0.490, 0.455),
    "wife_father_first":     (0.510, 0.436, 0.640, 0.455),
    "wife_father_middle":    (0.640, 0.436, 0.778, 0.455),
    "wife_father_last":      (0.778, 0.436, 0.963, 0.455),
    # Item 9: Father Citizenship (y=489-501 => 0.478-0.489)
    "husband_father_citizenship": (0.100, 0.480, 0.490, 0.496),
    "wife_father_citizenship":    (0.510, 0.480, 0.963, 0.496),
    # Item 10: Mother Names (y=501-550 => 0.489-0.537)
    "husband_mother_first":  (0.100, 0.492, 0.222, 0.510),
    "husband_mother_middle": (0.222, 0.492, 0.350, 0.510),
    "husband_mother_last":   (0.350, 0.492, 0.490, 0.510),
    "wife_mother_first":     (0.510, 0.492, 0.635, 0.510),
    "wife_mother_middle":    (0.635, 0.492, 0.778, 0.510),
    "wife_mother_last":      (0.778, 0.492, 0.963, 0.510),
    # Item 11: Mother Citizenship (y=550-565 => 0.537-0.552)
    "husband_mother_citizenship": (0.100, 0.539, 0.490, 0.555),
    "wife_mother_citizenship":    (0.510, 0.539, 0.963, 0.555),
    # Item 12: Consent Names (y=565-617 => 0.552-0.603)
    "husband_consent_first":  (0.100, 0.554, 0.228, 0.572),
    "husband_consent_middle": (0.228, 0.554, 0.355, 0.572),
    "husband_consent_last":   (0.355, 0.554, 0.490, 0.572),
    "wife_consent_first":     (0.510, 0.554, 0.630, 0.572),
    "wife_consent_middle":    (0.630, 0.554, 0.778, 0.572),
    "wife_consent_last":      (0.778, 0.554, 0.963, 0.572),
    # Item 13: Relationship (y=617-638 => 0.603-0.623)
    "husband_relationship": (0.100, 0.605, 0.490, 0.622),
    "wife_relationship":    (0.510, 0.605, 0.963, 0.622),
    # Item 14: Residence of Consent (y=638-704 => 0.623-0.688)
    "husband_residence2": (0.100, 0.625, 0.490, 0.674),
    "wife_residence2":    (0.510, 0.625, 0.963, 0.674),
    # Item 15: Place of Marriage (y=704-737 => 0.688-0.720)
    "place_marriage_office":   (0.100, 0.690, 0.490, 0.705),
    "place_marriage_city":     (0.490, 0.690, 0.748, 0.705),
    "place_marriage_province": (0.748, 0.690, 0.963, 0.705),
    # Items 16-17: Date / Time (y=737+ => 0.720+)
    "date_marriage_day":   (0.100, 0.722, 0.178, 0.736),
    "date_marriage_month": (0.178, 0.722, 0.310, 0.736),
    "date_marriage_year":  (0.310, 0.722, 0.412, 0.736),
    "time_marriage":       (0.640, 0.716, 0.920, 0.730),
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