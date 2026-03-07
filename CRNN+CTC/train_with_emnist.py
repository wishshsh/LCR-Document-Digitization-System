"""
train_with_emnist.py
====================
Fine-tune the CRNN model with EMNIST character data.

FIXES vs old version:
  - Phase 1: CNN FROZEN — only RNN+FC trained (prevents catastrophic forgetting)
  - Phase 2: Full model at 10x lower LR for final polish
  - log_softmax applied before CTCLoss (was missing — caused garbage loss)
  - Loads from best_model.pth (synthetic, 0.12% CER baseline)
  - Saves best_model_emnist.pth only when val improves
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

print("=" * 55)
print("Fine-tuning CRNN with EMNIST dataset")
print("=" * 55)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {DEVICE}")

emnist_dataset = CivilRegistryDataset(
    data_dir='data/train',
    annotations_file='data/emnist_train_annotations.json',
    img_height=64, img_width=512, augment=True
)
# FIXED: mix synthetic data in so the model never forgets multi-word sequences
synth_dataset = CivilRegistryDataset(
    data_dir='data/train',
    annotations_file='data/train_annotations.json',
    img_height=64, img_width=512, augment=True
)
train_dataset = emnist_dataset  # keep reference for char_to_idx / num_chars
mixed_train   = ConcatDataset([emnist_dataset, synth_dataset])
val_dataset = CivilRegistryDataset(
    data_dir='data/val',
    annotations_file='data/val_annotations.json',  # FIXED: was emnist_val — must match real task
    img_height=64, img_width=512, augment=False
)
print(f"EMNIST train  : {len(emnist_dataset)}")
print(f"Synthetic train: {len(synth_dataset)}")
print(f"Mixed train   : {len(mixed_train)}")
print(f"Val           : {len(val_dataset)}")

train_loader = DataLoader(mixed_train, batch_size=32, shuffle=True,
                          num_workers=0, collate_fn=collate_fn)
val_loader   = DataLoader(val_dataset,   batch_size=32, shuffle=False,
                          num_workers=0, collate_fn=collate_fn)

# ── Load best synthetic checkpoint ───────────────────────────
BASE = 'checkpoints/best_model.pth'
if not os.path.exists(BASE):
    print(f"ERROR: {BASE} not found. Run: python train.py")
    sys.exit(1)

ckpt   = torch.load(BASE, map_location=DEVICE, weights_only=False)
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
    print(f"  Note: {len(missing)} layers re-initialized (expected for fc layer)")
print(f"  Loaded epoch {ckpt.get('epoch')} "
      f"(val_loss={ckpt.get('val_loss', ckpt.get('val_cer', 0)):.4f})")

criterion = torch.nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)


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

    # Freeze or unfreeze CNN
    for name, param in model.named_parameters():
        param.requires_grad = not (freeze_cnn and 'cnn' in name)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Trainable params : {trainable:,}")

    opt      = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    sched    = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=3, factor=0.5)
    best     = float('inf')
    counter  = 0

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
            }, 'checkpoints/best_model_emnist.pth')
            print(f"  Epoch {epoch:02d}/{epochs}  Train={tr:.4f}  Val={vl:.4f}  <- saved")
        else:
            counter += 1
            print(f"  Epoch {epoch:02d}/{epochs}  Train={tr:.4f}  Val={vl:.4f}"
                  f"  (patience {counter}/{patience})")
            if counter >= patience:
                print(f"  Early stopping at epoch {epoch}.")
                break
    return best


# ── Phase 1: Freeze CNN — teach RNN+FC to handle EMNIST chars ─
p1_best = run_phase(1, epochs=30, lr=1e-4, freeze_cnn=True, patience=7)

# ── Phase 2: Unfreeze all — gentle full-model polish ──────────
p2_best = run_phase(2, epochs=20, lr=1e-6, freeze_cnn=False, patience=5)

print(f"\n{'='*55}")
print(f"EMNIST fine-tuning complete!")
print(f"  Phase 1 best val loss : {p1_best:.4f}")
print(f"  Phase 2 best val loss : {p2_best:.4f}")
print(f"  Saved : checkpoints/best_model_emnist.pth")
print(f"\nNext step: python IAM_train.py --prepare --train")