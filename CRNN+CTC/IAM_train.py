"""
IAM_train.py
============
Fine-tune the CRNN model using the IAM Handwriting Word Database.
Builds on top of EMNIST-trained model (best_model_emnist.pth).

DATASET:
  Download from: https://www.kaggle.com/datasets/nibinv23/iam-handwriting-word-database
  Expected structure after download:
    data/IAM/
      words/           ← word image folders (a01, a02, ...)
      words.txt        ← annotation file

STEP ORDER:
  1. python IAM_train.py --prepare   ← converts IAM → annotations JSON
  2. python IAM_train.py --train     ← trains the CRNN model
  3. python IAM_train.py --prepare --train  ← do both at once
"""

import os
import sys
import json
import argparse
import random
from pathlib import Path

import torch
import torch.optim as optim
from torch.utils.data import DataLoader

sys.path.append('.')
from crnn_model import CRNN_CivilRegistry as CRNN
from dataset import CivilRegistryDataset, collate_fn

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
IAM_ROOT = "data/IAM/iam_words"              # root folder of IAM dataset
IAM_WORDS_TXT   = f"{IAM_ROOT}/words.txt"  # annotation file from IAM
IAM_WORDS_DIR   = f"{IAM_ROOT}/words"      # word images folder

TRAIN_ANN       = "data/iam_train_annotations.json"
VAL_ANN         = "data/iam_val_annotations.json"
TRAIN_IMG_DIR   = "data/train/iam"
VAL_IMG_DIR     = "data/val/iam"

IMG_HEIGHT      = 64
IMG_WIDTH       = 400
BATCH_SIZE      = 32
EPOCHS          = 50
LR              = 0.0001
VAL_SPLIT       = 0.1
MAX_SAMPLES     = 50000

CHECKPOINT_IN   = "checkpoints/best_model_emnist.pth"
CHECKPOINT_OUT  = "checkpoints/best_model_iam.pth"

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
        print("Expected files:")
        print("  data/IAM/words.txt")
        print("  data/IAM/words/")
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
                img = img.resize((IMG_WIDTH, IMG_HEIGHT))
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
    with open(VAL_ANN, "w") as f:
        json.dump(val_ann, f, indent=2)

    print(f"\n  ✓ Train annotations → {TRAIN_ANN} ({len(train_ann)} entries)")
    print(f"  ✓ Val annotations   → {VAL_ANN} ({len(val_ann)} entries)")
    print("\n  Done! Now run: python IAM_train.py --train")


# ─────────────────────────────────────────────
#  STEP 2 — TRAIN
# ─────────────────────────────────────────────
def train_iam():
    print("\n" + "=" * 50)
    print("STEP 2 — Training CRNN with IAM dataset")
    print("=" * 50)
    print(f"  Device : {DEVICE}")

    for ann_file in [TRAIN_ANN, VAL_ANN]:
        if not os.path.exists(ann_file):
            print(f"ERROR: {ann_file} not found! Run --prepare first.")
            sys.exit(1)

    train_dataset = CivilRegistryDataset(
        data_dir="data/train",
        annotations_file=TRAIN_ANN,
        img_height=IMG_HEIGHT,
        img_width=IMG_WIDTH,
        augment=True
    )
    val_dataset = CivilRegistryDataset(
        data_dir="data/val",
        annotations_file=VAL_ANN,
        img_height=IMG_HEIGHT,
        img_width=IMG_WIDTH,
        augment=False
    )

    print(f"  Train samples : {len(train_dataset)}")
    print(f"  Val samples   : {len(val_dataset)}")
    print(f"  Num chars     : {train_dataset.num_chars}")

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE,
        shuffle=True, num_workers=0, collate_fn=collate_fn
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE,
        shuffle=False, num_workers=0, collate_fn=collate_fn
    )

    model = CRNN(num_chars=train_dataset.num_chars).to(DEVICE)

    if os.path.exists(CHECKPOINT_IN):
        checkpoint = torch.load(CHECKPOINT_IN, map_location=DEVICE, weights_only=False)
        try:
            model.load_state_dict(checkpoint["model_state_dict"])
            print(f"  ✓ Loaded checkpoint: {CHECKPOINT_IN}")
        except Exception as e:
            print(f"  ⚠ Could not load checkpoint ({e}) — training from scratch")
    else:
        print(f"  ⚠ No checkpoint at {CHECKPOINT_IN} — training from scratch")

    os.makedirs("checkpoints", exist_ok=True)

    criterion = torch.nn.CTCLoss(blank=0, reduction="mean", zero_infinity=True)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5, verbose=True
    )

    best_val_loss = float("inf")
    print(f"\n  Starting training for {EPOCHS} epochs...\n")

    for epoch in range(1, EPOCHS + 1):
        # ── Train ──────────────────────────────────
        model.train()
        train_loss    = 0
        train_batches = 0

        for images, targets, target_lengths, texts in train_loader:
            images     = images.to(DEVICE)
            batch_size = images.size(0)
            optimizer.zero_grad()
            outputs       = model(images)
            seq_len       = outputs.size(0)
            input_lengths = torch.full((batch_size,), seq_len, dtype=torch.long)
            loss = criterion(outputs, targets, input_lengths, target_lengths)
            if not torch.isnan(loss) and not torch.isinf(loss):
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5)
                optimizer.step()
                train_loss    += loss.item()
                train_batches += 1

        avg_train_loss = train_loss / max(train_batches, 1)

        # ── Validate ───────────────────────────────
        model.eval()
        val_loss    = 0
        val_batches = 0

        with torch.no_grad():
            for images, targets, target_lengths, texts in val_loader:
                images        = images.to(DEVICE)
                batch_size    = images.size(0)
                outputs       = model(images)
                seq_len       = outputs.size(0)
                input_lengths = torch.full((batch_size,), seq_len, dtype=torch.long)
                loss = criterion(outputs, targets, input_lengths, target_lengths)
                if not torch.isnan(loss) and not torch.isinf(loss):
                    val_loss    += loss.item()
                    val_batches += 1

        avg_val_loss = val_loss / max(val_batches, 1)
        scheduler.step(avg_val_loss)

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({"model_state_dict": model.state_dict()}, CHECKPOINT_OUT)
            print(f"  Epoch {epoch:3d}/{EPOCHS} | Train: {avg_train_loss:.4f} | Val: {avg_val_loss:.4f} ← BEST saved!")
        else:
            print(f"  Epoch {epoch:3d}/{EPOCHS} | Train: {avg_train_loss:.4f} | Val: {avg_val_loss:.4f}")

    print(f"\n  ✓ Training complete!")
    print(f"  ✓ Best model saved → {CHECKPOINT_OUT}")
    print(f"  Next step: fine-tune on Filipino names/addresses")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IAM Handwriting CRNN Trainer")
    parser.add_argument("--prepare", action="store_true", help="Parse IAM dataset and create annotation JSONs")
    parser.add_argument("--train",   action="store_true", help="Train CRNN model on IAM data")
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