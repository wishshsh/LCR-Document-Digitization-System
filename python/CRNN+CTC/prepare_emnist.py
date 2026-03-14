import torchvision
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import json

print("Preparing EMNIST data for CRNN training...")
print("Using 'balanced' split (47 classes — digits, uppercase, selected lowercase)")

# MAX_SAMPLES: how many EMNIST images to use out of 112,800 available.
# 50,000 chosen deliberately:
#   - ~1,064 images per class (47 classes) — enough for solid character recognition
#   - Keeps a healthy ~3:1 ratio vs synthetic data (16,000) in mixed training
#   - Going higher (e.g. full 112,800) would drown out synthetic Filipino-specific
#     patterns since EMNIST would be 88% of the mixed dataset
#   - IAM fine-tuning and physical scans handle remaining handwriting gaps
MAX_SAMPLES = 50000
VAL_RATIO   = 0.10   # 90% train, 10% val — proper percentage split

train_data = torchvision.datasets.EMNIST(
    root='datasets/emnist',
    split='balanced',       # balanced split — already downloaded
    train=True,
    download=False,         # files already exist, skip download
    transform=transforms.ToTensor()
)

# balanced split has 47 classes:
# 0-9 digits, A-Z uppercase, and selected lowercase
# mapping follows EMNIST balanced label order
LABELS = [
    '0','1','2','3','4','5','6','7','8','9',
    'A','B','C','D','E','F','G','H','I','J','K','L','M',
    'N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    'a','b','d','e','f','g','h','n','q','r','t',
]  # 47 classes exactly matching balanced split label indices

os.makedirs('data/train/emnist', exist_ok=True)
os.makedirs('data/val/emnist', exist_ok=True)

annotations_train = []
annotations_val   = []

val_cutoff = int(MAX_SAMPLES * (1 - VAL_RATIO))  # 45,000 train / 5,000 val

print(f"Dataset size : {len(train_data)} images available")
print(f"Using        : {MAX_SAMPLES} ({MAX_SAMPLES/len(train_data)*100:.1f}% of full dataset)")
print(f"Train / Val  : {val_cutoff} / {MAX_SAMPLES - val_cutoff} (90/10 split)")
print("Saving images...")

saved = 0   # count of successfully saved images (skips bad label indices)
for i, (img_tensor, label_idx) in enumerate(train_data):
    if saved >= MAX_SAMPLES:
        break

    # Safety check — skip if label index is out of range for our LABELS list
    if label_idx >= len(LABELS):
        continue

    char = LABELS[label_idx]
    img  = img_tensor.squeeze().numpy()
    img  = (img * 255).astype(np.uint8)

    # EMNIST images are transposed — rotate and flip to correct orientation
    img  = np.rot90(img, k=3)
    img  = np.fliplr(img)

    pil_img = Image.fromarray(img).convert('RGB')
    pil_img = pil_img.resize((512, 64))   # must match IMG_WIDTH=512

    fname = f'emnist_{saved:05d}.jpg'   # sequential filenames based on saved count

    # FIXED: proper percentage-based split (was hardcoded `if i < 5000`)
    if saved < val_cutoff:
        pil_img.save(f'data/train/emnist/{fname}')
        annotations_train.append({'image_path': f'emnist/{fname}', 'text': char})
    else:
        pil_img.save(f'data/val/emnist/{fname}')
        annotations_val.append({'image_path': f'emnist/{fname}', 'text': char})

    saved += 1
    if saved % 5000 == 0:
        print(f"  Processed {saved}/{MAX_SAMPLES} images...")

with open('data/emnist_train_annotations.json', 'w') as f:
    json.dump(annotations_train, f, indent=2)
with open('data/emnist_val_annotations.json', 'w') as f:
    json.dump(annotations_val, f, indent=2)

print(f"\nDone!")
print(f"  Train : {len(annotations_train)} images  (~{len(annotations_train)//47} per class)")
print(f"  Val   : {len(annotations_val)} images")
print(f"  Total : {len(annotations_train) + len(annotations_val)} / {len(train_data)} used")
print(f"  Labels: {sorted(set(a['text'] for a in annotations_train))}")
print(f"\nClass coverage: {len(set(a['text'] for a in annotations_train))}/47 classes in train")
print("\nNext step: python train_with_emnist.py")