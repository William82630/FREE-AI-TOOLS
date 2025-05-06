from PIL import Image, ImageDraw
import os

# Create a directory for static files if it doesn't exist
os.makedirs('static', exist_ok=True)

# Create a 16x16 image with a blue background
img = Image.new('RGB', (16, 16), color=(0, 64, 128))
draw = ImageDraw.Draw(img)

# Draw a simple 'F' letter in white
draw.rectangle((3, 3, 6, 13), fill=(255, 255, 255))
draw.rectangle((3, 3, 12, 6), fill=(255, 255, 255))
draw.rectangle((3, 8, 10, 10), fill=(255, 255, 255))

# Save as ICO
img.save('static/favicon.ico', format='ICO')

print("Favicon created successfully at static/favicon.ico")
