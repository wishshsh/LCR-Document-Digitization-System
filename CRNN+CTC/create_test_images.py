import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('test_images', exist_ok=True)

def create_image(text, filename):
    img = Image.new('RGB', (400, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 20)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = max((400 - (bbox[2] - bbox[0])) // 2, 2)
    y = max((64  - (bbox[3] - bbox[1])) // 2, 2)
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    img.save(filename)
    print(f'Created: {filename}')

create_image('Juan Dela Cruz',  'test_images/sample_name.jpg')
create_image('Juan Dela Cruz',  'test_images/name1.jpg')
create_image('01/15/1990',      'test_images/date1.jpg')
create_image('Tarlac City',     'test_images/place1.jpg')
create_image('Maria Santos',    'test_images/form1a_sample.jpg')

print('All test images created!')