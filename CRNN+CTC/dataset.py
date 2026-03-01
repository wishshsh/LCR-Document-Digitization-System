"""
Dataset Handler for Philippine Civil Registry Documents

FIXES:
  - img_width default changed from 200 -> 400  (matches train.py config and fix_data.py)
  - _preprocess_image: binarize BEFORE resize was causing LANCZOS gray artifacts
    Fixed to: resize grayscale first, THEN binarize — matches inference.py exactly
"""

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from pathlib import Path
import json


class CivilRegistryDataset(Dataset):

    def __init__(
        self,
        data_dir,
        annotations_file,
        img_height=64,
        img_width=512,          # FIXED: was 200, must match fix_data.py (400x64 images)
        augment=False,
        form_type='all'
    ):
        self.data_dir   = Path(data_dir)
        self.img_height = img_height
        self.img_width  = img_width
        self.augment    = augment
        self.form_type  = form_type

        with open(annotations_file, 'r', encoding='utf-8') as f:
            self.annotations = json.load(f)

        if form_type != 'all':
            self.annotations = [
                ann for ann in self.annotations
                if ann.get('form_type') == form_type
            ]

        self.chars       = self._build_charset()
        self.char_to_idx = {char: idx + 1 for idx, char in enumerate(self.chars)}
        self.char_to_idx['<blank>'] = 0
        self.idx_to_char = {v: k for k, v in self.char_to_idx.items()}
        self.num_chars   = len(self.char_to_idx)

        if self.augment:
            self.transform = A.Compose([
                A.OneOf([
                    A.GaussNoise(var_limit=(10.0, 50.0), p=0.5),
                    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.5),
                ], p=0.3),
                A.OneOf([
                    A.MotionBlur(blur_limit=3, p=0.5),
                    A.GaussianBlur(blur_limit=3, p=0.5),
                ], p=0.2),
                A.RandomBrightnessContrast(
                    brightness_limit=0.2, contrast_limit=0.2, p=0.3),
                A.OneOf([
                    A.ElasticTransform(alpha=1, sigma=50, p=0.5),
                    A.GridDistortion(num_steps=5, distort_limit=0.3, p=0.5),
                ], p=0.2),
            ])

        print(f"  Dataset loaded: {len(self)} samples  |  {img_width}x{img_height}  |  "
              f"vocab={self.num_chars}  |  aug={'ON' if augment else 'OFF'}")

    def _build_charset(self):
        chars = set()
        chars.update([chr(i) for i in range(ord('A'), ord('Z') + 1)])
        chars.update([chr(i) for i in range(ord('a'), ord('z') + 1)])
        chars.update([chr(i) for i in range(ord('0'), ord('9') + 1)])
        chars.update([' ', '.', ',', '-', '/', '(', ')', ':', ';', "'", '"'])
        chars.update(['ñ', 'Ñ', 'á', 'é', 'í', 'ó', 'ú'])
        return sorted(list(chars))

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        img_path   = self.data_dir / annotation['image_path']
        img        = cv2.imread(str(img_path))

        if img is None:
            raise ValueError(f"Failed to load image: {img_path}")

        img  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        text = annotation['text']

        if self.augment:
            augmented = self.transform(image=img)
            img       = augmented['image']

        img = self._preprocess_image(img)
        img = img.astype(np.float32) / 255.0
        img = torch.FloatTensor(img).unsqueeze(0)

        label_encoded = self._encode_text(text)
        return img, torch.IntTensor(label_encoded), len(label_encoded), text

    def _preprocess_image(self, img):
        """
        FIXED pipeline order — matches inference.py exactly:
          1. Grayscale
          2. Denoise
          3. Resize on GRAYSCALE first   (no binary artifacts from LANCZOS)
          4. Binarize AFTER resize        (pure 0/255 result)

        Old (broken) order was: denoise -> threshold -> resize
        LANCZOS on a binary image introduces gray anti-aliasing pixels.
        """
        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # 2. Denoise
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # 3. Resize on GRAYSCALE
        gray = cv2.resize(gray, (self.img_width, self.img_height))

        # 4. Binarize AFTER resize — pure 0/255, matches inference
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def _encode_text(self, text):
        return [self.char_to_idx[c] for c in text if c in self.char_to_idx]

    def decode_prediction(self, indices):
        return ''.join(
            self.idx_to_char[idx] for idx in indices
            if idx != 0 and idx in self.idx_to_char
        )


def collate_fn(batch):
    images, labels, label_lengths, texts = zip(*batch)
    images        = torch.stack(images, dim=0)
    labels_cat    = torch.cat(labels)
    label_lengths = torch.IntTensor(label_lengths)
    return images, labels_cat, label_lengths, texts


def create_annotation_file(image_dir, output_file):
    image_dir   = Path(image_dir)
    annotations = []
    for img_path in image_dir.rglob('*.jpg'):
        txt_path = img_path.with_suffix('.txt')
        if txt_path.exists():
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            annotations.append({
                'image_path': str(img_path.relative_to(image_dir)),
                'text':       text,
                'form_type':  img_path.parent.name,
                'field_type': img_path.stem.split('_')[0]
            })
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    print(f"Created {output_file} with {len(annotations)} annotations")
    return annotations
