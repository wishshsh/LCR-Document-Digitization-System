"""
finetune.py
===========
Fine-tune CRNN+CTC on generated civil registry form crops.

Loads best_model_final.pth (pretrained), continues training on
actual_annotations.json + train_annotations.json.

Usage:
    python finetune.py

Output:
    checkpoints/best_model_v2.pth
"""

import os
import sys
import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, ConcatDataset

sys.path.append('.')
from crnn_model import get_crnn_model
from dataset import CivilRegistryDataset, collate_fn

# ── Config ────────────────────────────────────────────────────
CHECKPOINT_IN  = "checkpoints/best_model_final.pth"
CHECKPOINT_OUT = "checkpoints/best_model_v2.pth"

ACTUAL_ANN = "data/actual_annotations.json"  # real scanned forms
SYNTH_ANN  = "data/train_annotations.json"   # synthetic / train split
VAL_ANN    = "data/val_annotations.json"     # validation set

IMG_HEIGHT = 64
IMG_WIDTH  = 512
BATCH_SIZE = 32

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Phase settings ────────────────────────────────────────────
PHASES = [
    # (name, epochs, lr, freeze_cnn, patience)
    ("Phase 1 — CNN frozen,   adapt to form crops", 20, 1e-4, True,  5),
    ("Phase 2 — Full model,   low LR polish",        15, 1e-5, False, 4),
]

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Fine-tuning CRNN+CTC on civil registry form crops")
    print("=" * 60)
    print(f"  Device      : {DEVICE}")
    print(f"  Checkpoint  : {CHECKPOINT_IN}")

    # ── Check required files ──────────────────────────────────
    for f in [CHECKPOINT_IN, VAL_ANN]:
        if not os.path.exists(f):
            print(f"ERROR: {f} not found.")
            sys.exit(1)

    # ── Datasets ──────────────────────────────────────────────
    datasets_to_merge = []

    # 1. Actual scanned forms (highest priority — real data)
    if os.path.exists(ACTUAL_ANN):
        actual_dataset = CivilRegistryDataset(
            data_dir=".", annotations_file=ACTUAL_ANN,
            img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=True
        )
        datasets_to_merge.append(actual_dataset)
        print(f"  Actual crops: {len(actual_dataset)}  (real scanned forms)")
    else:
        print(f"  [!] {ACTUAL_ANN} not found — run extract_actual_data.py first")

    # 2. Fully synthetic — keep so model doesn't forget basic characters
    if os.path.exists(SYNTH_ANN):
        synth_dataset = CivilRegistryDataset(
            data_dir="data/train", annotations_file=SYNTH_ANN,
            img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=True
        )
        datasets_to_merge.append(synth_dataset)
        print(f"  Synth crops : {len(synth_dataset)}  (fully synthetic)")

    if not datasets_to_merge:
        print("ERROR: No training data found. Run extract_actual_data.py first.")
        sys.exit(1)

    val_dataset = CivilRegistryDataset(
        data_dir="data/val", annotations_file=VAL_ANN,
        img_height=IMG_HEIGHT, img_width=IMG_WIDTH, augment=False
    )

    train_dataset = ConcatDataset(datasets_to_merge) if len(datasets_to_merge) > 1 else datasets_to_merge[0]
    print(f"  Total train : {len(train_dataset)}")
    print(f"  Val         : {len(val_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=0, collate_fn=collate_fn)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=0, collate_fn=collate_fn)

    # ── Load checkpoint ───────────────────────────────────────
    print(f"\n  Loading {CHECKPOINT_IN}...")
    ckpt   = torch.load(CHECKPOINT_IN, map_location=DEVICE, weights_only=False)
    config = ckpt.get('config', {})

    ref_dataset = datasets_to_merge[0]
    model = get_crnn_model(
        model_type      = config.get('model_type', 'standard'),
        img_height      = config.get('img_height', 64),
        num_chars       = ref_dataset.num_chars,
        hidden_size     = config.get('hidden_size', 128),
        num_lstm_layers = config.get('num_lstm_layers', 1),
    ).to(DEVICE)

    missing, _ = model.load_state_dict(ckpt['model_state_dict'], strict=False)
    if missing:
        print(f"  Note: {len(missing)} layers re-initialized (expected if vocab size changed)")
    print(f"  Loaded epoch {ckpt.get('epoch','?')}  "
          f"val_loss={ckpt.get('val_loss', ckpt.get('val_cer', 0)):.4f}")

    criterion = torch.nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)
    os.makedirs("checkpoints", exist_ok=True)

    # ── Train/val loop ────────────────────────────────────────
    def run_epoch(loader, training, optimizer=None):
        model.train() if training else model.eval()
        total, n = 0, 0
        ctx = torch.enable_grad() if training else torch.no_grad()
        with ctx:
            for images, targets, target_lengths, _ in loader:
                images     = images.to(DEVICE)
                batch_size = images.size(0)
                if training:
                    optimizer.zero_grad()
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

    best_overall = float('inf')

    for phase_name, epochs, lr, freeze_cnn, patience in PHASES:
        print(f"\n{'='*60}")
        print(f"  {phase_name}   LR={lr}")
        print(f"{'='*60}")

        for name, param in model.named_parameters():
            param.requires_grad = not (freeze_cnn and 'cnn' in name)

        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"  Trainable params : {trainable:,}")

        opt   = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
        sched = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=2, factor=0.5)
        best  = float('inf')
        wait  = 0

        for epoch in range(1, epochs + 1):
            tr = run_epoch(train_loader, True,  opt)
            vl = run_epoch(val_loader,   False, None)
            sched.step(vl)

            if vl < best:
                best = vl
                wait = 0
                if vl < best_overall:
                    best_overall = vl
                    torch.save({
                        'model_state_dict': model.state_dict(),
                        'config':           config,
                        'char_to_idx':      ref_dataset.char_to_idx,
                        'idx_to_char':      ref_dataset.idx_to_char,
                        'epoch':            epoch,
                        'val_loss':         vl,
                    }, CHECKPOINT_OUT)
                print(f"  Epoch {epoch:02d}/{epochs}  Train={tr:.4f}  Val={vl:.4f}  <- saved")
            else:
                wait += 1
                print(f"  Epoch {epoch:02d}/{epochs}  Train={tr:.4f}  Val={vl:.4f}  (patience {wait}/{patience})")
                if wait >= patience:
                    print(f"  Early stopping.")
                    break

    print(f"\n{'='*60}")
    print(f"  Fine-tuning complete!")
    print(f"  Best val loss : {best_overall:.4f}")
    print(f"  Saved         : {CHECKPOINT_OUT}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()