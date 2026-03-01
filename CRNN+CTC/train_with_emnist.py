"""
train_with_emnist.py
====================
Fine-tune the CRNN model with EMNIST character data.

FIXES:
  - img_width changed from 200 -> 400 (must match train.py and fix_data.py)
  - input_lengths now uses model output size (not hardcoded 49)
  - Hardcoded 49 was for 200px images; correct value for 400px is ~98
"""

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import sys

sys.path.append('.')
from crnn_model import CRNN_CivilRegistry as CRNN
from dataset import CivilRegistryDataset, collate_fn

print("=" * 50)
print("Fine-tuning CRNN with EMNIST dataset")
print("=" * 50)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {DEVICE}")

# FIXED: img_width=400 matches train.py and fix_data.py
train_dataset = CivilRegistryDataset(
    data_dir='data/train',
    annotations_file='data/emnist_train_annotations.json',
    img_height=64,
    img_width=400,      # FIXED was 200
    augment=True
)
val_dataset = CivilRegistryDataset(
    data_dir='data/val',
    annotations_file='data/emnist_val_annotations.json',
    img_height=64,
    img_width=400,      # FIXED was 200
    augment=False
)

print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True,
                          num_workers=0, collate_fn=collate_fn)
val_loader   = DataLoader(val_dataset,   batch_size=32, shuffle=False,
                          num_workers=0, collate_fn=collate_fn)

model      = CRNN(num_chars=train_dataset.num_chars).to(DEVICE)
checkpoint = torch.load('checkpoints/best_model.pth', map_location=DEVICE,
                        weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
print(f"Loaded existing model — fine-tuning with EMNIST (num_chars={train_dataset.num_chars})")

criterion = torch.nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)
optimizer = optim.Adam(model.parameters(), lr=0.0001)

best_loss = float('inf')
EPOCHS    = 30

for epoch in range(1, EPOCHS + 1):
    model.train()
    train_loss = 0

    for images, targets, target_lengths, texts in train_loader:
        images     = images.to(DEVICE)
        batch_size = images.size(0)

        optimizer.zero_grad()
        outputs = model(images)

        # FIXED: use actual output sequence length, not hardcoded 49
        # outputs shape: [seq_len, batch, num_chars]
        seq_len      = outputs.size(0)
        input_lengths = torch.full((batch_size,), seq_len, dtype=torch.long)

        loss = criterion(outputs, targets, input_lengths, target_lengths)
        if not torch.isnan(loss):
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5)
            optimizer.step()
            train_loss += loss.item()

    avg_loss = train_loss / len(train_loader)

    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save({'model_state_dict': model.state_dict()},
                   'checkpoints/best_model_emnist.pth')
        print(f"Epoch {epoch}/{EPOCHS} - Loss: {avg_loss:.4f} - Saved best!")
    else:
        print(f"Epoch {epoch}/{EPOCHS} - Loss: {avg_loss:.4f}")

print("EMNIST fine-tuning complete!")
print("Best model: checkpoints/best_model_emnist.pth")
