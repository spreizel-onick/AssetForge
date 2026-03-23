"""Visuelle Generatoren: Logo, Favicon, Icons, OG-Image, Farbpalette."""

import colorsys
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from . import register, get_output_dir


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a decent system font, fall back to default."""
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ── Logo ───────────────────────────────────────────────────

@register(
    name="logo",
    category="Visuell",
    description="Generiert ein text-basiertes Logo als PNG",
    parameters=[
        {"name": "text", "type": "text", "description": "Logo-Text", "required": True},
        {"name": "subtext", "type": "text", "description": "Untertitel / Slogan", "required": False},
        {"name": "style", "type": "select", "options": ["modern", "minimal", "bold", "gradient-bar"],
         "description": "Logo-Stil", "required": False},
        {"name": "bg_color", "type": "color", "description": "Hintergrundfarbe (hex)", "required": False, "default": "#1a1a2e"},
        {"name": "text_color", "type": "color", "description": "Textfarbe (hex)", "required": False, "default": "#e94560"},
        {"name": "accent_color", "type": "color", "description": "Akzentfarbe (für Stil-Details)", "required": False, "default": "#ff6b81"},
        {"name": "width", "type": "number", "description": "Breite in Pixel", "required": False, "default": 800},
        {"name": "height", "type": "number", "description": "Höhe in Pixel", "required": False, "default": 400},
        {"name": "shape", "type": "select", "options": ["none", "circle", "rounded_rect"],
         "description": "Hintergrund-Form", "required": False},
    ],
)
def generate_logo(params: dict) -> dict:
    w = int(params.get("width", 800))
    h = int(params.get("height", 400))
    bg = params.get("bg_color", "#1a1a2e")
    fg = params.get("text_color", "#e94560")
    accent = params.get("accent_color", "#ff6b81")
    text = params.get("text", "LOGO")
    subtext = params.get("subtext", "")
    style = params.get("style", "modern")
    shape = params.get("shape", "none")

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_rgb = _hex_to_rgb(bg)
    fg_rgb = _hex_to_rgb(fg)
    accent_rgb = _hex_to_rgb(accent)

    if shape == "circle":
        r = min(w, h) // 2 - 10
        cx, cy = w // 2, h // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_rgb)
    elif shape == "rounded_rect":
        draw.rounded_rectangle([20, 20, w - 20, h - 20], radius=30, fill=bg_rgb)
    else:
        draw.rectangle([0, 0, w, h], fill=bg_rgb)

    # Style: gradient-bar draws an accent bar at top
    if style == "gradient-bar":
        bar_h = max(6, h // 50)
        draw.rectangle([0, 0, w, bar_h], fill=accent_rgb)
        draw.rectangle([0, h - bar_h, w, h], fill=accent_rgb)

    # Calculate vertical offset for subtext
    has_sub = bool(subtext)
    y_offset = -20 if has_sub else 0

    # Find font size that fits
    if style == "bold":
        font_size = h // 2
    elif style == "minimal":
        font_size = h // 5
    else:
        font_size = h // 3

    font = _get_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    while tw > w * 0.8 and font_size > 10:
        font_size -= 4
        font = _get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (w - tw) // 2
    y = (h - th) // 2 - bbox[1] + y_offset

    # Style: minimal draws a line under text
    if style == "minimal":
        draw.text((x, y), text, fill=fg_rgb, font=font)
        line_y = y + th + bbox[1] + 12
        line_w = int(tw * 0.6)
        draw.rectangle([(w - line_w) // 2, line_y, (w + line_w) // 2, line_y + 3], fill=accent_rgb)
    else:
        draw.text((x, y), text, fill=fg_rgb, font=font)

    # Subtext
    if has_sub:
        sub_size = max(font_size // 3, 14)
        sub_font = _get_font(sub_size)
        sub_bbox = draw.textbbox((0, 0), subtext, font=sub_font)
        sub_tw = sub_bbox[2] - sub_bbox[0]
        sub_x = (w - sub_tw) // 2
        sub_y = y + th + bbox[1] + 15
        sub_color = accent_rgb if style != "minimal" else fg_rgb
        draw.text((sub_x, sub_y), subtext, fill=sub_color, font=sub_font)

    out = get_output_dir() / "logo.png"
    img.save(str(out), "PNG")
    return {"files": [str(out)], "message": f"Logo generiert: {w}x{h} ({style})"}


# ── Favicon ────────────────────────────────────────────────

@register(
    name="favicon",
    category="Visuell",
    description="Generiert Favicons in mehreren Größen (16, 32, 48, 192, 512)",
    parameters=[
        {"name": "text", "type": "text", "description": "Ein oder zwei Buchstaben für das Favicon", "required": True},
        {"name": "bg_color", "type": "color", "description": "Hintergrundfarbe (hex)", "required": False, "default": "#e94560"},
        {"name": "text_color", "type": "color", "description": "Textfarbe (hex)", "required": False, "default": "#ffffff"},
    ],
)
def generate_favicon(params: dict) -> dict:
    text = params.get("text", "A")[:2]
    bg = params.get("bg_color", "#e94560")
    fg = params.get("text_color", "#ffffff")
    sizes = [16, 32, 48, 192, 512]
    files = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 6, fill=_hex_to_rgb(bg))

        font_size = int(size * 0.55)
        font = _get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (size - tw) // 2
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), text, fill=_hex_to_rgb(fg), font=font)

        fname = f"favicon-{size}x{size}.png"
        out = get_output_dir() / fname
        img.save(str(out), "PNG")
        files.append(str(out))

    # Also save as .ico (16+32+48)
    ico_images = []
    for s in [16, 32, 48]:
        ico_images.append(Image.open(str(get_output_dir() / f"favicon-{s}x{s}.png")))
    ico_path = get_output_dir() / "favicon.ico"
    ico_images[0].save(str(ico_path), format="ICO", sizes=[(s, s) for s in [16, 32, 48]])
    files.append(str(ico_path))

    return {"files": files, "message": f"Favicons generiert in {len(sizes)} Größen + .ico"}


# ── OG-Image ──────────────────────────────────────────────

@register(
    name="og-image",
    category="Visuell",
    description="Generiert ein Open-Graph Social-Media-Preview-Bild (1200x630)",
    parameters=[
        {"name": "title", "type": "text", "description": "Titel", "required": True},
        {"name": "subtitle", "type": "text", "description": "Untertitel", "required": False},
        {"name": "bg_color", "type": "color", "description": "Hintergrundfarbe", "required": False, "default": "#0f3460"},
        {"name": "text_color", "type": "color", "description": "Textfarbe", "required": False, "default": "#ffffff"},
        {"name": "accent_color", "type": "color", "description": "Akzentfarbe", "required": False, "default": "#e94560"},
    ],
)
def generate_og_image(params: dict) -> dict:
    w, h = 1200, 630
    bg = _hex_to_rgb(params.get("bg_color", "#0f3460"))
    fg = _hex_to_rgb(params.get("text_color", "#ffffff"))
    accent = _hex_to_rgb(params.get("accent_color", "#e94560"))

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Accent bar at top
    draw.rectangle([0, 0, w, 8], fill=accent)

    # Title
    title = params.get("title", "Title")
    title_font = _get_font(64)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    draw.text((x, h // 2 - 60), title, fill=fg, font=title_font)

    # Subtitle
    subtitle = params.get("subtitle", "")
    if subtitle:
        sub_font = _get_font(32)
        bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, h // 2 + 30), subtitle, fill=accent, font=sub_font)

    out = get_output_dir() / "og-image.png"
    img.save(str(out), "PNG")
    return {"files": [str(out)], "message": "OG-Image (1200x630) generiert"}


# ── Farbpalette ────────────────────────────────────────────

@register(
    name="palette",
    category="Visuell",
    description="Generiert eine harmonische Farbpalette und exportiert als CSS + JSON",
    parameters=[
        {"name": "base_color", "type": "color", "description": "Basisfarbe (hex)", "required": True},
        {"name": "harmony", "type": "select", "options": ["complementary", "analogous", "triadic", "split-complementary"],
         "description": "Farbharmonie-Typ", "required": False},
        {"name": "count", "type": "number", "description": "Anzahl Farben", "required": False, "default": 5},
    ],
)
def generate_palette(params: dict) -> dict:
    base = params.get("base_color", "#e94560")
    harmony = params.get("harmony", "analogous")
    count = int(params.get("count", 5))

    r, g, b = _hex_to_rgb(base)
    h_base, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    hues = []
    if harmony == "complementary":
        hues = [h_base, (h_base + 0.5) % 1.0]
    elif harmony == "analogous":
        step = 0.08
        hues = [(h_base + step * (i - count // 2)) % 1.0 for i in range(count)]
    elif harmony == "triadic":
        hues = [h_base, (h_base + 1/3) % 1.0, (h_base + 2/3) % 1.0]
    elif harmony == "split-complementary":
        hues = [h_base, (h_base + 5/12) % 1.0, (h_base + 7/12) % 1.0]

    # Generate lighter/darker variants to reach desired count
    colors = []
    for hue in hues:
        rgb = colorsys.hsv_to_rgb(hue, s, v)
        hex_color = "#{:02x}{:02x}{:02x}".format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(hex_color)

    while len(colors) < count:
        hue = hues[len(colors) % len(hues)]
        factor = 0.7 + 0.3 * (len(colors) / count)
        rgb = colorsys.hsv_to_rgb(hue, s * factor, min(1.0, v * (1.1 - 0.2 * factor)))
        hex_color = "#{:02x}{:02x}{:02x}".format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(hex_color)

    colors = colors[:count]
    files = []

    # CSS
    css_lines = [":root {"]
    for i, c in enumerate(colors):
        css_lines.append(f"  --color-{i + 1}: {c};")
    css_lines.append("}")
    css_out = get_output_dir() / "palette.css"
    css_out.write_text("\n".join(css_lines), encoding="utf-8")
    files.append(str(css_out))

    # JSON
    json_out = get_output_dir() / "palette.json"
    json_out.write_text(json.dumps({"base": base, "harmony": harmony, "colors": colors}, indent=2), encoding="utf-8")
    files.append(str(json_out))

    # PNG swatch
    swatch_w = 100 * count
    img = Image.new("RGB", (swatch_w, 100))
    draw = ImageDraw.Draw(img)
    for i, c in enumerate(colors):
        draw.rectangle([i * 100, 0, (i + 1) * 100, 100], fill=_hex_to_rgb(c))
    swatch_out = get_output_dir() / "palette.png"
    img.save(str(swatch_out), "PNG")
    files.append(str(swatch_out))

    return {"files": files, "message": f"Farbpalette ({harmony}) mit {count} Farben generiert"}
