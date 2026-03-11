"""
Philippine Civil Registry — Field Extractor (Dynamic)
======================================================
Automatically detects form borders on ANY scan/photo and aligns field
extraction to the detected boundary — no hardcoded pixel positions.

Field coordinates calibrated directly from official PDF renders at 200 DPI:
  Form 102 (Birth):    1700 x 2800 px
  Form 103 (Death):    1700 x 2878 px
  Form 97  (Marriage): 1700 x 2600 px
  Form 90  (License):  1700 x 2600 px

Usage:
    python field_extractor.py --pdf  FORM_102.pdf --form birth
    python field_extractor.py --pdf  FORM_97.pdf  --form marriage --visualize
    python field_extractor.py --pdf  FORM_103.pdf --form death    --output results.json
    python field_extractor.py --image form102.png --form birth    --visualize
    python field_extractor.py --pdf  FORM_102.pdf --form birth    --checkpoint checkpoints/best_model_emnist.pth

.env file (project root) — each team member sets their own:
    POPPLER_PATH=C:\\your\\path\\to\\poppler\\Library\\bin
"""

import argparse
import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

import torch
from dotenv import load_dotenv

# Load .env first — must happen before POPPLER_PATH is read
load_dotenv()

# Poppler path from .env, falls back to None (Linux/Mac works without it)
POPPLER_PATH    = os.environ.get("POPPLER_PATH", None)
DEFAULT_CHECKPOINT = "checkpoints/best_model.pth"


# ══════════════════════════════════════════════════════════════════════════════
#  FIELD RATIO MAPS
#  Format: field_name: (x1, y1, x2, y2) — ratios 0.0–1.0
#  Coordinates are relative to the DETECTED FORM BOUNDARY (not full image).
#  x = left→right,  y = top→bottom
# ══════════════════════════════════════════════════════════════════════════════

# Form 102 → Certificate of Live Birth (Form 1A)
BIRTH_FIELDS = {
    # Header
    "province":                   (0.02, 0.068, 0.65, 0.088),
    "registry_number":            (0.66, 0.068, 0.99, 0.108),
    "city_municipality":          (0.02, 0.090, 0.65, 0.108),

    # Item 1 — Child Name
    "child_first_name":           (0.03, 0.109, 0.40, 0.141),
    "child_middle_name":          (0.40, 0.109, 0.64, 0.141),
    "child_last_name":            (0.64, 0.109, 0.99, 0.141),

    # Items 2-3 — Sex / Date of Birth
    "sex":                        (0.03, 0.142, 0.30, 0.167),
    "dob_day":                    (0.40, 0.142, 0.80, 0.167),
    "dob_month":                  (0.80, 0.142, 0.60, 0.167),
    "dob_year":                   (0.80, 0.142, 0.99, 0.167),

    # Item 4 — Place of Birth
    "place_birth_hospital":       (0.03, 0.169, 0.46, 0.197),
    "place_birth_city":           (0.47, 0.169, 0.70, 0.199),
    "place_birth_province":       (0.71, 0.169, 0.99, 0.199),

  

    # Mother section
    "mother_first_name":          (0.03, 0.248, 0.40, 0.276),
    "mother_middle_name":         (0.40, 0.248, 0.64, 0.276),
    "mother_last_name":           (0.64, 0.248, 0.99, 0.276),
    "mother_citizenship":         (0.03, 0.277, 0.50, 0.305),
    

    # Father section
    "father_first_name":          (0.03, 0.380, 0.40, 0.410),
    "father_middle_name":         (0.40, 0.380, 0.64, 0.410),
    "father_last_name":           (0.64, 0.380, 0.99, 0.410),
    "father_citizenship":         (0.03, 0.411, 0.28, 0.445),
   

    # Item 20 — Marriage of Parents
    "parents_marriage_month":     (0.03, 0.496, 0.19, 0.526),
    "parents_marriage_day":       (0.19, 0.496, 0.27, 0.526),
    "parents_marriage_year":      (0.27, 0.496, 0.38, 0.526),
    
    "parents_marriage_city":      (0.41, 0.496, 0.68, 0.526),
    "parents_marriage_province":  (0.68, 0.496, 0.84, 0.526),

   
}

# Form 103 → Certificate of Death (Form 2A)
DEATH_FIELDS = {
    # Header
    "province":                   (0.04, 0.128, 0.45, 0.144),
    "registry_number":            (0.52, 0.128, 0.75, 0.144),
    "city_municipality":          (0.04, 0.145, 0.45, 0.160),

    # Item 1 — Name
    "deceased_first_name":        (0.10, 0.162, 0.34, 0.178),
    "deceased_middle_name":       (0.34, 0.162, 0.56, 0.178),
    "deceased_last_name":         (0.56, 0.162, 0.75, 0.178),

    # Items 2-4 — Sex / Religion / Age
    "sex":                        (0.04, 0.182, 0.13, 0.220),
    "religion":                   (0.13, 0.182, 0.28, 0.220),
    "age_years":                  (0.28, 0.182, 0.38, 0.202),

    # Item 5 — Place of Death
    "place_death_hospital":       (0.13, 0.224, 0.42, 0.242),
    "place_death_city":           (0.42, 0.224, 0.58, 0.242),
    "place_death_province":       (0.58, 0.224, 0.75, 0.242),

    # Items 6-7 — Date of Death / Citizenship
    "dod_day":                    (0.10, 0.252, 0.22, 0.268),
    "dod_month":                  (0.22, 0.252, 0.38, 0.268),
    "dod_year":                   (0.38, 0.252, 0.52, 0.268),
    "citizenship":                (0.52, 0.252, 0.75, 0.268),

    # Item 8 — Residence
    "residence_house":            (0.13, 0.278, 0.40, 0.294),
    "residence_city":             (0.40, 0.278, 0.56, 0.294),
    "residence_province":         (0.56, 0.278, 0.75, 0.294),

    # Items 9-10 — Civil Status / Occupation
    "civil_status":               (0.04, 0.302, 0.38, 0.360),
    "occupation":                 (0.44, 0.302, 0.75, 0.360),

    # Item 17 — Causes of Death
    "cause_immediate":            (0.18, 0.402, 0.58, 0.418),
    "cause_antecedent":           (0.18, 0.424, 0.58, 0.440),
    "cause_underlying":           (0.18, 0.446, 0.58, 0.462),
    "cause_other":                (0.18, 0.468, 0.58, 0.484),

    # Item 25 — Informant
    "informant_name":             (0.04, 0.808, 0.35, 0.822),
    "informant_address":          (0.04, 0.822, 0.35, 0.836),
    "informant_date":             (0.35, 0.836, 0.58, 0.850),
}

# Form 97 → Certificate of Marriage (Form 3A)
MARRIAGE_FIELDS = {
    # Header
    "province":                   (0.14, 0.088, 0.52, 0.104),
    "registry_number":            (0.62, 0.088, 0.97, 0.104),
    "city_municipality":          (0.14, 0.104, 0.52, 0.120),

    # Item 1 — Names (HUSBAND left / WIFE right)
    "husband_first_name":         (0.14, 0.138, 0.47, 0.156),
    "wife_first_name":            (0.53, 0.138, 0.86, 0.156),
    "husband_middle_name":        (0.14, 0.156, 0.47, 0.174),
    "wife_middle_name":           (0.53, 0.156, 0.86, 0.174),
    "husband_last_name":          (0.14, 0.174, 0.47, 0.192),
    "wife_last_name":             (0.53, 0.174, 0.86, 0.192),

    # Item 2 — Date of Birth / Age
    "husband_dob_day":            (0.14, 0.198, 0.22, 0.216),
    "husband_dob_month":          (0.22, 0.198, 0.32, 0.216),
    "husband_dob_year":           (0.32, 0.198, 0.40, 0.216),
    "husband_age":                (0.40, 0.198, 0.47, 0.216),
    "wife_dob_day":               (0.53, 0.198, 0.60, 0.216),
    "wife_dob_month":             (0.60, 0.198, 0.70, 0.216),
    "wife_dob_year":              (0.70, 0.198, 0.78, 0.216),
    "wife_age":                   (0.78, 0.198, 0.86, 0.216),

    # Item 3 — Place of Birth
    "husband_place_birth_city":   (0.14, 0.222, 0.28, 0.242),
    "husband_place_birth_prov":   (0.28, 0.222, 0.40, 0.242),
    "husband_place_birth_country":(0.40, 0.222, 0.47, 0.242),
    "wife_place_birth_city":      (0.53, 0.222, 0.66, 0.242),
    "wife_place_birth_prov":      (0.66, 0.222, 0.78, 0.242),
    "wife_place_birth_country":   (0.78, 0.222, 0.86, 0.242),

    # Items 4a-b — Sex / Citizenship
    "husband_sex":                (0.14, 0.252, 0.22, 0.270),
    "husband_citizenship":        (0.22, 0.252, 0.47, 0.270),
    "wife_sex":                   (0.53, 0.252, 0.62, 0.270),
    "wife_citizenship":           (0.62, 0.252, 0.86, 0.270),

    # Item 5 — Residence
    "husband_residence":          (0.14, 0.282, 0.47, 0.330),
    "wife_residence":             (0.53, 0.282, 0.86, 0.330),

    # Item 6 — Religion
    "husband_religion":           (0.14, 0.336, 0.47, 0.354),
    "wife_religion":              (0.53, 0.336, 0.86, 0.354),

    # Item 7 — Civil Status
    "husband_civil_status":       (0.14, 0.360, 0.47, 0.378),
    "wife_civil_status":          (0.53, 0.360, 0.86, 0.378),

    # Item 8 — Father Name
    "husband_father_first":       (0.14, 0.396, 0.24, 0.414),
    "husband_father_middle":      (0.24, 0.396, 0.34, 0.414),
    "husband_father_last":        (0.34, 0.396, 0.47, 0.414),
    "wife_father_first":          (0.53, 0.396, 0.63, 0.414),
    "wife_father_middle":         (0.63, 0.396, 0.73, 0.414),
    "wife_father_last":           (0.73, 0.396, 0.86, 0.414),

    # Item 9 — Father Citizenship
    "husband_father_citizenship": (0.14, 0.420, 0.47, 0.436),
    "wife_father_citizenship":    (0.53, 0.420, 0.86, 0.436),

    # Item 10 — Mother Name
    "husband_mother_first":       (0.14, 0.444, 0.24, 0.462),
    "husband_mother_middle":      (0.24, 0.444, 0.34, 0.462),
    "husband_mother_last":        (0.34, 0.444, 0.47, 0.462),
    "wife_mother_first":          (0.53, 0.444, 0.63, 0.462),
    "wife_mother_middle":         (0.63, 0.444, 0.73, 0.462),
    "wife_mother_last":           (0.73, 0.444, 0.86, 0.462),

    # Item 11 — Mother Citizenship
    "husband_mother_citizenship": (0.14, 0.468, 0.47, 0.484),
    "wife_mother_citizenship":    (0.53, 0.468, 0.86, 0.484),

    # Items 15-16 — Place / Date of Marriage
    "place_marriage_office":      (0.14, 0.596, 0.44, 0.614),
    "place_marriage_city":        (0.44, 0.596, 0.68, 0.614),
    "place_marriage_province":    (0.68, 0.596, 0.88, 0.614),
    "date_marriage_day":          (0.14, 0.630, 0.24, 0.648),
    "date_marriage_month":        (0.24, 0.630, 0.38, 0.648),
    "date_marriage_year":         (0.38, 0.630, 0.48, 0.648),
}

# Form 90 → Application for Marriage License
MARRIAGE_LICENSE_FIELDS = {
    # Header
    "province":                   (0.12, 0.092, 0.48, 0.108),
    "registry_number":            (0.56, 0.092, 0.97, 0.108),
    "city_municipality":          (0.12, 0.108, 0.48, 0.124),
    "received_by":                (0.12, 0.124, 0.48, 0.140),
    "date_of_receipt":            (0.12, 0.140, 0.48, 0.156),
    "marriage_license_number":    (0.56, 0.124, 0.97, 0.140),
    "date_of_issuance":           (0.56, 0.140, 0.97, 0.156),

    # Item 1 — Name of Applicant (GROOM left / BRIDE right)
    "groom_first_name":           (0.02, 0.278, 0.46, 0.294),
    "bride_first_name":           (0.54, 0.278, 0.97, 0.294),
    "groom_middle_name":          (0.02, 0.296, 0.46, 0.312),
    "bride_middle_name":          (0.54, 0.296, 0.97, 0.312),
    "groom_last_name":            (0.02, 0.314, 0.46, 0.330),
    "bride_last_name":            (0.54, 0.314, 0.97, 0.330),

    # Item 2 — Date of Birth / Age
    "groom_dob_day":              (0.02, 0.334, 0.12, 0.350),
    "groom_dob_month":            (0.12, 0.334, 0.24, 0.350),
    "groom_dob_year":             (0.24, 0.334, 0.34, 0.350),
    "groom_age":                  (0.34, 0.334, 0.46, 0.350),
    "bride_dob_day":              (0.54, 0.334, 0.62, 0.350),
    "bride_dob_month":            (0.62, 0.334, 0.74, 0.350),
    "bride_dob_year":             (0.74, 0.334, 0.84, 0.350),
    "bride_age":                  (0.84, 0.334, 0.97, 0.350),

    # Item 3 — Place of Birth
    "groom_place_birth_city":     (0.02, 0.354, 0.18, 0.370),
    "groom_place_birth_province": (0.18, 0.354, 0.32, 0.370),
    "groom_place_birth_country":  (0.32, 0.354, 0.46, 0.370),
    "bride_place_birth_city":     (0.54, 0.354, 0.70, 0.370),
    "bride_place_birth_province": (0.70, 0.354, 0.84, 0.370),
    "bride_place_birth_country":  (0.84, 0.354, 0.97, 0.370),

    # Item 4 — Sex / Citizenship
    "groom_sex":                  (0.02, 0.374, 0.16, 0.390),
    "groom_citizenship":          (0.16, 0.374, 0.46, 0.390),
    "bride_sex":                  (0.54, 0.374, 0.68, 0.390),
    "bride_citizenship":          (0.68, 0.374, 0.97, 0.390),

    # Item 5 — Residence
    "groom_residence":            (0.02, 0.394, 0.46, 0.412),
    "bride_residence":            (0.54, 0.394, 0.97, 0.412),

    # Item 6 — Religion
    "groom_religion":             (0.02, 0.424, 0.46, 0.440),
    "bride_religion":             (0.54, 0.424, 0.97, 0.440),

    # Item 7 — Civil Status
    "groom_civil_status":         (0.02, 0.452, 0.46, 0.468),
    "bride_civil_status":         (0.54, 0.452, 0.97, 0.468),

    # Item 9 — Place where dissolved
    "groom_dissolution_city":     (0.02, 0.496, 0.16, 0.512),
    "groom_dissolution_province": (0.16, 0.496, 0.30, 0.512),
    "groom_dissolution_country":  (0.30, 0.496, 0.46, 0.512),
    "bride_dissolution_city":     (0.54, 0.496, 0.68, 0.512),
    "bride_dissolution_province": (0.68, 0.496, 0.82, 0.512),
    "bride_dissolution_country":  (0.82, 0.496, 0.97, 0.512),

    # Item 10 — Date when dissolved
    "groom_dissolution_day":      (0.02, 0.520, 0.12, 0.536),
    "groom_dissolution_month":    (0.12, 0.520, 0.24, 0.536),
    "groom_dissolution_year":     (0.24, 0.520, 0.34, 0.536),
    "bride_dissolution_day":      (0.54, 0.520, 0.62, 0.536),
    "bride_dissolution_month":    (0.62, 0.520, 0.74, 0.536),
    "bride_dissolution_year":     (0.74, 0.520, 0.84, 0.536),

    # Item 12 — Father Name
    "groom_father_first":         (0.02, 0.594, 0.16, 0.610),
    "groom_father_middle":        (0.16, 0.594, 0.28, 0.610),
    "groom_father_last":          (0.28, 0.594, 0.46, 0.610),
    "bride_father_first":         (0.54, 0.594, 0.66, 0.610),
    "bride_father_middle":        (0.66, 0.594, 0.78, 0.610),
    "bride_father_last":          (0.78, 0.594, 0.97, 0.610),

    # Item 13 — Father Citizenship
    "groom_father_citizenship":   (0.02, 0.620, 0.46, 0.636),
    "bride_father_citizenship":   (0.54, 0.620, 0.97, 0.636),

    # Item 14 — Father Residence
    "groom_father_residence":     (0.02, 0.644, 0.46, 0.660),
    "bride_father_residence":     (0.54, 0.644, 0.97, 0.660),

    # Item 15 — Mother Name
    "groom_mother_first":         (0.02, 0.674, 0.16, 0.690),
    "groom_mother_middle":        (0.16, 0.674, 0.28, 0.690),
    "groom_mother_last":          (0.28, 0.674, 0.46, 0.690),
    "bride_mother_first":         (0.54, 0.674, 0.66, 0.690),
    "bride_mother_middle":        (0.66, 0.674, 0.78, 0.690),
    "bride_mother_last":          (0.78, 0.674, 0.97, 0.690),

    # Item 16 — Mother Citizenship
    "groom_mother_citizenship":   (0.02, 0.696, 0.46, 0.712),
    "bride_mother_citizenship":   (0.54, 0.696, 0.97, 0.712),

    # Item 17 — Mother Residence
    "groom_mother_residence":     (0.02, 0.720, 0.46, 0.736),
    "bride_mother_residence":     (0.54, 0.720, 0.97, 0.736),
}

FORM_FIELDS = {
    "birth":            BIRTH_FIELDS,
    "death":            DEATH_FIELDS,
    "marriage":         MARRIAGE_FIELDS,
    "marriage_license": MARRIAGE_LICENSE_FIELDS,
}

COLOURS = [
    (0,200,0),(0,150,255),(200,0,200),(0,200,200),(200,200,0),(220,20,60),
    (255,140,0),(150,50,200),(0,160,80),(30,144,255),(255,20,147),(100,200,100),
]


# ══════════════════════════════════════════════════════════════════════════════
#  FORM BOUNDS DETECTOR
#  Finds the outer border of a civil registry form using line detection.
#  Falls back to full image if detection fails.
# ══════════════════════════════════════════════════════════════════════════════

class FormBoundsDetector:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def detect(self, image_bgr):
        h, w   = image_bgr.shape[:2]
        gray   = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        bounds = self._detect_by_lines(gray, w, h)
        if bounds is None:
            if self.verbose:
                print("  [Bounds] Line detection failed — using full image")
            return (0, 0, w, h)
        if self.verbose:
            print(f"  [Bounds] Detected: {bounds}")
        return bounds

    def _detect_by_lines(self, gray, w, h):
        try:
            thresh  = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2)
            hk      = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 5, 10), 1))
            h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hk)
            h_rows  = np.where(np.sum(h_lines, axis=1) > w * 0.15)[0]
            vk      = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 5, 10)))
            v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vk)
            v_cols  = np.where(np.sum(v_lines, axis=0) > h * 0.08)[0]
            if len(h_rows) == 0 or len(v_cols) == 0:
                return None
            top, bottom = int(h_rows.min()), int(h_rows.max())
            left, right = int(v_cols.min()), int(v_cols.max())
            if (right - left) < w * 0.4 or (bottom - top) < h * 0.4:
                return None
            return (left, top, right, bottom)
        except Exception as e:
            if self.verbose:
                print(f"  [Bounds error] {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
#  DYNAMIC FIELD EXTRACTOR
#  Crops each field region relative to the detected form boundary.
#  Works on any image size, DPI, scan margin, or slight rotation.
# ══════════════════════════════════════════════════════════════════════════════

class DynamicFieldExtractor:
    def __init__(self, form_type="birth", verbose=False):
        self.form_type    = form_type.lower()
        self.field_map    = FORM_FIELDS.get(self.form_type, BIRTH_FIELDS)
        self.detector     = FormBoundsDetector(verbose=verbose)
        self.verbose      = verbose
        self._last_bounds = None

    def _to_bgr(self, image):
        try:
            from PIL import Image as PILImage
            if isinstance(image, PILImage.Image):
                arr = np.array(image.convert("RGB"))
                return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except ImportError:
            pass
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            return image
        raise TypeError(f"Unsupported image type: {type(image)}")

    def extract(self, image):
        """Returns {field_name: BGR numpy array}."""
        image = self._to_bgr(image)
        h, w  = image.shape[:2]
        left, top, right, bottom = self.detector.detect(image)
        self._last_bounds = (left, top, right, bottom)
        form_w = right - left
        form_h = bottom - top
        if self.verbose:
            print(f"  [Extract] Image={w}x{h} "
                  f" Form={form_w}x{form_h} @ ({left},{top})-({right},{bottom})")
        crops = {}
        for name, (rx1, ry1, rx2, ry2) in self.field_map.items():
            x1 = max(0, min(int(left + rx1 * form_w), w - 1))
            y1 = max(0, min(int(top  + ry1 * form_h), h - 1))
            x2 = max(0, min(int(left + rx2 * form_w), w - 1))
            y2 = max(0, min(int(top  + ry2 * form_h), h - 1))
            if x2 > x1 and y2 > y1:
                crops[name] = image[y1:y2, x1:x2]
        return crops

    def visualize(self, image, output_path=None):
        """Draw detected boundary + field boxes. Returns annotated BGR image."""
        image = self._to_bgr(image)
        vis   = image.copy()
        h, w  = vis.shape[:2]
        self.extract(image)
        left, top, right, bottom = self._last_bounds
        form_w = right - left
        form_h = bottom - top
        cv2.rectangle(vis, (left, top), (right, bottom), (0, 140, 255), 3)
        cv2.putText(vis, "DETECTED FORM BOUNDARY",
                    (left, max(0, top - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)
        for idx, (name, (rx1, ry1, rx2, ry2)) in enumerate(self.field_map.items()):
            x1 = max(0, min(int(left + rx1 * form_w), w - 1))
            y1 = max(0, min(int(top  + ry1 * form_h), h - 1))
            x2 = max(0, min(int(left + rx2 * form_w), w - 1))
            y2 = max(0, min(int(top  + ry2 * form_h), h - 1))
            c  = COLOURS[idx % len(COLOURS)]
            cv2.rectangle(vis, (x1, y1), (x2, y2), c, 2)
            cv2.putText(vis, name[:22], (x1 + 2, max(0, y1 - 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, c, 1)
        if output_path:
            cv2.imwrite(str(output_path), vis)
            print(f"  Field map saved -> {output_path}")
        return vis


# ══════════════════════════════════════════════════════════════════════════════
#  FIELD NORMALIZER — prepares a BGR crop for CRNN inference
# ══════════════════════════════════════════════════════════════════════════════

class FieldNormalizer:
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
        return gray[y_min:y_max + 1, x_min:x_max + 1]

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
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return canvas

    def _binarize(self, img):
        _, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        white_ratio = np.mean(otsu == 255)
        if white_ratio < 0.30 or white_ratio > 0.97:
            return cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2)
        return otsu

    def normalize(self, crop) -> np.ndarray:
        """Accept BGR numpy array or PIL image, return normalized binary array."""
        try:
            from PIL import Image as PILImage
            if isinstance(crop, PILImage.Image):
                crop = cv2.cvtColor(np.array(crop.convert("RGB")), cv2.COLOR_RGB2BGR)
        except ImportError:
            pass
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        gray = self._crop_to_text(gray)
        gray = self._smart_resize(gray)
        return self._binarize(gray)

    def to_tensor(self, img: np.ndarray) -> torch.Tensor:
        return torch.FloatTensor(
            img.astype(np.float32) / 255.0
        ).unsqueeze(0).unsqueeze(0)


# ══════════════════════════════════════════════════════════════════════════════
#  CRNN MODEL LOADER
# ══════════════════════════════════════════════════════════════════════════════

def load_crnn_model(checkpoint_path: str, device: torch.device):
    sys.path.insert(0, str(Path(__file__).parent))
    from crnn_model import get_crnn_model

    print(f"  Loading CRNN model from: {checkpoint_path}")
    c           = torch.load(checkpoint_path, map_location=device, weights_only=False)
    config      = c.get("config", {})
    idx_to_char = c["idx_to_char"]
    num_chars   = c["model_state_dict"]["fc.weight"].shape[0]

    model = get_crnn_model(
        model_type=config.get("model_type", "standard"),
        img_height=config.get("img_height", 64),
        num_chars=num_chars,
        hidden_size=config.get("hidden_size", 128),
        num_lstm_layers=config.get("num_lstm_layers", 1),
    ).to(device)
    model.load_state_dict(c["model_state_dict"])
    model.eval()

    val_cer  = c.get("val_cer",  None)
    val_loss = c.get("val_loss", None)
    metric   = f"val_cer={val_cer:.2f}%" if val_cer else \
               f"val_loss={val_loss:.4f}" if val_loss else "no metric"
    print(f"  Model loaded  |  {metric}  |  chars={num_chars}")
    return model, idx_to_char, config.get("img_height", 64), config.get("img_width", 512)


# ══════════════════════════════════════════════════════════════════════════════
#  GREEDY CTC DECODE
# ══════════════════════════════════════════════════════════════════════════════

def greedy_decode(outputs: torch.Tensor, idx_to_char: dict) -> str:
    pred_indices = torch.argmax(outputs, dim=2).permute(1, 0)
    chars, prev  = [], -1
    for idx in pred_indices[0]:
        idx = idx.item()
        if idx != 0 and idx != prev and idx in idx_to_char:
            chars.append(idx_to_char[idx])
        prev = idx
    return "".join(chars)


# ══════════════════════════════════════════════════════════════════════════════
#  PDF → PIL IMAGE
# ══════════════════════════════════════════════════════════════════════════════

def pdf_to_image(pdf_path: str, dpi: int = 200):
    from pdf2image import convert_from_path
    kwargs = {"dpi": dpi, "first_page": 1, "last_page": 1}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    return convert_from_path(pdf_path, **kwargs)[0]


# ══════════════════════════════════════════════════════════════════════════════
#  CRNN OCR — runs on extracted field crops
# ══════════════════════════════════════════════════════════════════════════════

def run_crnn_ocr(crops: dict, model, idx_to_char: dict,
                 img_h: int, img_w: int, device: torch.device) -> dict:
    normalizer = FieldNormalizer(target_height=img_h, target_width=img_w)
    results    = {}
    with torch.no_grad():
        for name, crop in crops.items():
            try:
                norm   = normalizer.normalize(crop)
                tensor = normalizer.to_tensor(norm).to(device)
                text   = greedy_decode(model(tensor).cpu(), idx_to_char)
                results[name] = text
            except Exception as e:
                results[name] = f"[ERROR: {e}]"
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  CONVENIENCE WRAPPER — for other scripts that import this module
# ══════════════════════════════════════════════════════════════════════════════

def extract_field_images_dynamic(image, form_type="birth", verbose=False):
    """Extract field crops using dynamic boundary detection.
    Accepts PIL Image or BGR numpy array.
    Returns {field_name: BGR numpy array}."""
    return DynamicFieldExtractor(form_type=form_type, verbose=verbose).extract(image)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PH Civil Registry Field Extractor — Dynamic CRNN OCR")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf",   help="Path to scanned PDF")
    group.add_argument("--image", help="Path to scanned image (JPG/PNG)")
    parser.add_argument("--form",       required=True,
                        choices=["birth", "death", "marriage", "marriage_license"])
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--visualize",  action="store_true",
                        help="Save annotated field-map image")
    parser.add_argument("--output",     default=None,
                        help="Save extracted fields to JSON")
    parser.add_argument("--poppler",    default=None,
                        help="Override Poppler bin path (overrides .env)")
    parser.add_argument("--dpi",        type=int, default=200)
    parser.add_argument("--verbose",    action="store_true")
    args = parser.parse_args()

    global POPPLER_PATH
    if args.poppler:
        POPPLER_PATH = args.poppler

    form_labels = {
        "birth":            "Form 102 — Certificate of Live Birth",
        "death":            "Form 103 — Certificate of Death",
        "marriage":         "Form 97  — Certificate of Marriage",
        "marriage_license": "Form 90  — Application for Marriage License",
    }
    input_file = args.pdf or args.image

    print("\nPhilippine Civil Registry OCR — Dynamic Field Extractor")
    print("=" * 65)
    print(f"  Form       : {form_labels[args.form]}")
    print(f"  File       : {input_file}")
    print(f"  Checkpoint : {args.checkpoint}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device     : {device}\n")

    if not os.path.exists(args.checkpoint):
        print(f"ERROR: Checkpoint not found: {args.checkpoint}")
        sys.exit(1)

    model, idx_to_char, img_h, img_w = load_crnn_model(args.checkpoint, device)

    # Load image
    if args.pdf:
        print(f"  Converting PDF to image at {args.dpi} DPI...")
        try:
            pil_img    = pdf_to_image(args.pdf, dpi=args.dpi)
            page_image = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"\nERROR converting PDF: {e}")
            print("Fix: add POPPLER_PATH=C:\\...\\poppler\\Library\\bin to your .env file")
            sys.exit(1)
    else:
        page_image = cv2.imread(args.image)
        if page_image is None:
            print(f"ERROR: Could not load image: {args.image}")
            sys.exit(1)

    h, w = page_image.shape[:2]
    print(f"  Page size  : {w} x {h} px")

    extractor = DynamicFieldExtractor(form_type=args.form, verbose=args.verbose)

    if args.visualize:
        stem     = Path(input_file).stem
        out_path = stem + "_field_map.jpg"
        extractor.visualize(page_image, output_path=out_path)
        print(f"  Field map saved -> {out_path}")

    print(f"\n  Detecting form boundary and extracting fields...")
    crops = extractor.extract(page_image)
    print(f"  {len(crops)} field crops extracted")

    print(f"\n  Running CRNN OCR on {len(crops)} fields...")
    results = run_crnn_ocr(crops, model, idx_to_char, img_h, img_w, device)

    print(f"\n{'─'*65}")
    print(f"  {'FIELD':<42} TEXT")
    print(f"{'─'*65}")
    for name, text in results.items():
        print(f"  {name:<42} {text if text.strip() else '(empty)'}")
    print(f"{'─'*65}")
    print(f"\n  Fields recognized : {sum(1 for t in results.values() if t.strip())} / {len(results)}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"form": form_labels[args.form], "file": input_file,
                       "fields": results}, f, ensure_ascii=False, indent=2)
        print(f"\n  Results saved -> {args.output}")
    print()


if __name__ == "__main__":
    main()