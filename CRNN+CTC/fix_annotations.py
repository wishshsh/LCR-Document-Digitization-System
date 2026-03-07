import json, os

# Maps any image path to its correct form subfolder.
# FIXED: was only handling form1a/form2a — missed form3a and form90.
def detect_folder(image_path):
    for form in ['form1a', 'form2a', 'form3a', 'form90']:
        if form in image_path:
            return form
    return 'form1a'   # safe fallback

for split in ['train', 'val']:
    ann_file = f'data/{split}_annotations.json'
    if not os.path.exists(ann_file):
        print(f'SKIP: {ann_file} not found')
        continue

    with open(ann_file) as f:
        data = json.load(f)

    fixed = []
    skipped = 0
    for d in data:
        # Support both old key names ('image'/'label') and new ('image_path'/'text')
        image_val = d.get('image') or d.get('image_path', '')
        text_val  = d.get('label') or d.get('text', '')

        if not image_val or not text_val:
            skipped += 1
            continue

        filename = os.path.basename(image_val)
        folder   = detect_folder(image_val)
        fixed.append({'image_path': f'{folder}/{filename}', 'text': text_val})

    with open(ann_file, 'w') as f:
        json.dump(fixed, f, indent=2)

    print(f'{split}: {len(fixed)} fixed, {skipped} skipped')

print('Done!')