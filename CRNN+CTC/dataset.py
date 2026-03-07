"""
dataset.py
==========
PyTorch Dataset and DataLoader utilities for the Civil Registry OCR system.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


# ─────────────────────────────────────────────────────────────────────────────
#  CHARACTER SET
# ─────────────────────────────────────────────────────────────────────────────

PRINTABLE_CHARS = [chr(i) for i in range(32, 127)]  # space (32) to ~ (126)


def build_char_maps(extra_chars: Optional[List[str]] = None):
    chars = PRINTABLE_CHARS.copy()
    if extra_chars:
        for c in extra_chars:
            if c not in chars:
                chars.append(c)
    char_to_idx = {c: i + 1 for i, c in enumerate(chars)}
    idx_to_char = {i + 1: c for i, c in enumerate(chars)}
    num_chars   = len(chars) + 1  # +1 for blank=0
    return char_to_idx, idx_to_char, num_chars


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE NORMALIZER
# ─────────────────────────────────────────────────────────────────────────────

class ImageNormalizer:

    def __init__(self, target_height: int = 64, target_width: int = 512):
        self.H = target_height
        self.W = target_width

    def _to_gray(self, img):
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img.copy()

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

    def _aspect_resize(self, gray):
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

    def normalize(self, img: np.ndarray) -> np.ndarray:
        gray = self._to_gray(img)
        # NOTE: fastNlMeansDenoising intentionally removed from training pipeline.
        # It is slow (~200ms/image) and pointless on clean synthetic images.
        # Denoising is only applied in check_cer.py / inference.py (AdaptiveNormalizer)
        # which runs on real scanned documents where denoising actually helps.
        gray = self._crop_to_text(gray)
        gray = self._aspect_resize(gray)
        return self._binarize(gray)

    def to_tensor(self, img: np.ndarray) -> torch.Tensor:
        return torch.FloatTensor(
            img.astype(np.float32) / 255.0
        ).unsqueeze(0)  # [1, H, W]


# ─────────────────────────────────────────────────────────────────────────────
#  AUGMENTATION
# ─────────────────────────────────────────────────────────────────────────────

class Augmenter:

    def __call__(self, img: np.ndarray) -> np.ndarray:
        img = img.copy()

        # Random slight rotation (±3°)
        if random.random() < 0.3:
            angle = random.uniform(-3, 3)
            h, w  = img.shape
            M     = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            img   = cv2.warpAffine(img, M, (w, h),
                                   borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=255)

        # Random brightness/contrast
        if random.random() < 0.4:
            alpha = random.uniform(0.8, 1.2)
            beta  = random.randint(-20, 20)
            img   = np.clip(alpha * img.astype(np.float32) + beta,
                            0, 255).astype(np.uint8)

        # Gaussian blur
        if random.random() < 0.3:
            ksize = random.choice([3, 5])
            img   = cv2.GaussianBlur(img, (ksize, ksize), 0)

        # Salt-and-pepper noise
        if random.random() < 0.2:
            noise = np.random.randint(0, 100, img.shape)
            img[noise < 2]  = 0
            img[noise > 97] = 255

        # Random small horizontal shift
        if random.random() < 0.2:
            h, w  = img.shape
            shift = random.randint(-int(w * 0.05), int(w * 0.05))
            M     = np.float32([[1, 0, shift], [0, 1, 0]])
            img   = cv2.warpAffine(img, M, (w, h),
                                   borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=255)

        # ── NEW: Horizontal line noise ────────────────────────────────────────
        # Simulates ruled form lines bleeding through behind the text.
        # Civil registry forms have printed horizontal grid lines — scanners
        # often pick these up as faint grey stripes across text fields.
        if random.random() < 0.3:
            h, w    = img.shape
            n_lines = random.randint(1, 3)
            for _ in range(n_lines):
                y         = random.randint(0, h - 1)
                thickness = random.choice([1, 1, 1, 2])   # mostly 1px
                intensity = random.randint(160, 220)       # light grey, not black
                cv2.line(img, (0, y), (w, y),
                         color=intensity, thickness=thickness)

        # ── NEW: Perspective warp ─────────────────────────────────────────────
        # Simulates documents scanned or photographed at a slight angle.
        # Keystone distortion is common when forms are placed unevenly on
        # a flatbed scanner or photographed with a phone camera.
        if random.random() < 0.25:
            h, w  = img.shape
            d     = 0.03
            dx    = int(w * d)
            dy    = int(h * d)
            src   = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            dst   = np.float32([
                [random.randint(0, dx),     random.randint(0, dy)],
                [w - random.randint(0, dx), random.randint(0, dy)],
                [w - random.randint(0, dx), h - random.randint(0, dy)],
                [random.randint(0, dx),     h - random.randint(0, dy)],
            ])
            M   = cv2.getPerspectiveTransform(src, dst)
            img = cv2.warpPerspective(img, M, (w, h),
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=255)

        return img


# ─────────────────────────────────────────────────────────────────────────────
#  DATASET
# ─────────────────────────────────────────────────────────────────────────────

class CivilRegistryDataset(Dataset):
    """
    Args:
        data_dir         : root folder containing image subfolders (e.g. 'data/train')
        annotations_file : path to JSON file with image_path + text pairs
        img_height       : target image height (default 64)
        img_width        : target image width  (default 512)
        augment          : True = apply augmentation (training only)
        form_type        : 'all' or filter by form e.g. 'form1a'

    Properties used by train.py:
        .num_chars    → passed to CRNN model
        .char_to_idx  → saved in checkpoint
        .idx_to_char  → used for decoding predictions

    __getitem__ returns:
        image_tensor   FloatTensor [1, H, W]
        target         LongTensor  [label_length]
        target_length  int
        text           str  (original ground truth)
    """

    def __init__(
        self,
        data_dir:         str,
        annotations_file: str,
        img_height:       int  = 64,
        img_width:        int  = 512,
        augment:          bool = False,
        form_type:        str  = 'all',
    ):
        self.data_dir   = Path(data_dir)
        self.augment    = augment
        self.normalizer = ImageNormalizer(img_height, img_width)
        self.augmenter  = Augmenter()

        self.char_to_idx, self.idx_to_char, self.num_chars = build_char_maps()

        with open(annotations_file, 'r', encoding='utf-8') as f:
            all_annotations = json.load(f)

        if form_type != 'all':
            all_annotations = [
                a for a in all_annotations
                if form_type in a.get('image_path', '')
            ]

        self.samples: List[Dict] = []
        missing = 0
        for ann in all_annotations:
            img_path = self.data_dir / ann['image_path']
            if img_path.exists():
                text = ann['text'].strip()
                if text:
                    self.samples.append({
                        'image_path': str(img_path),
                        'text':       text,
                    })
            else:
                missing += 1

        if missing > 0:
            print(f"  [Dataset] WARNING: {missing} image(s) not found and skipped.")

        print(f"  [Dataset] Loaded {len(self.samples)} samples "
              f"from {annotations_file}  (augment={augment})")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        text   = sample['text']

        img = cv2.imread(sample['image_path'])
        if img is None:
            img = np.ones((64, 512, 3), dtype=np.uint8) * 255

        normalized   = self.normalizer.normalize(img)
        if self.augment:
            normalized = self.augmenter(normalized)

        image_tensor = self.normalizer.to_tensor(normalized)  # [1, H, W]

        encoded = [
            self.char_to_idx[c]
            for c in text
            if c in self.char_to_idx
        ]
        if len(encoded) == 0:
            encoded = [self.char_to_idx.get(' ', 1)]

        target        = torch.LongTensor(encoded)
        target_length = len(encoded)

        return image_tensor, target, target_length, text


# ─────────────────────────────────────────────────────────────────────────────
#  COLLATE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def collate_fn(batch):
    """
    CTC loss needs all labels packed into one flat 1D tensor.
    PyTorch's default collator can't handle variable-length labels,
    so this custom function packs them correctly.

    Returns:
        images         FloatTensor [B, 1, H, W]
        targets        LongTensor  [sum of all label lengths]
        target_lengths LongTensor  [B]
        texts          List[str]
    """
    images, targets, target_lengths, texts = zip(*batch)

    images         = torch.stack(images, dim=0)
    targets        = torch.cat([t for t in targets])
    target_lengths = torch.LongTensor(target_lengths)

    return images, targets, target_lengths, list(texts)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: CREATE ANNOTATION FILE  (run once to build your JSON)
# ─────────────────────────────────────────────────────────────────────────────

def create_annotation_file(data_dir: str, output_file: str,
                            extensions=('.jpg', '.jpeg', '.png')):
    """
    Auto-generate annotations JSON by scanning data_dir.
    For each image, looks for a sidecar .txt file with the same name.
    If not found, uses the filename stem (underscores → spaces) as label.

    Usage:
        from dataset import create_annotation_file
        create_annotation_file('data/train', 'data/train_annotations.json')
        create_annotation_file('data/val',   'data/val_annotations.json')
    """
    data_path   = Path(data_dir)
    annotations = []

    for img_path in sorted(data_path.rglob('*')):
        if img_path.suffix.lower() not in extensions:
            continue
        txt_path = img_path.with_suffix('.txt')
        if txt_path.exists():
            label = txt_path.read_text(encoding='utf-8').strip()
        else:
            label = img_path.stem.replace('_', ' ')
        if not label:
            continue
        rel_path = img_path.relative_to(data_path)
        annotations.append({
            'image_path': str(rel_path).replace('\\', '/'),
            'text':       label,
        })

    os.makedirs(Path(output_file).parent, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(annotations)} entries → {output_file}")
    return annotations


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST  (python dataset.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 55)
    print("  dataset.py self-test")
    print("=" * 55)

    c2i, i2c, n = build_char_maps()
    print(f"\n  Vocab size : {n}  (including blank=0)")
    print(f"  'A'={c2i['A']}  '0'={c2i['0']}  ' '={c2i[' ']}  '.'={c2i['.']}")

    dummy = np.ones((80, 300, 3), dtype=np.uint8) * 200
    norm  = ImageNormalizer(64, 512)
    out   = norm.normalize(dummy)
    t     = norm.to_tensor(out)
    print(f"\n  Normalizer : {dummy.shape} → {out.shape} → tensor {t.shape}")

    fake = [
        (torch.zeros(1, 64, 512), torch.LongTensor([1, 2, 3]),    3, "ABC"),
        (torch.zeros(1, 64, 512), torch.LongTensor([4, 5]),        2, "DE"),
        (torch.zeros(1, 64, 512), torch.LongTensor([6, 7, 8, 9]), 4, "FGHI"),
    ]
    imgs, tgts, tlens, txts = collate_fn(fake)
    print(f"\n  collate_fn : images={imgs.shape}  "
          f"targets={tgts.shape}  lengths={tlens.tolist()}")

    print("\n  ✓ All checks passed.\n")