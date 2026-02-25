import torchvision
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import json

print("Preparing EMNIST data for CRNN training...")

train_data = torchvision.datasets.EMNIST(
    root='datasets/emnist',
    split='byclass',
    train=True,
    download=False,
    transform=transforms.ToTensor()
)

LABELS = list('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')

os.makedirs('data/train/emnist', exist_ok=True)
os.makedirs('data/val/emnist', exist_ok=True)

annotations_train = []
annotations_val = []

print("Saving images...")
for i, (img_tensor, label_idx) in enumerate(train_data):
    if i >= 6000:
        break
    char = LABELS[label_idx]
    img = img_tensor.squeeze().numpy()
    img = (img * 255).astype(np.uint8)
    img = np.rot90(img, k=3)
    img = np.fliplr(img)
    pil_img = Image.fromarray(img).convert('RGB')
    pil_img = pil_img.resize((200, 64))
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

print(f"Done! Train: {len(annotations_train)}, Val: {len(annotations_val)}")
print("Next step: python train_with_emnist.py")
