from datasets import load_dataset
from pathlib import Path
import json

print("Downloading FUNSD+ from Hugging Face...")
dataset = load_dataset("konfuzio/funsd_plus")

Path("data/funsd_plus").mkdir(parents=True, exist_ok=True)

# Save train split
train_data = []
for item in dataset["train"]:
    train_data.append({
        "words":  item["words"],
        "labels": item["labels"],
        "bboxes": item["bboxes"],
    })

with open("data/funsd_plus/train.json", "w") as f:
    json.dump(train_data, f)

# Save test split  
test_data = []
for item in dataset["test"]:
    test_data.append({
        "words":  item["words"],
        "labels": item["labels"],
        "bboxes": item["bboxes"],
    })

with open("data/funsd_plus/test.json", "w") as f:
    json.dump(test_data, f)

print(f"Train: {len(train_data)} samples → data/funsd_plus/train.json")
print(f"Test:  {len(test_data)} samples  → data/funsd_plus/test.json")
print("Done!")