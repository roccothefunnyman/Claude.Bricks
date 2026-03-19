"""
Generate synthetic facade training images for Scenario 1.

Each class gets 20 images with visually distinct patterns so a
Random Forest on 64x64 RGB pixels can separate them. These are
placeholder images for pipeline testing -- replace with real
facade photos for production accuracy.

Run once:  python generate_samples.py
"""
import os
import random
from PIL import Image, ImageDraw

random.seed(42)
BASE = os.path.dirname(os.path.abspath(__file__))
IMG_SIZE = (128, 128)
COUNT = 20


def _save(img, label, idx):
    path = os.path.join(BASE, label, f"{label}_{idx:03d}.png")
    img.save(path)


def _rand(base, spread=30):
    return max(0, min(255, base + random.randint(-spread, spread)))


def generate_historic(n):
    """Warm stone tones, arched windows, ornate horizontal bands."""
    for i in range(n):
        img = Image.new("RGB", IMG_SIZE, (_rand(210), _rand(190), _rand(160)))
        d = ImageDraw.Draw(img)
        # Horizontal stone bands
        for y in range(0, IMG_SIZE[1], random.randint(16, 24)):
            c = (_rand(180), _rand(160), _rand(130))
            d.line([(0, y), (IMG_SIZE[0], y)], fill=c, width=2)
        # Arched windows
        for col in range(20, IMG_SIZE[0] - 20, 35):
            for row in range(20, IMG_SIZE[1] - 30, 45):
                wc = (_rand(80), _rand(70), _rand(50))
                d.rectangle([col, row + 8, col + 18, row + 30], fill=wc)
                d.arc([col, row, col + 18, row + 16], 0, 360, fill=wc, width=2)
        # Cornice line
        d.rectangle([0, 0, IMG_SIZE[0], 8], fill=(_rand(160), _rand(140), _rand(110)))
        _save(img, "historic", i)


def generate_modern(n):
    """Cool blue/grey tones, large glass panels, clean grid."""
    for i in range(n):
        bg = (_rand(200, 20), _rand(210, 20), _rand(220, 20))
        img = Image.new("RGB", IMG_SIZE, bg)
        d = ImageDraw.Draw(img)
        # Glass curtain wall grid
        spacing = random.choice([24, 32])
        for x in range(0, IMG_SIZE[0], spacing):
            for y in range(0, IMG_SIZE[1], spacing):
                glass = (_rand(140, 40), _rand(180, 40), _rand(220, 40))
                d.rectangle([x + 2, y + 2, x + spacing - 2, y + spacing - 2], fill=glass)
        # Steel mullions
        for x in range(0, IMG_SIZE[0], spacing):
            d.line([(x, 0), (x, IMG_SIZE[1])], fill=(100, 100, 110), width=2)
        for y in range(0, IMG_SIZE[1], spacing):
            d.line([(0, y), (IMG_SIZE[0], y)], fill=(100, 100, 110), width=2)
        _save(img, "modern", i)


def generate_industrial(n):
    """Dark muted tones, corrugated texture, few small windows."""
    for i in range(n):
        img = Image.new("RGB", IMG_SIZE, (_rand(100, 20), _rand(95, 20), _rand(90, 20)))
        d = ImageDraw.Draw(img)
        # Corrugated vertical lines
        stripe_w = random.randint(6, 10)
        for x in range(0, IMG_SIZE[0], stripe_w):
            shade = _rand(120, 25)
            d.rectangle([x, 0, x + stripe_w // 2, IMG_SIZE[1]], fill=(shade, shade, shade))
        # Small windows (sparse)
        for _ in range(random.randint(2, 4)):
            wx = random.randint(10, IMG_SIZE[0] - 30)
            wy = random.randint(30, IMG_SIZE[1] - 30)
            d.rectangle([wx, wy, wx + 16, wy + 12], fill=(_rand(160), _rand(170), _rand(180)))
        # Roofline / loading bay
        d.rectangle([0, IMG_SIZE[1] - 20, IMG_SIZE[0], IMG_SIZE[1]],
                     fill=(_rand(70), _rand(70), _rand(70)))
        _save(img, "industrial", i)


def generate_commercial(n):
    """Bright accent colors, storefront windows, signage bands."""
    for i in range(n):
        img = Image.new("RGB", IMG_SIZE, (_rand(230, 15), _rand(225, 15), _rand(215, 15)))
        d = ImageDraw.Draw(img)
        # Signage band at top
        accent = (random.randint(180, 255), random.randint(40, 120), random.randint(30, 80))
        d.rectangle([0, 0, IMG_SIZE[0], 22], fill=accent)
        # Large storefront windows
        for col in range(8, IMG_SIZE[0] - 8, 40):
            d.rectangle([col, 30, col + 32, IMG_SIZE[1] - 20],
                        fill=(_rand(170, 30), _rand(200, 30), _rand(220, 30)))
            d.rectangle([col, 30, col + 32, IMG_SIZE[1] - 20], outline=(60, 60, 60), width=2)
        # Ground strip
        d.rectangle([0, IMG_SIZE[1] - 14, IMG_SIZE[0], IMG_SIZE[1]],
                     fill=(_rand(140), _rand(130), _rand(120)))
        _save(img, "commercial", i)


def generate_residential(n):
    """Muted warm tones, regular small windows, pitched roof indication."""
    for i in range(n):
        wall = (_rand(200, 20), _rand(185, 20), _rand(170, 20))
        img = Image.new("RGB", IMG_SIZE, wall)
        d = ImageDraw.Draw(img)
        # Regular window grid
        for col in range(15, IMG_SIZE[0] - 15, 30):
            for row in range(25, IMG_SIZE[1] - 30, 32):
                d.rectangle([col, row, col + 14, row + 20],
                            fill=(_rand(130, 30), _rand(160, 30), _rand(190, 30)))
                # Window frame
                d.rectangle([col, row, col + 14, row + 20], outline=wall, width=1)
                # Sill
                d.line([(col - 2, row + 20), (col + 16, row + 20)], fill=(160, 150, 140), width=2)
        # Pitched roof triangle
        roof_c = (_rand(130, 20), _rand(70, 20), _rand(60, 20))
        d.polygon([(0, 18), (IMG_SIZE[0] // 2, 0), (IMG_SIZE[0], 18)], fill=roof_c)
        # Door
        dx = IMG_SIZE[0] // 2 - 8
        d.rectangle([dx, IMG_SIZE[1] - 35, dx + 16, IMG_SIZE[1]],
                    fill=(_rand(100, 30), _rand(60, 20), _rand(40, 15)))
        _save(img, "residential", i)


if __name__ == "__main__":
    generate_historic(COUNT)
    generate_modern(COUNT)
    generate_industrial(COUNT)
    generate_commercial(COUNT)
    generate_residential(COUNT)
    total = COUNT * 5
    print(f"Generated {total} synthetic facade images ({COUNT} per class)")
    for label in ["historic", "modern", "industrial", "commercial", "residential"]:
        count = len([f for f in os.listdir(os.path.join(BASE, label)) if f.endswith(".png")])
        print(f"  {label}/: {count} images")
