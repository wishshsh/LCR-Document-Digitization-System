"""
generate_form_samples.py
========================
Generates thousands of synthetic filled civil registry form images
using the blank PDF forms + template_matcher.py coordinates.

Each form is filled with random Filipino names/dates in handwriting fonts.
Crops are saved with labels → ready for CRNN+CTC fine-tuning.

Usage:
    python generate_form_samples.py

Output:
    data/train/real_forms/  -- cropped field images
    data/real_annotations.json  -- labels for fine-tuning
"""

import os
import sys
import json
import random
import datetime

from PIL import Image, ImageDraw, ImageFont

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(BASE_DIR)
PYTHON_DIR = ROOT_DIR  # template_matcher.py is here

NAMES_FILE  = os.path.join(BASE_DIR, 'data', 'ph_names.json')
OUT_IMG_DIR = os.path.join(BASE_DIR, 'data', 'train', 'real_forms')
OUT_ANN     = os.path.join(BASE_DIR, 'data', 'real_annotations.json')

FONTS_DIR = os.path.join(ROOT_DIR, 'test_images', 'handwriting_fonts')

# Only verified-working Google Fonts URLs
GOOGLE_FONTS = {
    'Kalam-Regular.ttf':          'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf',
    'Kalam-Bold.ttf':             'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Bold.ttf',
    'Kalam-Light.ttf':            'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Light.ttf',
    'PatrickHand-Regular.ttf':    'https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf',
    'IndieFlower-Regular.ttf':    'https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower-Regular.ttf',
    'Handlee-Regular.ttf':        'https://github.com/google/fonts/raw/main/ofl/handlee/Handlee-Regular.ttf',
    'GochiHand-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/gochihand/GochiHand-Regular.ttf',
    'ArchitectsDaughter.ttf':     'https://github.com/google/fonts/raw/main/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf',
    'ShadowsIntoLight.ttf':       'https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight.ttf',
    'ShadowsIntoLightTwo.ttf':    'https://github.com/google/fonts/raw/main/ofl/shadowsintolighttwo/ShadowsIntoLightTwo-Regular.ttf',
    'Kristi-Regular.ttf':         'https://github.com/google/fonts/raw/main/ofl/kristi/Kristi-Regular.ttf',
    'AmaticSC-Regular.ttf':       'https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Regular.ttf',
    'AmaticSC-Bold.ttf':          'https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Bold.ttf',
    'BadScript-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/badscript/BadScript-Regular.ttf',
    'Sacramento-Regular.ttf':     'https://github.com/google/fonts/raw/main/ofl/sacramento/Sacramento-Regular.ttf',
    'GreatVibes-Regular.ttf':     'https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf',
    'Allura-Regular.ttf':         'https://github.com/google/fonts/raw/main/ofl/allura/Allura-Regular.ttf',
    'AlexBrush-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/alexbrush/AlexBrush-Regular.ttf',
    'Parisienne-Regular.ttf':     'https://github.com/google/fonts/raw/main/ofl/parisienne/Parisienne-Regular.ttf',
    'Tangerine-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/tangerine/Tangerine-Regular.ttf',
    'Tangerine-Bold.ttf':         'https://github.com/google/fonts/raw/main/ofl/tangerine/Tangerine-Bold.ttf',
    'Courgette-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/courgette/Courgette-Regular.ttf',
    'Niconne-Regular.ttf':        'https://github.com/google/fonts/raw/main/ofl/niconne/Niconne-Regular.ttf',
    'MarckScript-Regular.ttf':    'https://github.com/google/fonts/raw/main/ofl/marckscript/MarckScript-Regular.ttf',
    'Norican-Regular.ttf':        'https://github.com/google/fonts/raw/main/ofl/norican/Norican-Regular.ttf',
    'Damion-Regular.ttf':         'https://github.com/google/fonts/raw/main/ofl/damion/Damion-Regular.ttf',
    'Satisfy-Regular.ttf':        'https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf',
    'Pacifico-Regular.ttf':       'https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf',
    'Italianno-Regular.ttf':      'https://github.com/google/fonts/raw/main/ofl/italianno/Italianno-Regular.ttf',
    'Pompiere-Regular.ttf':       'https://github.com/google/fonts/raw/main/ofl/pompiere/Pompiere-Regular.ttf',
}

FONT_PATHS = [
    # Downloaded handwriting fonts
    *[os.path.join(FONTS_DIR, name) for name in GOOGLE_FONTS],
    # Already available
    os.path.join(ROOT_DIR, 'test_images', 'Caveat-Regular.ttf'),
    # Windows fallbacks
    r'C:\Windows\Fonts\segoepr.ttf',
    r'C:\Windows\Fonts\segoeprb.ttf',
    r'C:\Windows\Fonts\comic.ttf',
]

def download_fonts():
    """Download handwriting fonts from Google Fonts if not present."""
    import urllib.request
    os.makedirs(FONTS_DIR, exist_ok=True)
    ok = 0
    for fname, url in GOOGLE_FONTS.items():
        dest = os.path.join(FONTS_DIR, fname)
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            ok += 1
            continue
        try:
            print(f"  Downloading {fname}...")
            with urllib.request.urlopen(url, timeout=10) as r, open(dest, 'wb') as f:
                f.write(r.read())
            # Validate: real TTF files are > 10KB
            if os.path.getsize(dest) < 10000:
                os.remove(dest)
                print(f"  Skipped {fname} (invalid file)")
            else:
                ok += 1
        except Exception as e:
            print(f"  Failed {fname}: {e}")
            if os.path.exists(dest):
                os.remove(dest)
    print(f"  {ok} fonts ready")

PDF_FORMS = {
    '97':  os.path.join(ROOT_DIR, 'python', 'CRNN+CTC', 'FORM 97 (MARRIAGE CERTIFICATE).pdf'),
    '102': os.path.join(ROOT_DIR, 'python', 'CRNN+CTC', 'FORM 102 (BIRTH CERTIFICATE).pdf'),
    '103': os.path.join(ROOT_DIR, 'python', 'CRNN+CTC', 'FORM 103 (DEATH CERTIFICATE).pdf'),
    '90':  os.path.join(ROOT_DIR, 'python', 'CRNN+CTC', 'FORM 90-MARRIAGE-LICENCE-FORM.pdf'),
}

SAMPLES_PER_FORM = 1000   # forms to generate per type
IMG_W = 64
IMG_H = 512

# ── Load TEMPLATES from template_matcher ─────────────────────
sys.path.insert(0, PYTHON_DIR)
from template_matcher import TEMPLATES

# ── Load Filipino names ───────────────────────────────────────
def load_names():
    if not os.path.exists(NAMES_FILE):
        print(f"ERROR: {NAMES_FILE} not found. Run generate_ph_names.py first.")
        sys.exit(1)
    with open(NAMES_FILE) as f:
        data = json.load(f)
    return data

# ── Random data generators ────────────────────────────────────
MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']
RELIGIONS = ['Roman Catholic','Islam','Baptist','Iglesia ni Cristo',
             'Seventh Day Adventist','Born Again Christian']
CIVIL_STATUSES = ['Single','Married','Widowed','Legally Separated']
CITIZENSHIPS = ['Filipino','American','Chinese','Japanese']
PROVINCES = ['Cebu','Davao del Sur','Metro Manila','Iloilo','Pampanga',
             'Batangas','Laguna','Cavite','Bulacan','Quezon City']
CITIES = ['Cebu City','Davao City','Manila','Iloilo City','San Fernando',
          'Batangas City','Santa Rosa','Bacoor','Malolos','Quezon City']

def rand_name(names, key):
    pool = names.get(key, ['Juan'])
    return random.choice(pool).upper()

def rand_date():
    y = random.randint(1950, 2005)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{d:02d}", MONTHS[m-1], str(y)

def rand_age():
    return str(random.randint(18, 80))

def rand_province():
    return random.choice(PROVINCES).upper()

def rand_city():
    return random.choice(CITIES).upper()

def rand_religion():
    return random.choice(RELIGIONS).upper()

def rand_civil_status():
    return random.choice(CIVIL_STATUSES).upper()

def rand_citizenship():
    return random.choice(CITIZENSHIPS).upper()

def rand_registry_no():
    return f"{random.randint(2000,2024)}-{random.randint(1000,9999)}"

def rand_time():
    h = random.randint(6, 18)
    m = random.choice(['00','15','30','45'])
    return f"{h:02d}:{m} {'AM' if h < 12 else 'PM'}"

def generate_field_value(field_name, names):
    """Generate a plausible random value for a given field name."""
    f = field_name.lower()
    if 'province' in f:          return rand_province()
    if 'registry' in f:          return rand_registry_no()
    if 'city' in f or 'municipality' in f: return rand_city()
    if 'first' in f and ('name' in f or 'father' in f or 'mother' in f):
        return rand_name(names, 'first')
    if 'middle' in f:            return rand_name(names, 'middle')
    if 'last' in f:              return rand_name(names, 'last')
    if '_name' in f and 'father' not in f and 'mother' not in f:
        return rand_name(names, 'first')
    if 'father_name' in f or 'mother_name' in f:
        return f"{rand_name(names,'first')} {rand_name(names,'middle')} {rand_name(names,'last')}"
    if 'dob_day' in f or 'day' in f:    return rand_date()[0]
    if 'dob_month' in f or 'month' in f: return rand_date()[1]
    if 'dob_year' in f or 'year' in f:   return rand_date()[2]
    if 'dob' in f and 'day' not in f and 'month' not in f and 'year' not in f:
        d,m,y = rand_date(); return f"{d} {m} {y}"
    if 'age' in f:               return rand_age()
    if 'birth' in f and 'place' in f: return rand_city()
    if 'place_of_birth' in f:    return rand_city()
    if 'sex' in f:               return random.choice(['MALE','FEMALE'])
    if 'citizenship' in f:       return rand_citizenship()
    if 'residence' in f:         return f"{rand_city()}, {rand_province()}"
    if 'religion' in f:          return rand_religion()
    if 'civil_status' in f:      return rand_civil_status()
    if 'place_of_marriage' in f: return rand_city()
    if 'date_of_marriage' in f:
        d,m,y = rand_date(); return f"{d} {m} {y}"
    if 'time_of_marriage' in f:  return rand_time()
    if 'marriage_date' in f:
        d,m,y = rand_date(); return f"{d} {m} {y}"
    if 'marriage_place' in f:    return rand_city()
    if 'marriage_license' in f:  return rand_registry_no()
    if 'date_issued' in f:
        d,m,y = rand_date(); return f"{d} {m} {y}"
    if 'occupation' in f:        return random.choice(['FARMER','TEACHER','NURSE','ENGINEER','DRIVER','HOUSEWIFE'])
    if 'type_of_birth' in f:     return random.choice(['SINGLE','TWIN','TRIPLET'])
    if 'birth_order' in f:       return random.choice(['1ST','2ND','3RD','4TH'])
    if 'weight' in f:            return f"{random.randint(2,5)}.{random.randint(0,9)} KG"
    if 'cause' in f:             return random.choice(['CARDIAC ARREST','PNEUMONIA','DIABETES','HYPERTENSION'])
    if 'father_name' in f:       return f"{rand_name(names,'first')} {rand_name(names,'last')}"
    if 'mother_name' in f:       return f"{rand_name(names,'first')} {rand_name(names,'last')}"
    return rand_name(names, 'first')

# ── Load fonts ────────────────────────────────────────────────
def load_fonts():
    fonts = []
    for path in FONT_PATHS:
        if os.path.exists(path):
            for size in [14, 16, 18, 20]:
                try:
                    fonts.append(ImageFont.truetype(path, size))
                except:
                    pass
    if not fonts:
        fonts = [ImageFont.load_default()]
    print(f"  Loaded {len(fonts)} font variants")
    return fonts

# ── Load blank form image ─────────────────────────────────────
def load_blank_form(form_type):
    """Convert PDF to image or use a reference scan as background."""
    pdf_path = PDF_FORMS.get(form_type)

    # Try pdf2image first
    if pdf_path and os.path.exists(pdf_path):
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(pdf_path, dpi=150)
            if pages:
                return pages[0].convert('RGB')
        except Exception as e:
            print(f"  pdf2image failed: {e}")

    # Fallback: use reference image (try png, jpg, jpeg)
    for ext in ['png', 'jpg', 'jpeg']:
        ref_path = os.path.join(ROOT_DIR, 'references', f'reference_{form_type}.{ext}')
        if os.path.exists(ref_path):
            return Image.open(ref_path).convert('RGB')
    # Also try hyphen variant (e.g. reference-90.jpg)
    for ext in ['png', 'jpg', 'jpeg']:
        ref_path = os.path.join(ROOT_DIR, 'references', f'reference-{form_type}.{ext}')
        if os.path.exists(ref_path):
            return Image.open(ref_path).convert('RGB')

    print(f"  WARNING: No blank form found for {form_type} — skipping")
    return None

# ── Render text on form ───────────────────────────────────────
def render_field(draw, x1r, y1r, x2r, y2r, text, img_w, img_h, fonts):
    """Draw handwritten-style text in a field box."""
    x1 = int(x1r * img_w)
    y1 = int(y1r * img_h)
    x2 = int(x2r * img_w)
    y2 = int(y2r * img_h)

    box_w = max(x2 - x1, 1)
    box_h = max(y2 - y1, 1)

    # Pick a font that fits
    font = random.choice(fonts)
    for f in fonts:
        bbox = f.getbbox(text)
        fw = bbox[2] - bbox[0]
        fh = bbox[3] - bbox[1]
        if fw <= box_w * 0.95 and fh <= box_h * 1.2:
            font = f
            break

    # Random pen color (dark blue/black like ballpen)
    r = random.randint(0, 40)
    g = random.randint(0, 40)
    b = random.randint(60, 120)
    color = (r, g, b)

    # Center text vertically in box
    bbox = font.getbbox(text)
    fh = bbox[3] - bbox[1]
    ty = y1 + (box_h - fh) // 2

    # Slight random x offset
    tx = x1 + random.randint(2, max(3, box_w // 10))

    draw.text((tx, ty), text, fill=color, font=font)

# ── Crop a field ──────────────────────────────────────────────
def crop_field(img, x1r, y1r, x2r, y2r):
    w, h = img.size
    x1 = max(0, int(x1r * w) - 4)
    y1 = max(0, int(y1r * h) - 4)
    x2 = min(w, int(x2r * w) + 4)
    y2 = min(h, int(y2r * h) + 4)
    return img.crop((x1, y1, x2, y2))

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Form Sample Generator")
    print("=" * 60)

    os.makedirs(OUT_IMG_DIR, exist_ok=True)
    print("\n  Downloading handwriting fonts...")
    download_fonts()
    names = load_names()
    fonts = load_fonts()
    annotations = []
    total = 0

    for form_type, template in TEMPLATES.items():
        print(f"\n  Generating Form {form_type}...")

        blank = load_blank_form(form_type)
        if blank is None:
            continue

        for i in range(SAMPLES_PER_FORM):
            # Fresh copy of blank form
            form_img = blank.copy()
            draw = ImageDraw.Draw(form_img)
            img_w, img_h = form_img.size

            field_values = {}
            for field_name, coords in template.items():
                x1r, y1r, x2r, y2r, _ = coords
                text = generate_field_value(field_name, names)
                field_values[field_name] = text
                render_field(draw, x1r, y1r, x2r, y2r, text, img_w, img_h, fonts)

            # Save full form preview (first sample only)
            if i == 0:
                preview_path = os.path.join(OUT_IMG_DIR, f'form{form_type}_preview.png')
                form_img.save(preview_path)
                print(f"    Preview saved: {preview_path}")

            # Crop each field and save
            for field_name, coords in template.items():
                x1r, y1r, x2r, y2r, _ = coords
                crop = crop_field(form_img, x1r, y1r, x2r, y2r)
                crop = crop.convert('L')  # grayscale

                fname = f"form{form_type}_{i:05d}_{field_name}.png"
                fpath = os.path.join(OUT_IMG_DIR, fname)
                crop.save(fpath)

                annotations.append({
                    "image_path": f"real_forms/{fname}",
                    "text": field_values[field_name]
                })
                total += 1

            if (i + 1) % 100 == 0:
                print(f"    {i+1}/{SAMPLES_PER_FORM} forms done ({total} crops so far)")

        print(f"  Form {form_type} done.")

    # Save annotations
    with open(OUT_ANN, 'w') as f:
        json.dump(annotations, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  Total crops : {total}")
    print(f"  Annotations : {OUT_ANN}")
    print(f"  Next step   : upload to Kaggle and run fine-tune")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
