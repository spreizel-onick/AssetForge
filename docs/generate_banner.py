"""Generate GitHub banner for AssetForge."""
from PIL import Image, ImageDraw, ImageFont
import math

WIDTH, HEIGHT = 1280, 640

img = Image.new("RGB", (WIDTH, HEIGHT), "#0f0f1a")
draw = ImageDraw.Draw(img)

# Background gradient effect with geometric shapes
for i in range(80):
    import random
    random.seed(42 + i)
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    size = random.randint(2, 6)
    alpha = random.randint(20, 60)
    color = (255, 99, 99, alpha) if i % 3 == 0 else (100, 100, 140, alpha)
    draw.ellipse([x-size, y-size, x+size, y+size], fill=color[:3])

# Accent gradient bar at top
for x in range(WIDTH):
    r = int(255 - (x / WIDTH) * 100)
    g = int(60 + (x / WIDTH) * 40)
    b = int(80 + (x / WIDTH) * 60)
    for y in range(4):
        draw.point((x, y), fill=(r, g, b))

# Subtle grid pattern
for x in range(0, WIDTH, 40):
    draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 8), width=1)
for y in range(0, HEIGHT, 40):
    draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 8), width=1)

# Decorative hex shapes
def draw_hex(draw, cx, cy, r, color, width=2):
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
    points.append(points[0])
    draw.line(points, fill=color, width=width)

draw_hex(draw, 180, 160, 80, (255, 99, 99))
draw_hex(draw, 180, 160, 60, (255, 130, 130))
draw_hex(draw, 1100, 480, 70, (255, 99, 99))
draw_hex(draw, 1100, 480, 50, (255, 130, 130))
draw_hex(draw, 950, 120, 40, (100, 100, 180))
draw_hex(draw, 300, 520, 35, (100, 100, 180))

# Anvil icon (simplified forge symbol)
anvil_x, anvil_y = 640, 200
# Anvil top
draw.rounded_rectangle([anvil_x-90, anvil_y-30, anvil_x+90, anvil_y+10], radius=8, fill=(255, 99, 99))
# Anvil body
draw.polygon([
    (anvil_x-70, anvil_y+10),
    (anvil_x+70, anvil_y+10),
    (anvil_x+50, anvil_y+50),
    (anvil_x-50, anvil_y+50),
], fill=(220, 70, 70))
# Anvil base
draw.rounded_rectangle([anvil_x-60, anvil_y+50, anvil_x+60, anvil_y+70], radius=4, fill=(180, 50, 50))
# Spark effects
sparks = [(anvil_x-40, anvil_y-50), (anvil_x+30, anvil_y-60), (anvil_x+60, anvil_y-40),
          (anvil_x-60, anvil_y-35), (anvil_x+10, anvil_y-70), (anvil_x-20, anvil_y-65)]
for sx, sy in sparks:
    draw.ellipse([sx-3, sy-3, sx+3, sy+3], fill=(255, 200, 100))
    draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(255, 255, 200))

# Title
try:
    font_large = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 72)
    font_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 72)
    font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 28)
    font_tags = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
    font_stats = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
except:
    font_large = ImageFont.load_default()
    font_bold = font_large
    font_sub = font_large
    font_tags = font_large
    font_stats = font_large

# "Asset" in white, "Forge" in accent
title_y = 300
asset_bbox = draw.textbbox((0, 0), "Asset", font=font_large)
forge_bbox = draw.textbbox((0, 0), "Forge", font=font_bold)
total_w = (asset_bbox[2] - asset_bbox[0]) + (forge_bbox[2] - forge_bbox[0]) + 5
start_x = (WIDTH - total_w) // 2

draw.text((start_x, title_y), "Asset", fill=(240, 240, 250), font=font_large)
draw.text((start_x + asset_bbox[2] - asset_bbox[0] + 5, title_y), "Forge", fill=(255, 99, 99), font=font_bold)

# Subtitle
subtitle = "Local Asset Generator for Developers"
sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
sub_w = sub_bbox[2] - sub_bbox[0]
draw.text(((WIDTH - sub_w) // 2, title_y + 90), subtitle, fill=(160, 160, 180), font=font_sub)

# Tag pills
tags = ["45 Generators", "5 Presets", "5 Categories", "Dark & Light Mode", "Zero Dependencies"]
tag_y = title_y + 150
total_tag_w = 0
tag_widths = []
for tag in tags:
    bbox = draw.textbbox((0, 0), tag, font=font_tags)
    w = bbox[2] - bbox[0] + 24
    tag_widths.append(w)
    total_tag_w += w
total_tag_w += (len(tags) - 1) * 12  # gaps

tx = (WIDTH - total_tag_w) // 2
for i, tag in enumerate(tags):
    w = tag_widths[i]
    draw.rounded_rectangle([tx, tag_y, tx + w, tag_y + 34], radius=17,
                           fill=(30, 15, 20), outline=(255, 99, 99))
    bbox = draw.textbbox((0, 0), tag, font=font_tags)
    tw = bbox[2] - bbox[0]
    draw.text((tx + (w - tw) // 2, tag_y + 6), tag, fill=(255, 200, 200), font=font_tags)
    tx += w + 12

# Bottom tech stack line
stack = "FastAPI · Pillow · Jinja2 · Vanilla JS"
stack_bbox = draw.textbbox((0, 0), stack, font=font_tags)
stack_w = stack_bbox[2] - stack_bbox[0]
draw.text(((WIDTH - stack_w) // 2, HEIGHT - 60), stack, fill=(100, 100, 130), font=font_tags)

# Bottom accent bar
for x in range(WIDTH):
    r = int(255 - (x / WIDTH) * 100)
    g = int(60 + (x / WIDTH) * 40)
    b = int(80 + (x / WIDTH) * 60)
    for y in range(HEIGHT - 4, HEIGHT):
        draw.point((x, y), fill=(r, g, b))

img.save("docs/banner.png", quality=95)
print("Banner saved: docs/banner.png")
