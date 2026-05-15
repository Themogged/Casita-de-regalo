import math
import random
import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, UnidentifiedImageError


CANVAS_SIZE = (1080, 1350)


class ProductFrameError(Exception):
    """Raised when a product image cannot be framed safely."""


def slugify_filename(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "producto"


def generate_yellow_child_frame(source_path, logo_path, output_path, product_name, *, quality=88):
    source_path = Path(source_path)
    logo_path = Path(logo_path)
    output_path = Path(output_path)

    if not source_path.exists():
        raise ProductFrameError(f"No existe la imagen origen: {source_path}")
    if not logo_path.exists():
        raise ProductFrameError(f"No existe el logo: {logo_path}")

    try:
        with Image.open(source_path) as raw_product:
            product_image = ImageOps.exif_transpose(raw_product).convert("RGB")
    except (OSError, UnidentifiedImageError) as exc:
        raise ProductFrameError(f"No se pudo abrir la imagen origen: {source_path}") from exc

    try:
        with Image.open(logo_path) as raw_logo:
            logo = ImageOps.exif_transpose(raw_logo).convert("RGBA")
    except (OSError, UnidentifiedImageError) as exc:
        raise ProductFrameError(f"No se pudo abrir el logo: {logo_path}") from exc

    canvas = _make_yellow_background(*CANVAS_SIZE)
    draw = ImageDraw.Draw(canvas, "RGBA")
    rng = random.Random(slugify_filename(product_name))

    _draw_child_decorations(draw, rng)
    _paste_product_photo(canvas, product_image)
    _draw_brand_badge(canvas, logo)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "WEBP", quality=quality, method=6)
    return output_path


def _make_yellow_background(width, height):
    top = (255, 246, 174)
    bottom = (255, 191, 56)
    canvas = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(canvas)

    for y in range(height):
        ratio = y / max(1, height - 1)
        wave = 0.04 * math.sin((y / height) * math.pi * 2)
        mix = min(1, max(0, ratio + wave))
        color = tuple(round(top[i] * (1 - mix) + bottom[i] * mix) for i in range(3))
        draw.line((0, y, width, y), fill=color)

    overlay = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.polygon(((width, 0), (width, height), (width * 0.42, height)), fill=(255, 173, 39, 36))
    draw.ellipse((-120, 120, 250, 520), fill=(255, 255, 255, 44))
    draw.ellipse((820, 40, 1210, 430), fill=(255, 255, 255, 42))
    draw.ellipse((760, 1040, 1180, 1460), fill=(255, 238, 160, 90))
    draw.rectangle((0, 0, width, height), outline=(255, 255, 255, 55), width=10)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


def _draw_child_decorations(draw, rng):
    palette = [
        (255, 120, 77, 180),
        (255, 156, 55, 170),
        (105, 190, 245, 160),
        (255, 102, 168, 160),
        (111, 210, 151, 150),
        (255, 255, 255, 190),
    ]

    for _ in range(30):
        x = rng.randint(18, 1040)
        y = rng.randint(18, 1320)
        if 70 < x < 1010 and 80 < y < 1135:
            continue
        size = rng.randint(14, 34)
        color = rng.choice(palette)
        if rng.random() < 0.45:
            _draw_star(draw, x, y, size, color)
        else:
            draw.ellipse((x - size, y - size, x + size, y + size), fill=color)

    for x, y, size, color in [
        (44, 118, 56, (255, 255, 255, 115)),
        (998, 210, 66, (255, 120, 77, 130)),
        (52, 1090, 72, (255, 126, 54, 150)),
        (990, 1122, 58, (255, 255, 255, 140)),
    ]:
        draw.ellipse((x - size, y - size, x + size, y + size), fill=color)
        draw.ellipse((x - size, y - size, x + size, y + size), outline=(255, 255, 255, 130), width=4)


def _draw_star(draw, cx, cy, radius, fill):
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        point_radius = radius if index % 2 == 0 else radius * 0.45
        points.append((cx + math.cos(angle) * point_radius, cy + math.sin(angle) * point_radius))
    draw.polygon(points, fill=fill)


def _paste_product_photo(canvas, product_image):
    draw = ImageDraw.Draw(canvas, "RGBA")
    outer = (78, 86, 1002, 1128)
    inner = (96, 104, 984, 1110)

    _rounded_shadow(canvas, outer, radius=34)
    draw.rounded_rectangle(outer, radius=34, fill=(255, 255, 255, 250))
    draw.rounded_rectangle((outer[0] + 8, outer[1] + 8, outer[2] - 8, outer[3] - 8), radius=28, outline=(255, 238, 170, 180), width=4)

    photo_box = _make_photo_fill_background(product_image, (inner[2] - inner[0], inner[3] - inner[1]))
    fitted = ImageOps.contain(product_image, photo_box.size, Image.Resampling.LANCZOS)
    x = (photo_box.width - fitted.width) // 2
    y = (photo_box.height - fitted.height) // 2
    photo_box.paste(fitted, (x, y), _soft_edge_mask(fitted.size))

    mask = Image.new("L", photo_box.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, photo_box.width, photo_box.height), radius=24, fill=255)
    canvas.paste(photo_box.convert("RGBA"), (inner[0], inner[1]), mask)


def _make_photo_fill_background(product_image, size):
    box_width, box_height = size
    background = ImageOps.fit(product_image, size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    background = background.filter(ImageFilter.GaussianBlur(radius=24))
    background = ImageOps.autocontrast(background, cutoff=1)
    background = Image.blend(background, Image.new("RGB", size, (255, 235, 135)), 0.08)

    vignette = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(vignette, "RGBA")
    draw.rectangle((0, 0, box_width, box_height), fill=(255, 255, 255, 12))
    draw.rounded_rectangle((18, 18, box_width - 18, box_height - 18), radius=30, outline=(255, 255, 255, 90), width=4)
    return Image.alpha_composite(background.convert("RGBA"), vignette).convert("RGB")


def _soft_edge_mask(size, feather=28):
    width, height = size
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    horizontal_feather = min(feather, max(1, width // 8))
    vertical_feather = min(feather, max(1, height // 8))

    for x in range(horizontal_feather):
        alpha = round(255 * (x + 1) / horizontal_feather)
        draw.line((x, 0, x, height), fill=alpha)
        draw.line((width - 1 - x, 0, width - 1 - x, height), fill=alpha)

    for y in range(vertical_feather):
        alpha = round(255 * (y + 1) / vertical_feather)
        draw.line((0, y, width, y), fill=alpha)
        draw.line((0, height - 1 - y, width, height - 1 - y), fill=alpha)

    return mask


def _draw_brand_badge(canvas, logo):
    draw = ImageDraw.Draw(canvas, "RGBA")
    badge = (188, 1172, 892, 1288)
    _rounded_shadow(canvas, badge, radius=46, opacity=52)
    draw.rounded_rectangle(badge, radius=46, fill=(255, 255, 255, 242))
    draw.rounded_rectangle((badge[0] + 6, badge[1] + 6, badge[2] - 6, badge[3] - 6), radius=40, outline=(255, 210, 86, 170), width=3)

    text = "Casita de Regalos"
    font_size = 54
    font = _load_font(font_size, bold=True)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    logo_copy = logo.copy()
    logo_copy.thumbnail((78, 78), Image.Resampling.LANCZOS)
    text_width = text_bbox[2] - text_bbox[0]

    while text_width > badge[2] - badge[0] - 180 and font_size > 34:
        font_size -= 2
        font = _load_font(font_size, bold=True)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]

    logo_x = badge[0] + 44
    logo_y = badge[1] + (badge[3] - badge[1] - logo_copy.height) // 2
    canvas.alpha_composite(logo_copy, (logo_x, logo_y))

    text_x = badge[0] + ((badge[2] - badge[0]) - text_width) // 2
    text_y = badge[1] + ((badge[3] - badge[1]) - (text_bbox[3] - text_bbox[1])) // 2 - 4
    draw.text((text_x + 2, text_y + 3), text, font=font, fill=(120, 70, 15, 55))
    draw.text((text_x, text_y), text, font=font, fill=(118, 78, 18, 255))


def _rounded_shadow(canvas, box, radius, opacity=45):
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    x1, y1, x2, y2 = box
    shadow_draw.rounded_rectangle((x1 + 8, y1 + 12, x2 + 8, y2 + 12), radius=radius, fill=(100, 60, 15, opacity))
    canvas.alpha_composite(shadow)


def _load_font(size, *, bold=False):
    candidates = [
        "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()
