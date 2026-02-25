import json, os

for split in ['train', 'val']:
    with open(f'data/{split}_annotations.json') as f:
        data = json.load(f)
    fixed = []
    for d in data:
        filename = os.path.basename(d['image'])
        folder = 'form1a' if 'form1a' in d['image'] else 'form2a'
        fixed.append({'image_path': f'{folder}/{filename}', 'text': d['label']})
    with open(f'data/{split}_annotations.json', 'w') as f:
        json.dump(fixed, f, indent=2)
    print(f'{split} fixed! Total:', len(fixed))

print('Done!')