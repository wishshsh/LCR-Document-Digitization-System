import torchvision
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import json

print("Preparing EMNIST data for CRNN training...")
print("Using 'balanced' split (47 classes — digits, uppercase, selected lowercase)")

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

print(f"Dataset size: {len(train_data)} images")
print("Saving images...")

for i, (img_tensor, label_idx) in enumerate(train_data):
    if i >= 6000:
        break

    # Safety check — skip if label out of range
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

    fname = f'emnist_{i:05d}.jpg'

    if i < 5000:
        pil_img.save(f'data/train/emnist/{fname}')
        annotations_train.append({'image_path': f'emnist/{fname}', 'text': char})
    else:
        pil_img.save(f'data/val/emnist/{fname}')
        annotations_val.append({'image_path': f'emnist/{fname}', 'text': char})

    if i % 1000 == 0:
        print(f"  Processed {i}/6000 images...")

with open('data/emnist_train_annotations.json', 'w') as f:
    json.dump(annotations_train, f, indent=2)
with open('data/emnist_val_annotations.json', 'w') as f:
    json.dump(annotations_val, f, indent=2)

print(f"\nDone!")
print(f"  Train : {len(annotations_train)} images")
print(f"  Val   : {len(annotations_val)} images")
print(f"  Labels: {sorted(set(a['text'] for a in annotations_train))}")
print("\nNext step: python train_with_emnist.py")