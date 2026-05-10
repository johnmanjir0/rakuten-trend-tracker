import PIL
from PIL import Image, ImageDraw, ImageFont
import moviepy
print(f"Pillow version: {PIL.__version__}")
print(f"MoviePy version: {moviepy.__version__}")

# 画像生成テスト
img = Image.new('RGB', (500, 500), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10, 10), "Hello Rakuten ROOM", fill=(255, 255, 0))
img.save('test_image.png')
print("Test image saved as test_image.png")
