"""
Philippine Civil Registry — Dynamic Field Extractor
=====================================================
Automatically aligns field boxes to ANY image size using border detection.
Only extracts fields needed for the output forms:
  Form 102 -> Form 1A (Birth Certificate)
  Form 103 -> Form 2A (Death Certificate)
  Form 97  -> Form 3A (Marriage Certificate)
  Birth Certs of Groom+Bride -> Form 90 (Marriage License)
"""

import cv2
import numpy as np
import argparse
from pathlib import Path

TESSERACT_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
#  FIELD RATIO MAPS — only fields needed for output forms
# ══════════════════════════════════════════════════════════════════════════════

# Form 102 -> Form 1A
BIRTH_FIELDS = {
    "registry_number":           (0.62, 0.096, 0.95, 0.114),
    "date_of_registration":      (0.62, 0.116, 0.95, 0.132),
    "child_first_name":          (0.14, 0.152, 0.42, 0.170),
    "child_middle_name":         (0.42, 0.152, 0.65, 0.170),
    "child_last_name":           (0.65, 0.152, 0.95, 0.170),
    "sex":                       (0.15, 0.178, 0.30, 0.196),
    "dob_day":                   (0.42, 0.178, 0.52, 0.196),
    "dob_month":                 (0.52, 0.178, 0.72, 0.196),
    "dob_year":                  (0.72, 0.178, 0.95, 0.196),
    "place_birth_hospital":      (0.22, 0.202, 0.50, 0.220),
    "place_birth_city":          (0.50, 0.202, 0.68, 0.220),
    "place_birth_province":      (0.68, 0.202, 0.88, 0.220),
    "mother_first_name":         (0.14, 0.308, 0.40, 0.326),
    "mother_middle_name":        (0.40, 0.308, 0.63, 0.326),
    "mother_last_name":          (0.63, 0.308, 0.95, 0.326),
    "nationality_of_mother":     (0.15, 0.332, 0.38, 0.350),
    "father_first_name":         (0.14, 0.462, 0.40, 0.480),
    "father_middle_name":        (0.40, 0.462, 0.63, 0.480),
    "father_last_name":          (0.63, 0.462, 0.95, 0.480),
    "nationality_of_father":     (0.15, 0.488, 0.33, 0.506),
    "parents_marriage_month":    (0.14, 0.580, 0.26, 0.596),
    "parents_marriage_day":      (0.26, 0.580, 0.36, 0.596),
    "parents_marriage_year":     (0.36, 0.580, 0.46, 0.596),
    "parents_marriage_city":     (0.52, 0.580, 0.68, 0.596),
    "parents_marriage_province": (0.68, 0.580, 0.82, 0.596),
}

# Form 103 -> Form 2A
DEATH_FIELDS = {
    "registry_number":           (0.58, 0.140, 0.78, 0.160),
    "date_of_registration":      (0.58, 0.160, 0.78, 0.178),
    "deceased_first_name":       (0.12, 0.188, 0.36, 0.206),
    "deceased_middle_name":      (0.36, 0.188, 0.58, 0.206),
    "deceased_last_name":        (0.58, 0.188, 0.78, 0.206),
    "sex":                       (0.08, 0.210, 0.18, 0.232),
    "age":                       (0.43, 0.210, 0.52, 0.232),
    "civil_status":              (0.04, 0.318, 0.32, 0.352),
    "nationality":               (0.62, 0.262, 0.78, 0.282),
    "dod_day":                   (0.20, 0.262, 0.30, 0.282),
    "dod_month":                 (0.30, 0.262, 0.46, 0.282),
    "dod_year":                  (0.46, 0.262, 0.60, 0.282),
    "place_death_hospital":      (0.22, 0.238, 0.48, 0.258),
    "place_death_city":          (0.48, 0.238, 0.63, 0.258),
    "place_death_province":      (0.63, 0.238, 0.78, 0.258),
    "cause_of_death":            (0.25, 0.422, 0.63, 0.494),
}

# Form 97 -> Form 3A
MARRIAGE_FIELDS = {
    "registry_number":            (0.60, 0.060, 0.90, 0.078),
    "date_of_registration":       (0.60, 0.078, 0.90, 0.096),
    "date_marriage_day":          (0.14, 0.643, 0.24, 0.662),
    "date_marriage_month":        (0.24, 0.643, 0.38, 0.662),
    "date_marriage_year":         (0.38, 0.643, 0.48, 0.662),
    "place_marriage_city":        (0.44, 0.620, 0.68, 0.642),
    "place_marriage_province":    (0.68, 0.620, 0.88, 0.642),
    "husband_first_name":         (0.14, 0.152, 0.42, 0.175),
    "husband_middle_name":        (0.14, 0.175, 0.42, 0.198),
    "husband_last_name":          (0.14, 0.198, 0.42, 0.220),
    "husband_age":                (0.40, 0.222, 0.48, 0.243),
    "husband_nationality":        (0.24, 0.268, 0.46, 0.288),
    "husband_father_first":       (0.14, 0.395, 0.26, 0.415),
    "husband_father_middle":      (0.26, 0.395, 0.37, 0.415),
    "husband_father_last":        (0.37, 0.395, 0.46, 0.415),
    "husband_father_nationality": (0.14, 0.415, 0.46, 0.435),
    "husband_mother_first":       (0.14, 0.440, 0.26, 0.460),
    "husband_mother_middle":      (0.26, 0.440, 0.37, 0.460),
    "husband_mother_last":        (0.37, 0.440, 0.46, 0.460),
    "husband_mother_nationality": (0.14, 0.460, 0.46, 0.480),
    "wife_first_name":            (0.55, 0.152, 0.82, 0.175),
    "wife_middle_name":           (0.55, 0.175, 0.82, 0.198),
    "wife_last_name":             (0.55, 0.198, 0.82, 0.220),
    "wife_age":                   (0.80, 0.222, 0.88, 0.243),
    "wife_nationality":           (0.64, 0.268, 0.82, 0.288),
    "wife_father_first":          (0.55, 0.395, 0.66, 0.415),
    "wife_father_middle":         (0.66, 0.395, 0.76, 0.415),
    "wife_father_last":           (0.76, 0.395, 0.88, 0.415),
    "wife_father_nationality":    (0.55, 0.415, 0.88, 0.435),
    "wife_mother_first":          (0.55, 0.440, 0.66, 0.460),
    "wife_mother_middle":         (0.66, 0.440, 0.76, 0.460),
    "wife_mother_last":           (0.76, 0.440, 0.88, 0.460),
    "wife_mother_nationality":    (0.55, 0.460, 0.88, 0.480),
}

# Birth cert of groom/bride -> Form 90
# Same Form 102 layout, run separately for groom and bride
MARRIAGE_LICENSE_FIELDS = {
    "first_name":            (0.14, 0.152, 0.42, 0.170),
    "middle_name":           (0.42, 0.152, 0.65, 0.170),
    "last_name":             (0.65, 0.152, 0.95, 0.170),
    "dob_day":               (0.42, 0.178, 0.52, 0.196),
    "dob_month":             (0.52, 0.178, 0.72, 0.196),
    "dob_year":              (0.72, 0.178, 0.95, 0.196),
    "place_birth_hospital":  (0.22, 0.202, 0.50, 0.220),
    "place_birth_city":      (0.50, 0.202, 0.68, 0.220),
    "place_birth_province":  (0.68, 0.202, 0.88, 0.220),
    "sex":                   (0.15, 0.178, 0.30, 0.196),
    "citizenship":           (0.15, 0.332, 0.38, 0.350),
    "father_first_name":     (0.14, 0.462, 0.40, 0.480),
    "father_middle_name":    (0.40, 0.462, 0.63, 0.480),
    "father_last_name":      (0.63, 0.462, 0.95, 0.480),
    "father_citizenship":    (0.15, 0.488, 0.33, 0.506),
    "mother_first_name":     (0.14, 0.308, 0.40, 0.326),
    "mother_middle_name":    (0.40, 0.308, 0.63, 0.326),
    "mother_last_name":      (0.63, 0.308, 0.95, 0.326),
    "mother_citizenship":    (0.15, 0.332, 0.38, 0.350),
}

FORM_FIELDS = {
    'birth':            BIRTH_FIELDS,
    'death':            DEATH_FIELDS,
    'marriage':         MARRIAGE_FIELDS,
    'marriage_license': MARRIAGE_LICENSE_FIELDS,
}


# ══════════════════════════════════════════════════════════════════════════════
#  FORM BOUNDS DETECTOR
# ══════════════════════════════════════════════════════════════════════════════

class FormBoundsDetector:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def detect(self, image_bgr):
        h, w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
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
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2)
            hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 5, 10), 1))
            h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hk)
            h_rows  = np.where(np.sum(h_lines, axis=1) > w * 0.15)[0]
            vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 5, 10)))
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
# ══════════════════════════════════════════════════════════════════════════════

class DynamicFieldExtractor:
    def __init__(self, form_type='birth', verbose=False):
        self.form_type    = form_type.lower()
        self.field_map    = FORM_FIELDS.get(self.form_type, BIRTH_FIELDS)
        self.detector     = FormBoundsDetector(verbose=verbose)
        self.verbose      = verbose
        self._last_bounds = None

    def extract(self, image):
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        h, w = image.shape[:2]
        left, top, right, bottom = self.detector.detect(image)
        self._last_bounds = (left, top, right, bottom)
        form_w = right - left
        form_h = bottom - top
        if self.verbose:
            print(f"  [Extract] Image={w}x{h}  Form={form_w}x{form_h} @ ({left},{top})-({right},{bottom})")
        crops = {}
        for field_name, (rx1, ry1, rx2, ry2) in self.field_map.items():
            x1 = max(0, min(int(left + rx1 * form_w), w - 1))
            y1 = max(0, min(int(top  + ry1 * form_h), h - 1))
            x2 = max(0, min(int(left + rx2 * form_w), w - 1))
            y2 = max(0, min(int(top  + ry2 * form_h), h - 1))
            if x2 > x1 and y2 > y1:
                crops[field_name] = image[y1:y2, x1:x2]
        return crops

    def visualize(self, image, output_path=None):
        if len(image.shape) == 2:
            vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            vis = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            vis = image.copy()
        h, w = vis.shape[:2]
        self.extract(image)
        left, top, right, bottom = self._last_bounds
        form_w = right - left
        form_h = bottom - top
        cv2.rectangle(vis, (left, top), (right, bottom), (255, 100, 0), 3)
        cv2.putText(vis, "DETECTED FORM BOUNDARY", (left, max(0, top - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)
        palette = [(0,200,0),(0,150,255),(200,0,200),(0,200,200),(200,200,0),(220,20,60)]
        for idx, (field_name, (rx1, ry1, rx2, ry2)) in enumerate(self.field_map.items()):
            x1 = max(0, min(int(left + rx1 * form_w), w - 1))
            y1 = max(0, min(int(top  + ry1 * form_h), h - 1))
            x2 = max(0, min(int(left + rx2 * form_w), w - 1))
            y2 = max(0, min(int(top  + ry2 * form_h), h - 1))
            color = palette[idx % len(palette)]
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 1)
            cv2.putText(vis, field_name[:22], (x1 + 2, max(0, y1 - 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1)
        if output_path:
            cv2.imwrite(str(output_path), vis)
            print(f"  Field map saved -> {output_path}")
        return vis


# ══════════════════════════════════════════════════════════════════════════════
#  DROP-IN REPLACEMENT
# ══════════════════════════════════════════════════════════════════════════════

def extract_field_images_dynamic(image, form_type='birth', verbose=False):
    try:
        from PIL import Image as PILImage
        if isinstance(image, PILImage.Image):
            image = np.array(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    except ImportError:
        pass
    return DynamicFieldExtractor(form_type=form_type, verbose=verbose).extract(image)


# ══════════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image',     required=True)
    parser.add_argument('--form',      default='birth',
                        choices=['birth','death','marriage','marriage_license'])
    parser.add_argument('--visualize', action='store_true')
    parser.add_argument('--verbose',   action='store_true')
    args = parser.parse_args()

    img_path = Path(args.image)
    if img_path.suffix.lower() == '.pdf':
        from pdf2image import convert_from_path
        import os
        poppler = os.environ.get('POPPLER_PATH', r'C:\Program Files\poppler-25.12.0\Library\bin')
        pages = convert_from_path(str(img_path), dpi=200, poppler_path=poppler)
        image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    else:
        image = cv2.imread(str(img_path))

    if image is None:
        print(f"ERROR: Could not load {img_path}")
        exit(1)

    print(f"Image: {image.shape[1]}x{image.shape[0]}px  Form: {args.form}")
    extractor = DynamicFieldExtractor(form_type=args.form, verbose=args.verbose)

    if args.visualize:
        out = str(img_path.stem) + '_dynamic_field_map.jpg'
        extractor.visualize(image, output_path=out)
    else:
        crops = extractor.extract(image)
        print(f"Extracted {len(crops)} fields:")
        for name, crop in crops.items():
            print(f"  {name:<35} {crop.shape[1]}x{crop.shape[0]}px")
