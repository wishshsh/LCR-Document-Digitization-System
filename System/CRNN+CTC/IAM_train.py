"""
IAM_train.py
============
Fine-tune the CRNN model using the IAM Handwriting Word Database.
Builds on top of EMNIST-trained model (best_model_emnist.pth).

FIXES vs old version:
  - IMG_WIDTH 400 -> 512 (must match pipeline)
  - Added log_softmax before CTCLoss (was missing — caused catastrophic forgetting)
  - Phase 1: CNN FROZEN — only RNN+FC trained
  - Phase 2: Full model at very low LR
  - Loads from best_model_emnist.pth, falls back to best_model.pth
  - Uses get_crnn_model() with correct architecture from checkpoint config

DATASET:
  Download from: https://www.kaggle.com/datasets/nibinv23/iam-handwriting-word-database
  Expected structure:
    data/IAM/iam_words/
      words/        <- word image folders (a01, a02, ...)
      words.txt     <- annotation file

USAGE:
  python IAM_train.py --prepare          # convert IAM -> annotation JSON
  python IAM_train.py --train            # fine-tune model
  python IAM_train.py --prepare --train  # do both
"""

import os
import sys
import json
import argparse
import random
from pathlib import Path

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, ConcatDataset

sys.path.append('.')
from crnn_model import get_crnn_model
from dataset import CivilRegistryDataset, collate_fn

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
IAM_ROOT      = "data/IAM/iam_words"
IAM_WORDS_TXT = f"{IAM_ROOT}/words.txt"
IAM_WORDS_DIR = f"{IAM_ROOT}/words"

TRAIN_ANN     = "data/iam_train_annotations.json"
IAM_VAL_ANN   = "data/iam_val_annotations.json"   # written by --prepare (IAM word images)
SYNTH_VAL_ANN = "data/val_annotations.json"       # real civil registry val set — never overwritten
TRAIN_IMG_DIR = "data/train/iam"
VAL_IMG_DIR   = "data/val/iam"

IMG_HEIGHT    = 64
IMG_WIDTH     = 512       # FIXED: was 400 — must match pipeline
BATCH_SIZE    = 32
VAL_SPLIT     = 0.1
MAX_SAMPLES   = 50000

# Load from EMNIST checkpoint, fall back to synthetic if not found
CHECKPOINT_IN  = "checkpoints/best_model_emnist.pth"
CHECKPOINT_IN2 = "checkpoints/best_model.pth"   # fallback
CHECKPOINT_OUT = "checkpoints/best_model_iam.pth"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ─────────────────────────────────────────────
#  STEP 1 — PREPARE
# ─────────────────────────────────────────────
def prepare_iam():
    from PIL import Image

    print("\n" + "=" * 50)
    print("STEP 1 — Preparing IAM dataset")
    print("=" * 50)

    if not os.path.exists(IAM_WORDS_TXT):
        print(f"ERROR: {IAM_WORDS_TXT} not found!")
        print("Download from: https://www.kaggle.com/datasets/nibinv23/iam-handwriting-word-database")
        print("Expected structure:")
        print("  data/IAM/iam_words/words.txt")
        print("  data/IAM/iam_words/words/")
        sys.exit(1)

    os.makedirs(TRAIN_IMG_DIR, exist_ok=True)
    os.makedirs(VAL_IMG_DIR,   exist_ok=True)

    entries = []
    print(f"  Reading {IAM_WORDS_TXT} ...")
    with open(IAM_WORDS_TXT, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ")
            if len(parts) < 9:
                continue
            word_id    = parts[0]
            seg_result = parts[1]
            text       = parts[-1]
            if seg_result != "ok":
                continue
            if len(text) < 1 or len(text) > 32:
                continue
            parts_id = word_id.split("-")
            img_path = os.path.join(
                IAM_WORDS_DIR,
                parts_id[0],
                f"{parts_id[0]}-{parts_id[1]}",
                f"{word_id}.png"
            )
            if not os.path.exists(img_path):
                continue
            entries.append((img_path, text))

    print(f"  Found {len(entries)} valid word entries")

    if MAX_SAMPLES and len(entries) > MAX_SAMPLES:
        random.shuffle(entries)
        entries = entries[:MAX_SAMPLES]
        print(f"  Limiting to {MAX_SAMPLES} samples")

    random.shuffle(entries)
    split_idx     = int(len(entries) * (1 - VAL_SPLIT))
    train_entries = entries[:split_idx]
    val_entries   = entries[split_idx:]
    print(f"  Train: {len(train_entries)} | Val: {len(val_entries)}")
    print("  Copying and resizing images...")

    def process_entries(entry_list, out_dir, prefix):
        annotations = []
        for i, (src_path, text) in enumerate(entry_list):
            try:
                img = Image.open(src_path).convert("RGB")
                img = img.resize((IMG_WIDTH, IMG_HEIGHT))  # FIXED: 512x64
                fname    = f"iam_{prefix}_{i:06d}.jpg"
                out_path = os.path.join(out_dir, fname)
                img.save(out_path, quality=90)
                annotations.append({"image_path": f"iam/{fname}", "text": text})
            except Exception:
                continue
            if i % 5000 == 0:
                print(f"    {i}/{len(entry_list)} processed...")
        return annotations

    train_ann = process_entries(train_entries, TRAIN_IMG_DIR, "train")
    val_ann   = process_entries(val_entries,   VAL_IMG_DIR,   "val")

    with open(TRAIN_ANN, "w") as f:
        json.dump(train_ann, f, indent=2)
    with open(IAM_VAL_ANN, "w") as f:
        json.dump(val_ann, f, indent=2)

    print(f"\n  Train annotations -> {TRAIN_ANN} ({len(train_ann)} entries)")
    print(f"  Val annotations   -> {IAM_VAL_ANN} ({len(val_ann)} entries)")
    print("\n  Done! Now run: python IAM_train.py --train")


# ─────────────────────────────────────────────
#  STEP 2 — TRAIN
# ─────────────────────────────────────────────
def train_iam():
    print("\n" + "=" * 55)
    print("STEP 2 — Fine-tuning CRNN with IAM dataset")
    print("=" * 55)
    print(f"  Device : {DEVICE}")

    for ann_file in [TRAIN_ANN, SYNTH_VAL_ANN]:
        if not os.path.exists(ann_file):
            print(f"ERROR: {ann_file} not found! Run --prepare first.")
            sys.exit(1)

    train_dataset = CivilRegistryDataset(
        data_dir="data/train", annotations_file=TRAIN_ANN,
        img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=True
    )
    # FIXED: mix synthetic data in so the model never forgets Filipino multi-word sequences
    synth_dataset = CivilRegistryDataset(
        data_dir="data/train", annotations_file="data/train_annotations.json",
        img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=True
    )
    mixed_train = ConcatDataset([train_dataset, synth_dataset])
    val_dataset = CivilRegistryDataset(
        data_dir="data/val", annotations_file=SYNTH_VAL_ANN,
        img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=False
    )
    print(f"  IAM train     : {len(train_dataset)}")
    print(f"  Synthetic train: {len(synth_dataset)}")
    print(f"  Mixed train   : {len(mixed_train)}")
    print(f"  Val           : {len(val_dataset)}")

    train_loader = DataLoader(mixed_train, batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=0, collate_fn=collate_fn)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=0, collate_fn=collate_fn)

    # ── Load checkpoint (EMNIST preferred, synthetic fallback) ──
    ckpt_path = CHECKPOINT_IN if os.path.exists(CHECKPOINT_IN) else CHECKPOINT_IN2
    if not os.path.exists(ckpt_path):
        print(f"ERROR: No checkpoint found at {CHECKPOINT_IN} or {CHECKPOINT_IN2}")
        print("Run: python train.py  then  python train_with_emnist.py")
        sys.exit(1)

    print(f"  Loading: {ckpt_path}")
    ckpt   = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    config = ckpt.get('config', {})

    model = get_crnn_model(
        model_type      = config.get('model_type', 'standard'),
        img_height      = config.get('img_height', 64),
        num_chars       = train_dataset.num_chars,
        hidden_size     = config.get('hidden_size', 128),
        num_lstm_layers = config.get('num_lstm_layers', 1),
    ).to(DEVICE)

    missing, _ = model.load_state_dict(ckpt['model_state_dict'], strict=False)
    if missing:
        print(f"  Note: {len(missing)} layers re-initialized")
    print(f"  Loaded epoch {ckpt.get('epoch', 'N/A')} "
          f"val_loss={ckpt.get('val_loss', ckpt.get('val_cer', 0)):.4f}")

    criterion = torch.nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)
    os.makedirs("checkpoints", exist_ok=True)

    def run_epoch(loader, training, optimizer=None):
        model.train() if training else model.eval()
        total, n = 0, 0
        ctx = torch.enable_grad() if training else torch.no_grad()
        with ctx:
            for images, targets, target_lengths, _ in loader:
                images        = images.to(DEVICE)
                batch_size    = images.size(0)
                if training:
                    optimizer.zero_grad()
                # CRITICAL: log_softmax before CTCLoss
                outputs       = F.log_softmax(model(images), dim=2)
                seq_len       = outputs.size(0)
                input_lengths = torch.full((batch_size,), seq_len, dtype=torch.long)
                loss = criterion(outputs, targets, input_lengths, target_lengths)
                if not torch.isnan(loss) and not torch.isinf(loss):
                    if training:
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 5)
                        optimizer.step()
                    total += loss.item()
                    n     += 1
        return total / max(n, 1)

    def run_phase(num, epochs, lr, freeze_cnn, patience):
        print(f"\n{'='*55}")
        print(f"  PHASE {num} — "
              f"{'CNN FROZEN  (RNN+FC only)' if freeze_cnn else 'FULL MODEL  (all layers)'}"
              f"   LR={lr}")
        print(f"{'='*55}")

        for name, param in model.named_parameters():
            param.requires_grad = not (freeze_cnn and 'cnn' in name)

        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"  Trainable params : {trainable:,}")

        opt     = optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
        sched   = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=3, factor=0.5)
        best    = float('inf')
        counter = 0

        for epoch in range(1, epochs + 1):
            tr = run_epoch(train_loader, True,  opt)
            vl = run_epoch(val_loader,   False, None)
            sched.step(vl)

            if vl < best:
                best    = vl
                counter = 0
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'config':           config,
                    'char_to_idx':      train_dataset.char_to_idx,
                    'idx_to_char':      train_dataset.idx_to_char,
                    'epoch':            epoch,
                    'val_loss':         vl,   # FIXED: renamed from val_cer — this is val loss, not CER%
                }, CHECKPOINT_OUT)
                print(f"  Epoch {epoch:02d}/{epochs}  "
                      f"Train={tr:.4f}  Val={vl:.4f}  <- saved")
            else:
                counter += 1
                print(f"  Epoch {epoch:02d}/{epochs}  "
                      f"Train={tr:.4f}  Val={vl:.4f}  "
                      f"(patience {counter}/{patience})")
                if counter >= patience:
                    print(f"  Early stopping at epoch {epoch}.")
                    break
        return best

    # Phase 1: Freeze CNN
    p1 = run_phase(1, epochs=30, lr=1e-4, freeze_cnn=True,  patience=7)
    # Phase 2: Full model, very low LR
    p2 = run_phase(2, epochs=20, lr=1e-6, freeze_cnn=False, patience=5)

    print(f"\n{'='*55}")
    print(f"IAM fine-tuning complete!")
    print(f"  Phase 1 best val loss : {p1:.4f}")
    print(f"  Phase 2 best val loss : {p2:.4f}")
    print(f"  Saved : {CHECKPOINT_OUT}")
    print(f"\nNext step: collect physical certificate scans")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--train",   action="store_true")
    args = parser.parse_args()

    if not args.prepare and not args.train:
        print("Usage:")
        print("  python IAM_train.py --prepare          # prepare dataset")
        print("  python IAM_train.py --train            # train model")
        print("  python IAM_train.py --prepare --train  # do both")
        sys.exit(0)

    if args.prepare:
        prepare_iam()
    if args.train:
        train_iam()