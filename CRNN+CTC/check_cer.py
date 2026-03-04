"""
check_cer.py
============
Measures TRUE CER by actually running the model on images.

Usage:
    python check_cer.py                        # live CER on val set
    python check_cer.py --saved                # old behavior (fast, unreliable)
    python check_cer.py --images test_images/  # run on any image folder
"""

import os
import sys
import json
import random
import cv2
import numpy as np
import editdistance
from pathlib import Path

try:
    import torch
except ImportError:
    print("ERROR: torch not installed. Run: pip install torch")
    exit(1)

USE_SAVED = '--saved' in sys.argv
IMAGE_DIR = None
for i, arg in enumerate(sys.argv[1:], 1):
    if arg == '--images' and i < len(sys.argv) - 1:
        IMAGE_DIR = sys.argv[i + 1]
    elif arg.startswith('--images='):
        IMAGE_DIR = arg.split('=', 1)[1]

CHECKPOINTS = [
    'checkpoint_epoch_50.pth',
    'checkpoint_epoch_60.pth',
    'checkpoint_epoch_70.pth',
    'checkpoint_epoch_80.pth',
    'checkpoint_epoch_90.pth',
    'checkpoint_epoch_100.pth',
]
CHECKPOINT_DIR = 'checkpoints'
VAL_DATA_DIR   = 'data/val'
VAL_ANN_FILE   = 'data/val_annotations.json'


class AdaptiveImageNormalizer:
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

    def _smart_resize_gray(self, gray):
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

    def normalize(self, img):
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        gray = self._crop_to_text(gray)
        gray = self._smart_resize_gray(gray)
        return self._binarize(gray)

    def to_tensor(self, img):
        return torch.FloatTensor(
            img.astype(np.float32) / 255.0
        ).unsqueeze(0).unsqueeze(0)


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


def measure_live_cer(model, idx_to_char, img_h, img_w,
                     ann_file, data_dir, device, max_samples=200):
    if not os.path.exists(ann_file):
        return None, 0, f"Annotation file not found: {ann_file}"

    with open(ann_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)

    if len(annotations) > max_samples:
        random.seed(42)
        annotations = random.sample(annotations, max_samples)

    normalizer = AdaptiveImageNormalizer(img_h, img_w)
    model.eval()

    total_char_dist = 0
    total_chars     = 0
    total_word_dist = 0
    total_words     = 0
    n_exact         = 0
    n_evaluated     = 0
    worst_errors    = []

    with torch.no_grad():
        for ann in annotations:
            img_path = os.path.join(data_dir, ann['image_path'])
            gt       = ann['text']
            if not os.path.exists(img_path):
                continue
            try:
                raw = cv2.imread(img_path)
                if raw is None:
                    continue
                norm   = normalizer.normalize(raw)
                tensor = normalizer.to_tensor(norm).to(device)
                out    = model(tensor)
                pred   = greedy_decode(out.cpu(), idx_to_char)[0]

                cd = editdistance.eval(pred, gt)
                wd = editdistance.eval(pred.split(), gt.split())

                total_char_dist += cd
                total_chars     += len(gt)
                total_word_dist += wd
                total_words     += len(gt.split())
                if pred == gt:
                    n_exact += 1
                if cd > 0:
                    worst_errors.append((gt, pred, cd))
                n_evaluated += 1
            except Exception:
                continue

    if n_evaluated == 0:
        return None, 0, "No images could be evaluated"

    cer = (total_char_dist / total_chars * 100) if total_chars > 0 else 0
    wer = (total_word_dist / total_words * 100) if total_words > 0 else 0
    acc = (n_exact / n_evaluated * 100)

    return {
        'cer': cer, 'wer': wer, 'exact_match': acc,
        'n_evaluated': n_evaluated,
        'errors': sorted(worst_errors, key=lambda x: x[2], reverse=True)[:5]
    }, n_evaluated, None


def run_on_folder(model, idx_to_char, img_h, img_w, folder, device):
    normalizer = AdaptiveImageNormalizer(img_h, img_w)
    model.eval()
    exts  = {'.jpg', '.jpeg', '.png', '.bmp'}
    paths = sorted(p for p in Path(folder).rglob('*') if p.suffix.lower() in exts)
    results = []
    with torch.no_grad():
        for p in paths:
            try:
                raw    = cv2.imread(str(p))
                norm   = normalizer.normalize(raw)
                tensor = normalizer.to_tensor(norm).to(device)
                pred   = greedy_decode(model(tensor).cpu(), idx_to_char)[0]
                results.append((p.name, pred))
            except Exception as e:
                results.append((p.name, f'ERROR: {e}'))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

if USE_SAVED:
    print("=" * 65)
    print("  SAVED CER  (training-time value — may not reflect real accuracy)")
    print("  Run without --saved for true live CER.")
    print("=" * 65)
    print("{:<8} {:<12} {:<12} {}".format("Epoch", "CER(%)", "WER(%)", "File"))
    print("-" * 65)
    best_cer, best_cp = float('inf'), None
    for cp in CHECKPOINTS:
        path = os.path.join(CHECKPOINT_DIR, cp)
        if not os.path.exists(path):
            continue
        try:
            c        = torch.load(path, weights_only=False)
            cer      = c['val_cer']
            epoch    = c['epoch']
            history  = c.get('history', {})
            wer_list = history.get('val_wer', [])
            wer      = wer_list[epoch - 1] if wer_list and epoch <= len(wer_list) else None
            wer_s    = f"{wer:.4f}%" if wer else 'N/A'
            marker   = ' <-- BEST' if cer < best_cer else ''
            print("{:<8} {:<12} {:<12} {}{}".format(
                epoch, f"{cer:.4f}%", wer_s, cp, marker))
            if cer < best_cer:
                best_cer, best_cp = cer, cp
        except Exception as e:
            print(f"  Could not load {cp}: {e}")
    print("=" * 65)
    print(f"\nBEST: {best_cp}  CER={best_cer:.4f}%")

else:
    print("=" * 78)
    print("  LIVE CER  —  model actually runs on images  (true accuracy)")
    print("=" * 78)
    print("{:<8} {:<10} {:<10} {:<12} {:<8} {}".format(
        "Epoch", "CER(%)", "WER(%)", "ExactMatch", "N", "File"))
    print("-" * 78)

    best_cer, best_cp, best_metrics = float('inf'), None, None

    for cp in CHECKPOINTS:
        cp_path = os.path.join(CHECKPOINT_DIR, cp)
        if not os.path.exists(cp_path):
            print(f"  (skipping {cp} — not found)")
            continue
        try:
            from crnn_model import get_crnn_model
            c           = torch.load(cp_path, map_location=device, weights_only=False)
            epoch       = c['epoch']
            idx_to_char = c['idx_to_char']
            config      = c.get('config', {})
            img_h       = config.get('img_height', 64)
            img_w       = config.get('img_width', 512)
            saved_cer   = c.get('val_cer', None)

            model = get_crnn_model(
                model_type=config.get('model_type', 'standard'),
                img_height=img_h,
                num_chars=c['model_state_dict']['fc.weight'].shape[0],
                hidden_size=config.get('hidden_size', 256),
                num_lstm_layers=config.get('num_lstm_layers', 2)
            ).to(device)
            model.load_state_dict(c['model_state_dict'])

            if IMAGE_DIR:
                print(f"\nPredictions from {cp}:")
                for fname, pred in run_on_folder(
                        model, idx_to_char, img_h, img_w, IMAGE_DIR, device):
                    print(f"  {fname:<35} ->  {pred}")
                continue

            metrics, n, err = measure_live_cer(
                model, idx_to_char, img_h, img_w,
                VAL_ANN_FILE, VAL_DATA_DIR, device)

            if metrics is None:
                print(f"  Epoch {epoch}  SKIP: {err}")
                continue

            cer    = metrics['cer']
            marker = ' <-- BEST' if cer < best_cer else ''
            print("{:<8} {:<10} {:<10} {:<12} {:<8} {}{}".format(
                epoch,
                f"{cer:.2f}%",
                f"{metrics['wer']:.2f}%",
                f"{metrics['exact_match']:.1f}%",
                n, cp, marker))

            if saved_cer and abs(cer - saved_cer) > 2.0:
                print(f"          ^ MISMATCH: saved={saved_cer:.2f}%  live={cer:.2f}%"
                      f"  diff={abs(cer - saved_cer):.2f}%")
                print(f"            Cause: model trained on clean synthetic only.")
                print(f"            Fix:   regenerate data with fix_data.py + retrain.")

            if cer < best_cer:
                best_cer, best_cp, best_metrics = cer, cp, metrics

        except Exception as e:
            print(f"  Could not evaluate {cp}: {e}")

    if not IMAGE_DIR:
        print("=" * 78)
        print(f"\nBEST CHECKPOINT : {best_cp}")
        print(f"BEST LIVE CER   : {best_cer:.4f}%")

        if best_metrics and best_metrics['errors']:
            print(f"\nWorst predictions (GT -> Predicted):")
            for gt, pred, dist in best_metrics['errors']:
                print(f"  [{dist:2d}]  '{gt}'")
                print(f"        '{pred}'")

        print(f"\nTo use best model:")
        print(f"  import shutil")
        print(f"  shutil.copy('checkpoints/{best_cp}', 'checkpoints/best_model.pth')")
        print("=" * 78)