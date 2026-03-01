"""
Philippine Civil Registry Field Extractor
Extracts fields from Forms 97, 102, 103 using relative coordinate ratios.
Coordinates measured precisely from grid-annotated field maps.
"""

import argparse
import os
import sys
import json
from pathlib import Path

# ─────────────────────────────────────────────
#  POPPLER PATH — adjust if needed
# ─────────────────────────────────────────────
POPPLER_PATH = r"C:\Users\irish\OneDrive\Desktop\poppler-25.12.0\Library\bin"

# ─────────────────────────────────────────────
#  FIELD COORDINATE MAPS
#  Format: field_name: (x1, y1, x2, y2)  — all values 0.0–1.0
#  Measured directly from grid-annotated field_map images
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════
#  FORM 102 — CERTIFICATE OF LIVE BIRTH
#  PDF page: 1700 × 2800 px  |  Field map: 1214 × 2000 px
# ══════════════════════════════════════════════════════════════
BIRTH_FIELDS = {
    # PDF actual size: 1275 x 2100 px
    # ── Header ─────────────────────────────────────────────────
    # province blank: row just below "province" label
    "province":             (0.038, 0.074, 0.495, 0.086),
    "registry_no":          (0.618, 0.074, 0.963, 0.086),
    "city_municipality":    (0.038, 0.088, 0.580, 0.100),

    # ── 1. Child name — blank row below "1. NAME" label ────────
    "child_first_name":     (0.082, 0.109, 0.435, 0.121),
    "child_middle_name":    (0.435, 0.109, 0.682, 0.121),
    "child_last_name":      (0.682, 0.109, 0.963, 0.121),

    # ── 2. Sex / 3. Date of Birth — blank cells ────────────────
    "sex":                  (0.038, 0.136, 0.082, 0.148),
    "dob_day":              (0.192, 0.136, 0.328, 0.148),
    "dob_month":            (0.328, 0.136, 0.492, 0.148),
    "dob_year":             (0.492, 0.136, 0.628, 0.148),

    # ── 4. Place of Birth ──────────────────────────────────────
    "place_birth_hospital": (0.082, 0.150, 0.388, 0.163),
    "place_birth_city":     (0.388, 0.150, 0.622, 0.163),
    "place_birth_province": (0.622, 0.150, 0.820, 0.163),
    "weight_at_birth":      (0.820, 0.150, 0.963, 0.163),

    # ── 5a/5b/5c. Type / Multiple / Order ─────────────────────
    "type_of_birth":        (0.082, 0.166, 0.270, 0.178),
    "multiple_birth_order": (0.270, 0.166, 0.492, 0.178),
    "birth_order":          (0.492, 0.166, 0.700, 0.178),
    "birth_weight_grams":   (0.820, 0.178, 0.963, 0.192),

    # ── 7. Mother Maiden Name ──────────────────────────────────
    "mother_first_name":    (0.082, 0.215, 0.390, 0.228),
    "mother_middle_name":   (0.390, 0.215, 0.635, 0.228),
    "mother_last_name":     (0.635, 0.215, 0.963, 0.228),

    # ── 8. Citizenship / 9. Religion / 11. Occupation ──────────
    "mother_citizenship":   (0.038, 0.232, 0.082, 0.244),
    "mother_religion":      (0.082, 0.232, 0.390, 0.244),
    "mother_occupation":    (0.492, 0.232, 0.700, 0.244),
    "mother_age_at_birth":  (0.820, 0.232, 0.963, 0.244),

    # ── 10a/10b/10c. Children stats ───────────────────────────
    "mother_children_alive":        (0.082, 0.258, 0.212, 0.270),
    "mother_children_still_living": (0.212, 0.258, 0.362, 0.270),
    "mother_children_born_dead":    (0.362, 0.258, 0.492, 0.270),

    # ── 13. Mother Residence ──────────────────────────────────
    "mother_residence_house":    (0.082, 0.330, 0.262, 0.342),
    "mother_residence_city":     (0.388, 0.330, 0.632, 0.342),
    "mother_residence_province": (0.632, 0.330, 0.820, 0.342),
    "mother_residence_country":  (0.820, 0.330, 0.963, 0.342),

    # ── 14. Father Name ───────────────────────────────────────
    "father_first_name":    (0.082, 0.356, 0.390, 0.368),
    "father_middle_name":   (0.390, 0.356, 0.635, 0.368),
    "father_last_name":     (0.635, 0.356, 0.963, 0.368),

    # ── 15/16/17. Father Citizenship / Religion / Occupation ──
    "father_citizenship":   (0.038, 0.380, 0.082, 0.392),
    "father_religion":      (0.082, 0.380, 0.390, 0.392),
    "father_occupation":    (0.492, 0.380, 0.700, 0.392),
    "father_age_at_birth":  (0.820, 0.380, 0.963, 0.392),

    # ── 19. Father Residence ──────────────────────────────────
    "father_residence_house":    (0.082, 0.406, 0.262, 0.418),
    "father_residence_city":     (0.388, 0.406, 0.632, 0.418),
    "father_residence_province": (0.632, 0.406, 0.820, 0.418),
    "father_residence_country":  (0.820, 0.406, 0.963, 0.418),

    # ── 20a. Marriage of Parents ──────────────────────────────
    "parents_marriage_month":    (0.082, 0.442, 0.198, 0.454),
    "parents_marriage_day":      (0.198, 0.442, 0.270, 0.454),
    "parents_marriage_year":     (0.270, 0.442, 0.355, 0.454),
    "parents_marriage_city":     (0.355, 0.442, 0.555, 0.454),
    "parents_marriage_province": (0.555, 0.442, 0.750, 0.454),
    "parents_marriage_country":  (0.750, 0.442, 0.963, 0.454),

    # ── 22. Informant ─────────────────────────────────────────
    "informant_name":         (0.082, 0.634, 0.390, 0.646),
    "informant_relationship": (0.082, 0.648, 0.390, 0.660),
    "informant_address":      (0.082, 0.662, 0.390, 0.674),
    "informant_date":         (0.082, 0.676, 0.390, 0.686),
}


# ══════════════════════════════════════════════════════════════
#  FORM 103 — CERTIFICATE OF DEATH
#  PDF page: 1700 × 2878 px  |  Field map: 1181 × 2000 px
# ══════════════════════════════════════════════════════════════
DEATH_FIELDS = {
    # PDF actual size: 1275 x 2159 px
    # ── Header ─────────────────────────────────────────────────
    "province":          (0.038, 0.108, 0.328, 0.120),
    "registry_no":       (0.355, 0.108, 0.560, 0.120),
    "city_municipality": (0.038, 0.122, 0.328, 0.134),

    # ── 1. Name ───────────────────────────────────────────────
    "deceased_first_name":  (0.095, 0.146, 0.310, 0.158),
    "deceased_middle_name": (0.310, 0.146, 0.545, 0.158),
    "deceased_last_name":   (0.545, 0.146, 0.760, 0.158),

    # ── 2. Sex / 3. Religion / 4. Age ─────────────────────────
    "sex":        (0.038, 0.172, 0.090, 0.210),
    "religion":   (0.090, 0.172, 0.215, 0.196),
    "age_years":  (0.248, 0.182, 0.335, 0.196),
    "age_months": (0.380, 0.182, 0.455, 0.196),
    "age_days":   (0.455, 0.182, 0.528, 0.196),

    # ── 5. Place of Death ─────────────────────────────────────
    "place_death_hospital": (0.085, 0.206, 0.368, 0.220),
    "place_death_city":     (0.368, 0.206, 0.568, 0.220),
    "place_death_province": (0.568, 0.206, 0.760, 0.220),

    # ── 6. Date of Death / 7. Citizenship ─────────────────────
    "dod_day":     (0.085, 0.232, 0.175, 0.246),
    "dod_month":   (0.175, 0.232, 0.278, 0.246),
    "dod_year":    (0.278, 0.232, 0.368, 0.246),
    "citizenship": (0.368, 0.232, 0.760, 0.246),

    # ── 8. Residence ──────────────────────────────────────────
    "residence_house":    (0.085, 0.260, 0.262, 0.274),
    "residence_city":     (0.262, 0.260, 0.472, 0.274),
    "residence_province": (0.472, 0.260, 0.668, 0.274),

    # ── 9. Civil Status / 10. Occupation ──────────────────────
    "civil_status": (0.038, 0.288, 0.290, 0.328),
    "occupation":   (0.368, 0.288, 0.668, 0.328),

    # ── 17. Causes of Death ───────────────────────────────────
    "cause_immediate":  (0.150, 0.392, 0.580, 0.406),
    "cause_antecedent": (0.150, 0.418, 0.580, 0.432),
    "cause_underlying": (0.150, 0.444, 0.580, 0.458),
    "cause_other":      (0.085, 0.468, 0.668, 0.482),

    # ── 25. Informant ─────────────────────────────────────────
    "informant_name":    (0.085, 0.800, 0.368, 0.814),
    "informant_address": (0.368, 0.800, 0.668, 0.814),
    "informant_date":    (0.085, 0.826, 0.250, 0.838),
}


# ══════════════════════════════════════════════════════════════
#  FORM 97 — CERTIFICATE OF MARRIAGE
#  PDF page: ~1700 × 2800 px  |  Field map: 1307 × 2000 px
#  LEFT column = HUSBAND (x: 0.100–0.490)
#  RIGHT column = WIFE    (x: 0.490–0.970)
# ══════════════════════════════════════════════════════════════
MARRIAGE_FIELDS = {
    # ── Header  — blank cells below labels ───────────────────
    "province":          (0.100, 0.058, 0.490, 0.068),
    "city_municipality": (0.100, 0.070, 0.490, 0.080),
    "registry_no":       (0.688, 0.058, 0.963, 0.072),

    # ── 1. Names — blank rows ─────────────────────────────────
    "husband_first_name":  (0.100, 0.108, 0.490, 0.120),
    "wife_first_name":     (0.510, 0.108, 0.963, 0.120),
    "husband_middle_name": (0.100, 0.130, 0.490, 0.142),
    "wife_middle_name":    (0.510, 0.130, 0.963, 0.142),
    "husband_last_name":   (0.100, 0.152, 0.490, 0.164),
    "wife_last_name":      (0.510, 0.152, 0.963, 0.164),

    # ── 2a/2b. Date of Birth / Age ────────────────────────────
    "husband_dob_day":   (0.100, 0.174, 0.175, 0.188),
    "husband_dob_month": (0.175, 0.174, 0.268, 0.188),
    "husband_dob_year":  (0.268, 0.174, 0.362, 0.188),
    "husband_age":       (0.362, 0.174, 0.490, 0.188),
    "wife_dob_day":      (0.510, 0.174, 0.590, 0.188),
    "wife_dob_month":    (0.590, 0.174, 0.678, 0.188),
    "wife_dob_year":     (0.678, 0.174, 0.778, 0.188),
    "wife_age":          (0.778, 0.174, 0.963, 0.188),

    # ── 3. Place of Birth ─────────────────────────────────────
    "husband_place_birth":          (0.100, 0.200, 0.212, 0.214),
    "husband_place_birth_city":     (0.212, 0.200, 0.362, 0.214),
    "husband_place_birth_province": (0.362, 0.200, 0.424, 0.214),
    "husband_place_birth_country":  (0.424, 0.200, 0.490, 0.214),
    "wife_place_birth":             (0.510, 0.200, 0.590, 0.214),
    "wife_place_birth_city":        (0.590, 0.200, 0.752, 0.214),
    "wife_place_birth_province":    (0.752, 0.200, 0.862, 0.214),
    "wife_place_birth_country":     (0.862, 0.200, 0.963, 0.214),

    # ── 4a/4b. Sex / Citizenship ──────────────────────────────
    "husband_sex":         (0.100, 0.226, 0.150, 0.238),
    "husband_citizenship": (0.150, 0.226, 0.490, 0.238),
    "wife_sex":            (0.510, 0.226, 0.560, 0.238),
    "wife_citizenship":    (0.560, 0.226, 0.963, 0.238),

    # ── 5. Residence ──────────────────────────────────────────
    "husband_residence": (0.100, 0.252, 0.490, 0.282),
    "wife_residence":    (0.510, 0.252, 0.963, 0.282),

    # ── 6. Religion ───────────────────────────────────────────
    "husband_religion": (0.100, 0.298, 0.490, 0.312),
    "wife_religion":    (0.510, 0.298, 0.963, 0.312),

    # ── 7. Civil Status ───────────────────────────────────────
    "husband_civil_status": (0.100, 0.326, 0.490, 0.338),
    "wife_civil_status":    (0.510, 0.326, 0.963, 0.338),

    # ── 8. Name of Father ─────────────────────────────────────
    "husband_father_first":  (0.100, 0.352, 0.242, 0.366),
    "husband_father_middle": (0.242, 0.352, 0.362, 0.366),
    "husband_father_last":   (0.362, 0.352, 0.490, 0.366),
    "wife_father_first":     (0.510, 0.352, 0.640, 0.366),
    "wife_father_middle":    (0.640, 0.352, 0.778, 0.366),
    "wife_father_last":      (0.778, 0.352, 0.963, 0.366),

    # ── 9. Father Citizenship ─────────────────────────────────
    "husband_father_citizenship": (0.100, 0.378, 0.490, 0.390),
    "wife_father_citizenship":    (0.510, 0.378, 0.963, 0.390),

    # ── 10. Name of Mother ────────────────────────────────────
    "husband_mother_first":  (0.100, 0.404, 0.222, 0.416),
    "husband_mother_middle": (0.222, 0.404, 0.350, 0.416),
    "husband_mother_last":   (0.350, 0.404, 0.490, 0.416),
    "wife_mother_first":     (0.510, 0.404, 0.635, 0.416),
    "wife_mother_middle":    (0.635, 0.404, 0.778, 0.416),
    "wife_mother_last":      (0.778, 0.404, 0.963, 0.416),

    # ── 11. Mother Citizenship ────────────────────────────────
    "husband_mother_citizenship": (0.100, 0.428, 0.490, 0.440),
    "wife_mother_citizenship":    (0.510, 0.428, 0.963, 0.440),

    # ── 12. Consent Giver ─────────────────────────────────────
    "husband_consent_first":  (0.100, 0.452, 0.228, 0.466),
    "husband_consent_middle": (0.228, 0.452, 0.355, 0.466),
    "husband_consent_last":   (0.355, 0.452, 0.490, 0.466),
    "wife_consent_first":     (0.510, 0.452, 0.630, 0.466),
    "wife_consent_middle":    (0.630, 0.452, 0.778, 0.466),
    "wife_consent_last":      (0.778, 0.452, 0.963, 0.466),

    # ── 13. Relationship ──────────────────────────────────────
    "husband_relationship": (0.100, 0.480, 0.490, 0.492),
    "wife_relationship":    (0.510, 0.480, 0.963, 0.492),

    # ── 13. Residence of consent giver ────────────────────────
    "husband_residence2": (0.100, 0.502, 0.490, 0.514),
    "wife_residence2":    (0.510, 0.502, 0.963, 0.514),

    # ── 14. Residence ─────────────────────────────────────────
    "husband_residence14": (0.100, 0.524, 0.490, 0.562),
    "wife_residence14":    (0.510, 0.524, 0.963, 0.562),

    # ── 15. Place of Marriage ─────────────────────────────────
    "place_marriage_office":   (0.100, 0.582, 0.490, 0.594),
    "place_marriage_city":     (0.490, 0.582, 0.748, 0.594),
    "place_marriage_province": (0.748, 0.582, 0.963, 0.594),
    "place_marriage_venue":    (0.100, 0.596, 0.490, 0.608),

    # ── 16/17. Date / Time of Marriage ───────────────────────
    "date_marriage_day":   (0.100, 0.622, 0.178, 0.634),
    "date_marriage_month": (0.178, 0.622, 0.310, 0.634),
    "date_marriage_year":  (0.310, 0.622, 0.412, 0.634),
    "time_marriage":       (0.650, 0.614, 0.963, 0.628),
}


# ─────────────────────────────────────────────
#  COLOUR PALETTE — one colour per form
# ─────────────────────────────────────────────
COLOURS = [
    (255, 100, 100, 80),   # red
    (100, 200, 100, 80),   # green
    (100, 100, 255, 80),   # blue
    (255, 200,   0, 80),   # yellow
    (200,   0, 200, 80),   # magenta
    (  0, 200, 200, 80),   # cyan
    (255, 140,   0, 80),   # orange
    (150,  50, 200, 80),   # purple
    (  0, 160,  80, 80),   # dark green
    (220,  20,  60, 80),   # crimson
    ( 30, 144, 255, 80),   # dodger blue
    (255,  20, 147, 80),   # deep pink
]


def pdf_to_image(pdf_path: str, dpi: int = 150):
    """Convert first page of PDF to PIL Image."""
    from pdf2image import convert_from_path
    kwargs = {"dpi": dpi, "first_page": 1, "last_page": 1}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    pages = convert_from_path(pdf_path, **kwargs)
    return pages[0]


def draw_fields(image, fields: dict, label_font_size: int = 14):
    """Draw semi-transparent boxes + labels for every field."""
    from PIL import Image as PILImage, ImageDraw, ImageFont
    overlay = PILImage.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = image.size

    try:
        font = ImageFont.truetype("arial.ttf", label_font_size)
    except Exception:
        font = ImageFont.load_default()

    for idx, (name, (x1, y1, x2, y2)) in enumerate(fields.items()):
        px1 = int(x1 * w)
        py1 = int(y1 * h)
        px2 = int(x2 * w)
        py2 = int(y2 * h)
        colour = COLOURS[idx % len(COLOURS)]
        draw.rectangle([px1, py1, px2, py2], fill=colour, outline=colour[:3] + (200,), width=2)
        draw.text((px1 + 2, py1 + 1), name, fill=(0, 0, 0, 230), font=font)

    return PILImage.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def extract_field_images(image, fields: dict):
    """Return a dict of field_name → cropped PIL Image."""
    w, h = image.size
    crops = {}
    for name, (x1, y1, x2, y2) in fields.items():
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        if px2 > px1 and py2 > py1:
            crops[name] = image.crop((px1, py1, px2, py2))
    return crops


def run_ocr(crops: dict, ocr_engine="tesseract"):
    """Run OCR on each cropped field image. Returns dict of field → text."""
    results = {}
    if ocr_engine == "tesseract":
        try:
            import pytesseract
            for name, img in crops.items():
                text = pytesseract.image_to_string(img, config="--psm 7").strip()
                results[name] = text
        except ImportError:
            print("  ⚠  pytesseract not installed — skipping OCR.")
    return results


def main():
    parser = argparse.ArgumentParser(description="PH Civil Registry Field Extractor")
    parser.add_argument("--pdf",       required=True,  help="Path to the PDF file")
    parser.add_argument("--form",      required=True,  choices=["birth", "death", "marriage"])
    parser.add_argument("--visualize", action="store_true", help="Save field map image")
    parser.add_argument("--ocr",       action="store_true", help="Run OCR on each field")
    parser.add_argument("--output",    default=None,   help="Output JSON file (optional)")
    parser.add_argument("--poppler",   default=None,   help="Override Poppler bin path")
    parser.add_argument("--dpi",       type=int, default=150)
    args = parser.parse_args()

    global POPPLER_PATH
    if args.poppler:
        POPPLER_PATH = args.poppler

    form_map = {
        "birth":    ("Form 102 — Certificate of Live Birth",    BIRTH_FIELDS),
        "death":    ("Form 103 — Certificate of Death",         DEATH_FIELDS),
        "marriage": ("Form 97 — Certificate of Marriage",       MARRIAGE_FIELDS),
    }
    form_label, fields = form_map[args.form]

    print("\nPhilippine Civil Registry OCR")
    print("=" * 60)
    print(f"  Form  : {form_label}")
    print(f"  File  : {args.pdf}")

    # Convert PDF
    print("  Converting PDF to image...")
    try:
        image = pdf_to_image(args.pdf, dpi=args.dpi)
    except Exception as e:
        print(f"ERROR converting PDF: {e}")
        print("""
If you see 'Unable to get page count' or 'pdftoppm not found':
  1. Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases
  2. Extract and set POPPLER_PATH at the top of this script.
     Example: POPPLER_PATH = r'C:\\Users\\irish\\Desktop\\poppler-24.08.0\\Library\\bin'
""")
        sys.exit(1)

    print(f"  Page size: {image.width}×{image.height} px")

    # Visualise
    if args.visualize:
        vis = draw_fields(image, fields)
        stem = Path(args.pdf).stem
        out_jpg = f"{stem}_field_map.jpg"
        vis.save(out_jpg, quality=90)
        print(f"  ✓ Field map saved → {out_jpg}")
        print("    Open this image to verify boxes are over the correct fields.")
        print("    If any box is wrong, adjust the ratio values in the script.")

    # OCR
    if args.ocr:
        print("  Running OCR …")
        crops   = extract_field_images(image, fields)
        results = run_ocr(crops)
        print("\n  Extracted fields:")
        for name, text in results.items():
            print(f"    {name:40s} → {text!r}")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n  ✓ Results saved → {args.output}")

    print()


if __name__ == "__main__":
    main()