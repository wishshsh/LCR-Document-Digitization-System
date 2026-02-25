import torchvision
import torchvision.transforms as transforms

print("Loading EMNIST dataset...")

train_data = torchvision.datasets.EMNIST(
    root='datasets/emnist',
    split='byclass',
    train=True,
    download=False,
    transform=transforms.ToTensor()
)

print(f"Training samples: {len(train_data)}")
print("EMNIST loaded successfully!")
