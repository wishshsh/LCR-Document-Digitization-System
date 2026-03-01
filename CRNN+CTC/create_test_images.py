import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('test_images', exist_ok=True)

def load_font(size=20):
    """Same font loader as fix_data.py — tries multiple paths."""
    for fp in [
        'arial.ttf', 'Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/arial.ttf',
    ]:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    print("WARNING: Could not load Arial/DejaVu font. Using default — predictions may be inaccurate.")
    return ImageFont.load_default()

def create_image(text, filename):
    """Render text exactly the same way as fix_data.py training images."""
    img  = Image.new('RGB', (512, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = load_font(20)

    bbox = draw.textbbox((0, 0), text, font=font)
    x = max((512 - (bbox[2] - bbox[0])) // 2, 2)
    y = max((64  - (bbox[3] - bbox[1])) // 2, 2)
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    img.save(filename)
    print(f'Created: {filename}')

# ── Test samples ──────────────────────────────────────────────
create_image('Juan Dela Cruz',                  'test_images/demo.jpg')
create_image('Juan Dela Cruz',                  'test_images/name1.jpg')
create_image('01/15/1990',                      'test_images/date1.jpg')
create_image('Tarlac City',                     'test_images/place1.jpg')
create_image('Maria Santos',                    'test_images/form1a_sample.jpg')

# ── Extra test cases (names, dates, addresses) ────────────────
create_image('Jose Dela Cruz Jr.',              'test_images/name2.jpg')
create_image('Ana Marie Reyes',                 'test_images/name3.jpg')
create_image('03/22/1985',                      'test_images/date2.jpg')
create_image('07/04/2000',                      'test_images/date3.jpg')
create_image('Brgy. San Jose, Capas, Tarlac',   'test_images/place2.jpg')
create_image('78 MacArthur Hwy., Tarlac City',  'test_images/place3.jpg')

print('\nAll test images created!')
print('Font used matches training data — predictions should be accurate.')
