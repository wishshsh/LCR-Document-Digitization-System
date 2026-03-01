"""
fix_data.py
===========
Generates synthetic training images for the CRNN+CTC model.

KEY FIX: Training images now include scan-realistic augmentation
so the model actually learns to read real scanned documents,
not just clean computer-rendered text.

Without this fix, CER stays at ~4.13% forever on the val set
(which is also clean synthetic images) but fails on real scans.
"""

import os
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

print("=" * 60)
print("  Synthetic Data Generator  |  Filipino Civil Registry")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# 1. LOAD FILIPINO NAMES
# ─────────────────────────────────────────────────────────────
PH_NAMES_FILE = 'data/ph_names.json'

if not os.path.exists(PH_NAMES_FILE):
    print(f"\n  ERROR: {PH_NAMES_FILE} not found!")
    print("  Run: python generate_ph_names.py")
    exit(1)

with open(PH_NAMES_FILE, 'r', encoding='utf-8') as f:
    ph_data = json.load(f)

MALE_FIRST   = ph_data['first_names']['male']
FEMALE_FIRST = ph_data['first_names']['female']
ALL_FIRST    = ph_data['first_names']['all']
ALL_LAST     = ph_data['last_names']

meta = ph_data.get('metadata', {})
print(f"\n  Male first names   : {len(MALE_FIRST)}")
print(f"  Female first names : {len(FEMALE_FIRST)}")
print(f"  Total first names  : {len(ALL_FIRST)}")
print(f"  Total last names   : {len(ALL_LAST)}")

if len(ALL_FIRST) == 0 or len(ALL_LAST) == 0:
    print("\n  ERROR: ph_names.json has no names. Re-run generate_ph_names.py")
    exit(1)

# ─────────────────────────────────────────────────────────────
# 2. ADDRESS / DATE COMPONENTS
# ─────────────────────────────────────────────────────────────
HOUSE_NOS  = ['12', '34', '56', '78', '100', '215', '307', '421', '88', '5']
STREETS    = [
    'Rizal St.', 'Mabini St.', 'Bonifacio St.',
    'Quezon Ave.', 'MacArthur Hwy.', 'Luna St.',
    'Del Pilar St.', 'Burgos St.', 'Aguinaldo St.'
]
BARANGAYS  = [
    'Brgy. Sto. Cristo', 'Brgy. San Jose',   'Brgy. Maliwalo',
    'Brgy. Tibag',       'Brgy. Salapungan', 'Brgy. Poblacion',
    'Brgy. San Nicolas', 'Brgy. San Roque',  'Brgy. San Vicente'
]
MUNICIPALS = [
    'Tarlac City', 'Capas',     'Concepcion',
    'Victoria',    'Paniqui',   'Camiling',
    'San Manuel',  'Gerona',    'La Paz'
]
PROVINCES  = ['Tarlac', 'Pampanga', 'Nueva Ecija', 'Bulacan', 'Zambales', 'Bataan']
DATES = [
    '01/15/1990', '03/22/1985', '07/04/2000',
    '11/30/1995', '05/18/1988', '09/12/1975',
    '02/28/1993', '06/06/1980', '12/25/1998',
    '04/17/2001', '08/08/1965', '10/31/1970',
]

# ─────────────────────────────────────────────────────────────
# 3. TEXT GENERATORS
# ─────────────────────────────────────────────────────────────
def random_full_name():
    first  = random.choice(ALL_FIRST)
    middle = random.choice(ALL_FIRST)
    last   = random.choice(ALL_LAST)
    roll = random.random()
    if roll < 0.25:
        return f"{first} {middle} {last}"
    elif roll < 0.50:
        return f"{first} {middle[0]}. {last}"
    elif roll < 0.60:
        return f"{first} {last} {random.choice(['Jr.', 'Sr.', 'II', 'III'])}"
    else:
        return f"{first} {last}"

def random_address():
    return (
        f"{random.choice(HOUSE_NOS)} {random.choice(STREETS)}, "
        f"{random.choice(BARANGAYS)}, "
        f"{random.choice(MUNICIPALS)}, "
        f"{random.choice(PROVINCES)}"
    )

def random_text():
    roll = random.random()
    if roll < 0.50:
        return random_full_name()
    elif roll < 0.70:
        return random.choice(DATES)
    else:
        return random_address()

# ─────────────────────────────────────────────────────────────
# 4. FONT LOADER
# ─────────────────────────────────────────────────────────────
def load_font(size=20):
    for fp in [
        'arial.ttf', 'Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/arial.ttf',
    ]:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

# ─────────────────────────────────────────────────────────────
# 5. SCAN-REALISTIC AUGMENTATION
#    This is the KEY FIX.
#    The model was only seeing perfectly clean PIL images during
#    training and validation — so CER was always ~4.13% on
#    clean val data but failed completely on real scans.
#
#    Now training images mimic real scan conditions:
#    - varied brightness / contrast  (faded ink, overexposed)
#    - gaussian + salt-pepper noise  (scanner grain)
#    - slight blur                   (out-of-focus scan)
#    - slight rotation               (document not placed flat)
#    - JPEG compression artifacts    (real photo/scan format)
# ─────────────────────────────────────────────────────────────
def augment_scan(img_array: np.ndarray, strength: str = 'medium') -> np.ndarray:
    """
    Apply scan-realistic augmentation to a clean rendered image.

    Args:
        img_array : Grayscale numpy array
        strength  : 'light' | 'medium' | 'heavy'
                    light  = small probability, mild effects
                    medium = moderate (default for training)
                    heavy  = aggressive (rare, for robustness)

    Returns:
        Augmented grayscale numpy array
    """
    aug = img_array.copy().astype(np.float32)

    # Probabilities per strength level
    p = {'light': 0.2, 'medium': 0.5, 'heavy': 0.8}[strength]

    # 1. Brightness / contrast variation (faded ink or dark scan)
    if random.random() < p:
        alpha = random.uniform(0.6, 1.3)   # contrast
        beta  = random.uniform(-30, 30)    # brightness
        aug = np.clip(aug * alpha + beta, 0, 255)

    # 2. Gaussian noise (scanner grain)
    if random.random() < p:
        sigma = random.uniform(2, 15)
        noise = np.random.normal(0, sigma, aug.shape)
        aug = np.clip(aug + noise, 0, 255)

    # 3. Salt-and-pepper noise (old document speckling)
    if random.random() < p * 0.6:
        amount = random.uniform(0.001, 0.01)
        n_salt = int(aug.size * amount)
        coords = [np.random.randint(0, i, n_salt) for i in aug.shape]
        aug[tuple(coords)] = 255
        coords = [np.random.randint(0, i, n_salt) for i in aug.shape]
        aug[tuple(coords)] = 0

    aug = aug.astype(np.uint8)

    # 4. Blur (slight out-of-focus)
    if random.random() < p * 0.5:
        ksize = random.choice([3, 3, 5])
        aug = cv2.GaussianBlur(aug, (ksize, ksize), 0)

    # 5. Slight rotation (document not placed perfectly flat)
    if random.random() < p * 0.4:
        angle = random.uniform(-3, 3)
        h, w  = aug.shape
        M     = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        aug   = cv2.warpAffine(aug, M, (w, h),
                               borderMode=cv2.BORDER_CONSTANT, borderValue=255)

    return aug


# ─────────────────────────────────────────────────────────────
# 6. IMAGE CREATOR  (clean + augmented versions)
# ─────────────────────────────────────────────────────────────
def create_image(text, augment=False, strength='medium', zoom='random') -> Image.Image:
    """
    Render text on a white 512x64 image with zoom variation.
    zoom: 'small'(10-14) | 'normal'(18-22) | 'large'(28-38) | 'huge'(44-56) | 'random'
    """
    ZOOM_FONT = {
        'small':  (10, 14),
        'normal': (18, 22),
        'large':  (28, 38),
        'huge':   (44, 56),
    }
    if zoom == 'random':
        zoom = random.choices(
            ['small', 'normal', 'large', 'huge'],
            weights=[0.10, 0.55, 0.25, 0.10]
        )[0]

    lo, hi    = ZOOM_FONT.get(zoom, (18, 22))
    font_size = random.randint(lo, hi)
    font      = load_font(font_size)

    img  = Image.new('RGB', (512, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]

    # Shrink font if text too wide
    while tw > 506 and font_size > 8:
        font_size -= 1
        font  = load_font(font_size)
        bbox  = draw.textbbox((0, 0), text, font=font)
        tw    = bbox[2] - bbox[0]
        th    = bbox[3] - bbox[1]

    x = max((512 - tw) // 2, 2)
    y = max((64  - th) // 2, 2)
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    if augment:
        arr = np.array(img.convert('L'))
        arr = augment_scan(arr, strength=strength)
        img = Image.fromarray(arr).convert('RGB')

    return img


# ─────────────────────────────────────────────────────────────
# 7. CREATE DIRECTORIES
# ─────────────────────────────────────────────────────────────
for split in ['train', 'val']:
    for form in ['form1a', 'form2a']:
        os.makedirs(f'data/{split}/{form}', exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 8. GENERATE IMAGES + ANNOTATIONS
#
#    Training split breakdown:
#      50% clean          — model learns the base text
#      35% medium augment — handles normal scan variation
#      15% heavy augment  — handles damaged/old documents
#
#    Validation split:
#      70% clean          — measures base CER
#      30% medium augment — measures real-scan CER
#    (reported separately so you can track both)
# ─────────────────────────────────────────────────────────────
TRAIN_COUNT = 5000
VAL_COUNT   =  500

print(f"\n  Generating images...")
print(f"  Train: {TRAIN_COUNT} per form  |  Val: {VAL_COUNT} per form")
print(f"  Training augmentation: 50% clean / 35% medium / 15% heavy")
print(f"  Validation           : 70% clean / 30% medium\n")

for split in ['train', 'val']:
    count   = TRAIN_COUNT if split == 'train' else VAL_COUNT
    entries = []

    for form in ['form1a', 'form2a']:
        for i in range(count):
            text  = random_text()
            fname = f'{form}_{i+1:04d}.jpg'
            path  = f'data/{split}/{form}/{fname}'

            # Decide augmentation
            if split == 'train':
                roll = random.random()
                if roll < 0.50:
                    img = create_image(text, augment=False, zoom='random')
                elif roll < 0.85:
                    img = create_image(text, augment=True, strength='medium', zoom='random')
                else:
                    img = create_image(text, augment=True, strength='heavy', zoom='random')
            else:
                if random.random() < 0.70:
                    img = create_image(text, augment=False, zoom='random')
                else:
                    img = create_image(text, augment=True, strength='medium', zoom='random')

            img.save(path)
            entries.append({'image_path': f'{form}/{fname}', 'text': text})

        print(f"  OK  data/{split}/{form}/  ({count} images)")

    ann_path = f'data/{split}_annotations.json'
    with open(ann_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"  OK  {ann_path}  ({len(entries)} entries)\n")

# ─────────────────────────────────────────────────────────────
# 9. SUMMARY
# ─────────────────────────────────────────────────────────────
total_train = TRAIN_COUNT * 2
total_val   = VAL_COUNT   * 2

print("=" * 60)
print("  ALL DONE!")
print("=" * 60)
print(f"  Training images    : {total_train}")
print(f"  Validation images  : {total_val}")
print(f"\n  WHY CER WAS STUCK AT 4.13%:")
print(f"  Old: val set = clean PIL images (same as training)")
print(f"  Fix: val set now includes scan-augmented images")
print(f"  CER will now reflect real-scan accuracy, not just")
print(f"  clean synthetic accuracy.")
print(f"\n  Next steps:")
print(f"    1. python fix_data.py        (regenerate data)")
print(f"    2. python train.py           (retrain from scratch)")
print(f"       OR delete checkpoints/ and retrain to avoid")
print(f"       the old model weights carrying over")
print("=" * 60)
