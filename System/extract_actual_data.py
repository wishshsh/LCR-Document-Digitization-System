"""
extract_actual_data.py
======================
Extract field crops from actual scanned civil registry forms and
auto-label them with EasyOCR as a starting point for CRNN fine-tuning.

Reads images from:
    actual_images/{form_type}/*.{png,jpg,jpeg}

For each image:
  1. Aligns to reference using ORB + ECC + corner fallback
  2. Crops every field defined in TEMPLATES
  3. Applies CLAHE per-crop before auto-labeling
  4. Saves crop to data/actual_crops/
  5. Auto-labels with EasyOCR + field-type post-processing

Output:
    data/actual_crops/             -- field crop images
    data/actual_annotations.json   -- labels for fine-tuning

After running:
  - Open actual_annotations.json
  - Fix any wrong 'text' values
  - Run finetune.py to train

Usage:
    cd python/CRNN+CTC
    python extract_actual_data.py

    # or point to a different images folder:
    python extract_actual_data.py --images /path/to/actual_images
"""

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image

# ── Paths ─────────────────────────────────────────────────────
THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(os.path.dirname(THIS_DIR))   # project root
PYTHON_DIR = os.path.dirname(THIS_DIR)                    # python/

sys.path.insert(0, PYTHON_DIR)

from template_matcher import (
    TEMPLATES, REFERENCE_IMAGES,
    align_to_reference, _preprocess, _crop_field,
    _get_easyocr, _postprocess,
)

try:
    import cv2 as _cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

CROPS_DIR  = os.path.join(THIS_DIR, 'data', 'actual_crops')
ANN_PATH   = os.path.join(THIS_DIR, 'data', 'actual_annotations.json')
MIN_CROP_W = 10
MIN_CROP_H = 6

# Substrings that indicate a file is a debug/test output, not a real scan
_SKIP_SUBSTRINGS = ('debug', 'aligned', 'crops_aligned')
_SKIP_PREFIXES   = ('test_', 'father_', 'father2_')


def _is_scan(fname: str) -> bool:
    base = fname.lower()
    ext  = os.path.splitext(base)[1]
    if ext not in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp'):
        return False
    if any(s in base for s in _SKIP_SUBSTRINGS):
        return False
    if any(base.startswith(p) for p in _SKIP_PREFIXES):
        return False
    return True


def _ocr_crop(arr: np.ndarray, reader) -> str:
    """Run EasyOCR on a uint8 RGB numpy array."""
    try:
        results = reader.readtext(arr, detail=0, paragraph=True)
        return ' '.join(results).strip()
    except Exception as e:
        return ''


def process_image(img_path: str, form_type: str, reader, crops_dir: str) -> list:
    """
    Align one scan, crop every template field, save crops, auto-label.
    Returns list of annotation dicts for this image.
    """
    template = TEMPLATES[form_type]
    fname    = os.path.basename(img_path)
    stem     = os.path.splitext(fname)[0]

    try:
        img = Image.open(img_path).convert('RGB')
    except Exception as e:
        print(f'    [skip] Cannot open: {e}')
        return []

    w, h = img.size
    print(f'  Processing {fname} ({w}x{h})...')

    # Align (ORB → ECC → corner → resize)
    img, orb_inliers = align_to_reference(img, form_type)
    print(f'    ORB inliers: {orb_inliers}')

    # Grayscale + deskew
    processed = _preprocess(img)

    annotations = []

    for field_name, coords in template.items():
        x1r, y1r, x2r, y2r, _ = coords
        crop = _crop_field(processed, x1r, y1r, x2r, y2r)

        if crop is None or crop.size[0] < MIN_CROP_W or crop.size[1] < MIN_CROP_H:
            continue

        # CLAHE per-crop before OCR (same as extract_fields in template_matcher)
        gray = np.array(crop.convert('L'))
        if _CV2_OK:
            clahe = _cv2.createCLAHE(clipLimit=1.5, tileGridSize=(2, 2))
            gray  = clahe.apply(gray)
        arr = np.stack([gray, gray, gray], axis=-1)

        raw   = _ocr_crop(arr, reader)
        label = _postprocess(raw, field_name)

        crop_fname = f'{form_type}_{stem}_{field_name}.png'
        crop.save(os.path.join(crops_dir, crop_fname))

        annotations.append({
            'image_path': os.path.join('data', 'actual_crops', crop_fname),
            'text':       label,
            'form_type':  form_type,
            'field':      field_name,
            'source_img': fname,
        })

    print(f'    Saved {len(annotations)} crops')
    return annotations


def main(images_root: str):
    os.makedirs(CROPS_DIR, exist_ok=True)

    print('[extract] Loading EasyOCR...')
    reader = _get_easyocr()
    if reader is None:
        print('[extract] ERROR: EasyOCR failed to load.')
        sys.exit(1)
    print('[extract] EasyOCR ready.')

    all_annotations = []

    for form_type in sorted(TEMPLATES.keys()):
        folder = os.path.join(images_root, form_type)
        if not os.path.isdir(folder):
            print(f'\n[extract] No images in {folder}, skipping.')
            continue

        scans = sorted(f for f in os.listdir(folder) if _is_scan(f))
        if not scans:
            print(f'\n[extract] No scan images in {folder}, skipping.')
            continue

        ref = REFERENCE_IMAGES.get(form_type, '')
        if not os.path.exists(ref):
            print(f'\n[extract] WARNING: No reference image for form {form_type} — alignment will be resize-only')

        print(f'\n[extract] Form {form_type} — {len(scans)} image(s)')

        for fname in scans:
            anns = process_image(os.path.join(folder, fname), form_type, reader, CROPS_DIR)
            all_annotations.extend(anns)

    with open(ANN_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_annotations, f, indent=2, ensure_ascii=False)

    total = len(all_annotations)
    print(f'\n[extract] Done.')
    print(f'  Crops saved : {total}')
    print(f'  Annotations : {ANN_PATH}')
    print()
    print('Review actual_annotations.json and correct any wrong labels,')
    print('then run finetune.py to train on this data.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--images',
        default=os.path.join(ROOT_DIR, 'actual_images'),
        help='Path to actual_images/ folder (default: <project_root>/actual_images)',
    )
    args = parser.parse_args()
    main(args.images)
