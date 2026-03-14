"""
compare_live_cer.py
===================
Runs live CER on all three checkpoints to find the best one.
Usage: python compare_live_cer.py
"""

import os
import sys
import json
import random
import cv2
import numpy as np
import editdistance
import torch
import torch.nn.functional as F
sys.path.append('.')
from crnn_model import get_crnn_model

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

VAL_ANN  = 'data/val_annotations.json'
VAL_DIR  = 'data/val'
MAX_SAMPLES = 200

CHECKPOINTS = {
    'Synthetic' : 'checkpoints/best_model.pth',
    'EMNIST'    : 'checkpoints/best_model_emnist.pth',
    'IAM'       : 'checkpoints/best_model_iam.pth',
}


def normalize(img, H=64, W=512):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    inv  = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(inv, 20, 255, cv2.THRESH_BINARY)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        pad   = max(4, int((y_max - y_min) * 0.15))
        y_min = max(0, y_min - pad)
        x_min = max(0, x_min - pad)
        y_max = min(gray.shape[0]-1, y_max + pad)
        x_max = min(gray.shape[1]-1, x_max + pad)
        gray  = gray[y_min:y_max+1, x_min:x_max+1]
    h, w = gray.shape
    if h == 0 or w == 0:
        return np.ones((H, W), dtype=np.uint8) * 255
    scale = H / h
    new_w = int(w * scale)
    if new_w > W:
        scale = W / w
        new_w = W
        new_h = int(h * scale)
    else:
        new_h = H
    resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    canvas  = np.ones((H, W), dtype=np.uint8) * 255
    canvas[(H-new_h)//2:(H-new_h)//2+new_h,
           (W-new_w)//2:(W-new_w)//2+new_w] = resized
    _, otsu = cv2.threshold(canvas, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return otsu


def greedy_decode(outputs, idx_to_char):
    pred_indices = torch.argmax(outputs, dim=2).permute(1, 0)
    results = []
    for seq in pred_indices:
        chars, prev = [], -1
        for idx in seq:
            idx = idx.item()
            if idx != 0 and idx != prev and idx in idx_to_char:
                chars.append(idx_to_char[idx])
            prev = idx
        results.append(''.join(chars))
    return results


def evaluate(checkpoint_path, label):
    if not os.path.exists(checkpoint_path):
        print(f"  {label:<12}: FILE NOT FOUND — skipping")
        return

    c      = torch.load(checkpoint_path, map_location=device, weights_only=False)
    config = c.get('config', {})

    # Load idx_to_char from checkpoint if available
    idx_to_char = c.get('idx_to_char', None)
    if idx_to_char is None:
        from dataset import build_char_maps
        _, idx_to_char, _ = build_char_maps()

    model = get_crnn_model(
        model_type      = config.get('model_type', 'standard'),
        img_height      = config.get('img_height', 64),
        num_chars       = c['model_state_dict']['fc.weight'].shape[0],
        hidden_size     = config.get('hidden_size', 128),
        num_lstm_layers = config.get('num_lstm_layers', 1),
    ).to(device)
    model.load_state_dict(c['model_state_dict'], strict=False)
    model.eval()

    with open(VAL_ANN, 'r', encoding='utf-8') as f:
        anns = json.load(f)
    random.seed(42)
    if len(anns) > MAX_SAMPLES:
        anns = random.sample(anns, MAX_SAMPLES)

    total_cd, total_c = 0, 0
    exact, n = 0, 0
    worst = []

    with torch.no_grad():
        for ann in anns:
            img_path = os.path.join(VAL_DIR, ann['image_path'])
            gt       = ann['text']
            if not os.path.exists(img_path):
                continue
            raw = cv2.imread(img_path)
            if raw is None:
                continue
            norm   = normalize(raw)
            tensor = torch.FloatTensor(
                norm.astype(np.float32) / 255.0
            ).unsqueeze(0).unsqueeze(0).to(device)
            out  = model(tensor)
            pred = greedy_decode(out.cpu(), idx_to_char)[0]
            cd   = editdistance.eval(pred, gt)
            total_cd += cd
            total_c  += len(gt)
            if pred == gt:
                exact += 1
            if cd > 0:
                worst.append((gt, pred, cd))
            n += 1

    cer = (total_cd / total_c * 100) if total_c > 0 else 0
    acc = (exact / n * 100) if n > 0 else 0
    print(f"  {label:<12}: CER={cer:.2f}%  ExactMatch={acc:.1f}%  (n={n})")

    if worst:
        worst = sorted(worst, key=lambda x: x[2], reverse=True)[:2]
        for gt, pred, d in worst:
            print(f"             [{d}] '{gt}' -> '{pred}'")


print("=" * 60)
print("  LIVE CER COMPARISON — all checkpoints")
print("=" * 60)
for label, path in CHECKPOINTS.items():
    evaluate(path, label)
print("=" * 60)
print("Use the checkpoint with the lowest CER for IAM/physical fine-tuning.")