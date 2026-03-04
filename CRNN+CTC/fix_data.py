"""
fix_data.py
===========
Generates synthetic training images for the Civil Registry OCR system.

Run this ONCE before training to create your dataset.

STEP ORDER:
  1. python generate_ph_names.py   ← generates data/ph_names.json
  2. python fix_data.py            ← generates all training images  (THIS FILE)
  3. python train.py               ← trains the CRNN model

WHAT IT GENERATES:
  - Printed text images of names, dates, places, and other form fields
  - Covers all 4 form types: birth, death, marriage, marriage license
  - Splits into train (90%) and val (10%)
  - Writes data/train_annotations.json and data/val_annotations.json

OUTPUT STRUCTURE:
  data/
    train/
      form1a/   ← birth certificate fields
      form2a/   ← death certificate fields
      form3a/   ← marriage certificate fields
      form90/   ← marriage license fields
    val/
      form1a/
      form2a/
      form3a/
      form90/
    train_annotations.json
    val_annotations.json
"""

import os
import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

IMG_WIDTH      = 512
IMG_HEIGHT     = 64
FONT_SIZE      = 22
VAL_SPLIT      = 0.10        # 10% of images go to val
RANDOM_SEED    = 42

# How many images to generate per form type
SAMPLES_PER_FORM = {
    'form1a': 3000,   # birth certificate
    'form2a': 2000,   # death certificate
    'form3a': 2000,   # marriage certificate
    'form90': 1000,   # marriage license
}

PH_NAMES_FILE = 'data/ph_names.json'

random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────────────────────
#  FONT LOADER  (same as create_test_images.py)
# ─────────────────────────────────────────────────────────────────────────────

def load_font(size=FONT_SIZE):
    for fp in [
        'arial.ttf', 'Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibri.ttf',
    ]:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    print("WARNING: Could not load a TrueType font. Using default bitmap font.")
    print("         Prediction accuracy may be lower.")
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_text_image(text: str, font, width=IMG_WIDTH, height=IMG_HEIGHT,
                      noise=False) -> Image.Image:
    """
    Render text on a white background, centered.
    Optionally adds slight noise to simulate scan variation.
    """
    img  = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]

    x = max(4, (width  - tw) // 2)
    y = max(4, (height - th) // 2)

    # Slightly vary text color (dark gray to black) for realism
    shade = random.randint(0, 40)
    draw.text((x, y), text, fill=(shade, shade, shade), font=font)

    return img


# ─────────────────────────────────────────────────────────────────────────────
#  DATA POOLS  (Filipino-specific text samples)
# ─────────────────────────────────────────────────────────────────────────────

# Load Filipino names if available, else use built-in fallbacks
def load_ph_names():
    if os.path.exists(PH_NAMES_FILE):
        with open(PH_NAMES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        first_names = data['first_names']['all']
        last_names  = data['last_names']
        print(f"  Loaded ph_names.json: "
              f"{len(first_names)} first names, {len(last_names)} last names")
    else:
        print(f"  WARNING: {PH_NAMES_FILE} not found.")
        print(f"  Using built-in fallback names.")
        print(f"  For better results run: python generate_ph_names.py first.")
        first_names = [
            'Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Carlos',
            'Elena', 'Ramon', 'Lucia', 'Eduardo', 'Carmen', 'Antonio',
            'Isabel', 'Francisco', 'Gloria', 'Roberto', 'Corazon',
            'Ricardo', 'Remedios', 'Manuel', 'Teresita', 'Andres',
            'Lourdes', 'Fernando', 'Maricel', 'Rolando', 'Rowena',
            'Danilo', 'Cristina', 'Ernesto', 'Marilou', 'Renato',
            'Felicidad', 'Alfredo', 'Natividad', 'Domingo', 'Milagros',
        ]
        last_names = [
            'Santos', 'Reyes', 'Cruz', 'Bautista', 'Ocampo', 'Garcia',
            'Mendoza', 'Torres', 'Flores', 'Aquino', 'Dela Cruz',
            'Del Rosario', 'San Jose', 'De Guzman', 'Villanueva',
            'Gonzales', 'Ramos', 'Diaz', 'Castro', 'Morales',
            'Lim', 'Tan', 'Go', 'Chua', 'Sy', 'Ong',
            'Macaraeg', 'Pascual', 'Buenaventura', 'Concepcion',
            'Manalo', 'Soriano', 'Evangelista', 'Salazar', 'Tolentino',
        ]
    return first_names, last_names


MIDDLE_NAMES = [
    'dela', 'de la', 'del', 'san', 'Santa',
    'Amor', 'Gracia', 'Fe', 'Paz', 'Luz',
    'Jose', 'Maria', 'Juan', 'Ana', 'Rosa',
]

SUFFIXES = ['Jr.', 'Sr.', 'II', 'III', '']  # '' = no suffix

MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

CITIES = [
    'Tarlac City', 'Manila', 'Quezon City', 'Caloocan', 'Davao City',
    'Cebu City', 'Zamboanga City', 'Antipolo', 'Pasig', 'Cagayan de Oro',
    'Paranaque', 'Valenzuela', 'Bacoor', 'General Santos', 'Makati',
    'Pasay', 'Las Pinas', 'Muntinlupa', 'Marikina', 'San Jose del Monte',
    'Cabanatuan', 'Angeles City', 'Olongapo', 'Iligan', 'Bacolod',
    'Iloilo City', 'Butuan', 'Cotabato City', 'Tacloban', 'Lucena',
]

PROVINCES = [
    'Tarlac', 'Metro Manila', 'Cebu', 'Davao del Sur', 'Cavite',
    'Laguna', 'Bulacan', 'Rizal', 'Pampanga', 'Batangas',
    'Nueva Ecija', 'Pangasinan', 'Ilocos Norte', 'Ilocos Sur',
    'Leyte', 'Negros Occidental', 'Negros Oriental', 'Iloilo',
    'Zamboanga del Sur', 'Misamis Oriental', 'Agusan del Norte',
    'South Cotabato', 'Sultan Kudarat', 'Maguindanao', 'Lanao del Sur',
]

BARANGAYS = [
    'Brgy. San Jose', 'Brgy. Sta. Maria', 'Brgy. San Antonio',
    'Brgy. Santo Nino', 'Brgy. Poblacion', 'Brgy. San Isidro',
    'Brgy. San Pedro', 'Brgy. San Miguel', 'Brgy. Mabini',
    'Brgy. Rizal', 'Brgy. Magsaysay', 'Brgy. Quezon',
]

RELIGIONS = [
    'Roman Catholic', 'Catholic', 'Islam', 'Muslim',
    'Iglesia ni Cristo', 'INC', 'Baptist', 'Methodist',
    'Seventh Day Adventist', 'Born Again Christian', 'Aglipayan',
]

OCCUPATIONS = [
    'Farmer', 'Teacher', 'Engineer', 'Nurse', 'Doctor',
    'Laborer', 'Housewife', 'Driver', 'Carpenter', 'Vendor',
    'Student', 'OFW', 'Fisherman', 'Mechanic', 'Electrician',
    'Police Officer', 'Military', 'Government Employee',
    'Business Owner', 'Retired',
]

CIVIL_STATUSES = ['Single', 'Married', 'Widowed', 'Legally Separated']

CITIZENSHIPS = ['Filipino', 'Filipino', 'Filipino', 'American',
                'Chinese', 'Japanese', 'Korean']  # weighted toward Filipino

DEATH_CAUSES = [
    'Cardio-Respiratory Arrest', 'Hypertensive Cardiovascular Disease',
    'Acute Myocardial Infarction', 'Cerebrovascular Accident',
    'Pneumonia', 'Septicemia', 'Renal Failure', 'Diabetes Mellitus',
    'Pulmonary Tuberculosis', 'Cancer of the Lung',
    'Chronic Obstructive Pulmonary Disease', 'Liver Cirrhosis',
    'Dengue Hemorrhagic Fever', 'Acute Gastroenteritis',
    'Congestive Heart Failure',
]

ATTENDANT_TYPES = [
    'Private Physician', 'Public Health Officer',
    'Hospital Authority', 'Hilot', 'None',
]


# ─────────────────────────────────────────────────────────────────────────────
#  TEXT GENERATORS  (one per field type)
# ─────────────────────────────────────────────────────────────────────────────

def gen_full_name(first_names, last_names, with_suffix=True):
    first  = random.choice(first_names)
    middle = random.choice(last_names)   # middle name = another last name (PH style)
    last   = random.choice(last_names)
    suffix = random.choice(SUFFIXES) if with_suffix else ''
    name   = f"{first} {middle} {last}"
    if suffix:
        name += f" {suffix}"
    return name


def gen_first_name(first_names):
    return random.choice(first_names)


def gen_last_name(last_names):
    return random.choice(last_names)


def gen_middle_name(last_names):
    # In Philippines, middle name = mother's maiden last name
    return random.choice(last_names)


def gen_date_slash():
    month = random.randint(1, 12)
    day   = random.randint(1, 28)
    year  = random.randint(1930, 2005)
    return f"{month:02d}/{day:02d}/{year}"


def gen_date_long():
    month = random.choice(MONTHS)
    day   = random.randint(1, 28)
    year  = random.randint(1930, 2005)
    return f"{month} {day}, {year}"


def gen_date_day():
    return str(random.randint(1, 28))


def gen_date_month():
    return random.choice(MONTHS)


def gen_date_year():
    return str(random.randint(1930, 2010))


def gen_age():
    return str(random.randint(1, 95))


def gen_place_full():
    return f"{random.choice(BARANGAYS)}, {random.choice(CITIES)}, {random.choice(PROVINCES)}"


def gen_place_city():
    return random.choice(CITIES)


def gen_place_province():
    return random.choice(PROVINCES)


def gen_address():
    num  = random.randint(1, 999)
    st   = random.choice(['Mabini St.', 'Rizal Ave.', 'MacArthur Hwy.',
                           'Quezon Blvd.', 'Gen. Luna St.', 'Bonifacio St.'])
    return f"{num} {st}, {random.choice(CITIES)}"


def gen_registry_no():
    year = random.randint(2000, 2024)
    seq  = random.randint(1, 9999)
    return f"{year}-{seq:04d}"


def gen_sex():
    return random.choice(['Male', 'Female'])


def gen_religion():
    return random.choice(RELIGIONS)


def gen_occupation():
    return random.choice(OCCUPATIONS)


def gen_civil_status():
    return random.choice(CIVIL_STATUSES)


def gen_citizenship():
    return random.choice(CITIZENSHIPS)


def gen_weight():
    return f"{random.randint(1500, 4500)} grams"


def gen_death_cause():
    return random.choice(DEATH_CAUSES)


def gen_attendant():
    return random.choice(ATTENDANT_TYPES)


# ─────────────────────────────────────────────────────────────────────────────
#  FORM FIELD DEFINITIONS
#  Each entry = (field_name, generator_function)
#  These match the fields in field_extractor.py exactly.
# ─────────────────────────────────────────────────────────────────────────────

def get_form_fields(form_type, first_names, last_names):
    fn = first_names
    ln = last_names

    if form_type == 'form1a':   # Birth Certificate
        return [
            ('province',                lambda: gen_place_province()),
            ('registry_no',             lambda: gen_registry_no()),
            ('city_municipality',       lambda: gen_place_city()),
            ('child_first_name',        lambda: gen_first_name(fn)),
            ('child_middle_name',       lambda: gen_middle_name(ln)),
            ('child_last_name',         lambda: gen_last_name(ln)),
            ('sex',                     lambda: gen_sex()),
            ('dob_day',                 lambda: gen_date_day()),
            ('dob_month',               lambda: gen_date_month()),
            ('dob_year',                lambda: gen_date_year()),
            ('place_birth_hospital',    lambda: f"Ospital ng {gen_place_city()}"),
            ('place_birth_city',        lambda: gen_place_city()),
            ('place_birth_province',    lambda: gen_place_province()),
            ('weight_at_birth',         lambda: gen_weight()),
            ('type_of_birth',           lambda: random.choice(['Single', 'Twin', 'Triplet'])),
            ('mother_first_name',       lambda: gen_first_name(fn)),
            ('mother_middle_name',      lambda: gen_middle_name(ln)),
            ('mother_last_name',        lambda: gen_last_name(ln)),
            ('mother_citizenship',      lambda: gen_citizenship()),
            ('mother_religion',         lambda: gen_religion()),
            ('mother_occupation',       lambda: gen_occupation()),
            ('mother_age_at_birth',     lambda: str(random.randint(16, 45))),
            ('mother_residence_house',  lambda: gen_address()),
            ('mother_residence_city',   lambda: gen_place_city()),
            ('mother_residence_province', lambda: gen_place_province()),
            ('father_first_name',       lambda: gen_first_name(fn)),
            ('father_middle_name',      lambda: gen_middle_name(ln)),
            ('father_last_name',        lambda: gen_last_name(ln)),
            ('father_citizenship',      lambda: gen_citizenship()),
            ('father_religion',         lambda: gen_religion()),
            ('father_occupation',       lambda: gen_occupation()),
            ('father_age_at_birth',     lambda: str(random.randint(18, 55))),
            ('parents_marriage_month',  lambda: gen_date_month()),
            ('parents_marriage_day',    lambda: gen_date_day()),
            ('parents_marriage_year',   lambda: gen_date_year()),
            ('parents_marriage_city',   lambda: gen_place_city()),
            ('informant_name',          lambda: gen_full_name(fn, ln, False)),
            ('informant_address',       lambda: gen_address()),
            ('informant_date',          lambda: gen_date_slash()),
        ]

    elif form_type == 'form2a':   # Death Certificate
        return [
            ('province',               lambda: gen_place_province()),
            ('registry_no',            lambda: gen_registry_no()),
            ('city_municipality',      lambda: gen_place_city()),
            ('deceased_first_name',    lambda: gen_first_name(fn)),
            ('deceased_middle_name',   lambda: gen_middle_name(ln)),
            ('deceased_last_name',     lambda: gen_last_name(ln)),
            ('sex',                    lambda: gen_sex()),
            ('religion',               lambda: gen_religion()),
            ('age_years',              lambda: gen_age()),
            ('place_death_full',       lambda: f"{gen_place_city()}, {gen_place_province()}"),
            ('dod_day',                lambda: gen_date_day()),
            ('dod_month',              lambda: gen_date_month()),
            ('dod_year',               lambda: gen_date_year()),
            ('citizenship',            lambda: gen_citizenship()),
            ('residence_full',         lambda: gen_address()),
            ('civil_status',           lambda: gen_civil_status()),
            ('occupation',             lambda: gen_occupation()),
            ('cause_immediate',        lambda: gen_death_cause()),
            ('cause_antecedent',       lambda: gen_death_cause()),
            ('cause_underlying',       lambda: gen_death_cause()),
            ('cause_other',            lambda: gen_death_cause()),
            ('informant_name',         lambda: gen_full_name(fn, ln, False)),
            ('informant_address',      lambda: gen_address()),
            ('informant_date',         lambda: gen_date_slash()),
        ]

    elif form_type == 'form3a':   # Marriage Certificate
        return [
            ('province',               lambda: gen_place_province()),
            ('city_municipality',      lambda: gen_place_city()),
            ('registry_no',            lambda: gen_registry_no()),
            ('husband_first_name',     lambda: gen_first_name(fn)),
            ('husband_middle_name',    lambda: gen_middle_name(ln)),
            ('husband_last_name',      lambda: gen_last_name(ln)),
            ('wife_first_name',        lambda: gen_first_name(fn)),
            ('wife_middle_name',       lambda: gen_middle_name(ln)),
            ('wife_last_name',         lambda: gen_last_name(ln)),
            ('husband_dob_day',        lambda: gen_date_day()),
            ('husband_dob_month',      lambda: gen_date_month()),
            ('husband_dob_year',       lambda: gen_date_year()),
            ('husband_age',            lambda: gen_age()),
            ('wife_dob_day',           lambda: gen_date_day()),
            ('wife_dob_month',         lambda: gen_date_month()),
            ('wife_dob_year',          lambda: gen_date_year()),
            ('wife_age',               lambda: gen_age()),
            ('husband_place_birth_city',    lambda: gen_place_city()),
            ('husband_place_birth_province', lambda: gen_place_province()),
            ('wife_place_birth_city',       lambda: gen_place_city()),
            ('wife_place_birth_province',   lambda: gen_place_province()),
            ('husband_citizenship',    lambda: gen_citizenship()),
            ('wife_citizenship',       lambda: gen_citizenship()),
            ('husband_religion',       lambda: gen_religion()),
            ('wife_religion',          lambda: gen_religion()),
            ('husband_civil_status',   lambda: gen_civil_status()),
            ('wife_civil_status',      lambda: gen_civil_status()),
            ('husband_father_first',   lambda: gen_first_name(fn)),
            ('husband_father_last',    lambda: gen_last_name(ln)),
            ('wife_father_first',      lambda: gen_first_name(fn)),
            ('wife_father_last',       lambda: gen_last_name(ln)),
            ('husband_mother_first',   lambda: gen_first_name(fn)),
            ('husband_mother_last',    lambda: gen_last_name(ln)),
            ('wife_mother_first',      lambda: gen_first_name(fn)),
            ('wife_mother_last',       lambda: gen_last_name(ln)),
            ('place_marriage_city',    lambda: gen_place_city()),
            ('place_marriage_province', lambda: gen_place_province()),
            ('date_marriage_day',      lambda: gen_date_day()),
            ('date_marriage_month',    lambda: gen_date_month()),
            ('date_marriage_year',     lambda: gen_date_year()),
        ]

    elif form_type == 'form90':   # Marriage License Application
        return [
            ('province',               lambda: gen_place_province()),
            ('city_municipality',      lambda: gen_place_city()),
            ('registry_no',            lambda: gen_registry_no()),
            ('husband_first_name',     lambda: gen_first_name(fn)),
            ('husband_middle_name',    lambda: gen_middle_name(ln)),
            ('husband_last_name',      lambda: gen_last_name(ln)),
            ('wife_first_name',        lambda: gen_first_name(fn)),
            ('wife_middle_name',       lambda: gen_middle_name(ln)),
            ('wife_last_name',         lambda: gen_last_name(ln)),
            ('husband_age',            lambda: gen_age()),
            ('wife_age',               lambda: gen_age()),
            ('husband_citizenship',    lambda: gen_citizenship()),
            ('wife_citizenship',       lambda: gen_citizenship()),
            ('husband_residence',      lambda: gen_address()),
            ('wife_residence',         lambda: gen_address()),
            ('application_date',       lambda: gen_date_slash()),
        ]

    return []


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_dataset():
    print("=" * 65)
    print("  fix_data.py — Synthetic Training Data Generator")
    print("=" * 65)

    # Load Filipino names
    print("\n[1/4] Loading Filipino names...")
    first_names, last_names = load_ph_names()

    # Create output directories
    print("\n[2/4] Creating output directories...")
    for split in ['train', 'val']:
        for form in ['form1a', 'form2a', 'form3a', 'form90']:
            Path(f'data/{split}/{form}').mkdir(parents=True, exist_ok=True)
    print("  ✓ Directories ready")

    # Load font
    print("\n[3/4] Loading font...")
    font = load_font(FONT_SIZE)
    print("  ✓ Font loaded")

    # Generate images
    print("\n[4/4] Generating images...")
    print(f"  {'Form':<10} {'Total':>7} {'Train':>7} {'Val':>7}")
    print(f"  {'-'*35}")

    train_annotations = []
    val_annotations   = []
    total_generated   = 0

    for form_type, n_samples in SAMPLES_PER_FORM.items():
        fields      = get_form_fields(form_type, first_names, last_names)
        n_val       = max(1, int(n_samples * VAL_SPLIT))
        n_train     = n_samples - n_val
        form_train  = 0
        form_val    = 0

        # Distribute samples evenly across all field types
        # Each field gets roughly n_samples // len(fields) images
        samples_per_field = max(1, n_samples // len(fields))

        img_idx = 0
        for field_name, generator in fields:
            for _ in range(samples_per_field):
                text = generator()
                if not text or not text.strip():
                    continue

                # Render image
                img  = render_text_image(text, font)
                fname = f"{field_name}_{img_idx:06d}.jpg"

                # Decide train or val
                is_val = (img_idx % round(1 / VAL_SPLIT)) == 0

                if is_val:
                    out_path = f"data/val/{form_type}/{fname}"
                    val_annotations.append({
                        'image_path': f"{form_type}/{fname}",
                        'text':       text,
                    })
                    form_val += 1
                else:
                    out_path = f"data/train/{form_type}/{fname}"
                    train_annotations.append({
                        'image_path': f"{form_type}/{fname}",
                        'text':       text,
                    })
                    form_train += 1

                img.save(out_path, quality=95)
                img_idx += 1

        total_generated += form_train + form_val
        print(f"  {form_type:<10} {form_train+form_val:>7,} "
              f"{form_train:>7,} {form_val:>7,}")

    # Save annotation files
    with open('data/train_annotations.json', 'w', encoding='utf-8') as f:
        json.dump(train_annotations, f, indent=2, ensure_ascii=False)

    with open('data/val_annotations.json', 'w', encoding='utf-8') as f:
        json.dump(val_annotations, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'=' * 65}")
    print(f"  DONE!")
    print(f"{'=' * 65}")
    print(f"  Total images generated : {total_generated:,}")
    print(f"  Train images           : {len(train_annotations):,}")
    print(f"  Val images             : {len(val_annotations):,}")
    print(f"\n  Saved:")
    print(f"    data/train_annotations.json  ({len(train_annotations)} entries)")
    print(f"    data/val_annotations.json    ({len(val_annotations)} entries)")
    print(f"\n  Next step: python train.py")
    print(f"{'=' * 65}")


if __name__ == '__main__':
    generate_dataset()