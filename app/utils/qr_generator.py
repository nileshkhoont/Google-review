"""Generates and saves QR code poster images that point to a business's
customer landing page."""

import math
import os

import qrcode
from qrcode.image.pil import PilImage

from PIL import (
    Image,
    ImageDraw,
    ImageFilter,
    ImageFont,
    ImageOps,
)

from app.config import settings

# Used whenever a business hasn't picked its own primary_color — matches
# the app's own brand indigo (see --color-primary in style.css) so an
# unbranded poster still looks intentional rather than generic.
DEFAULT_PRIMARY_COLOR = "#4f46e5"

# Fixed Movya mark stamped in the center of every generated QR code,
# regardless of business — a "powered by" watermark, not the business's
# own logo (which appears separately, in the header lockup).
MOVYA_LOGO_PATH = "app/logo/m.png"

# Real brand marks for the poster's social icon row, used in place of
# drawn glyphs — a flat programmatic redraw reads noticeably off-brand
# next to the actual platform icons.
ICON_LOGO_PATHS = {
    "google": "app/logo/google.jpg",
    "instagram": "app/logo/instagram.jpg",
    "facebook": "app/logo/facebook.png",
    "website": "app/logo/website.avif",
    "twitter": "app/logo/X.jpg",
}

# Fallback flat colors, used only if a logo file above is missing.
_ICON_COLORS = {
    "google": "#4285F4",
    "instagram": "#d946ef",
    "facebook": "#1877F2",
    "website": "#3b82f6",
    "twitter": "#1DA1F2",
}


def _ensure_qr_dir() -> None:
    os.makedirs(settings.qr_code_dir, exist_ok=True)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _lighten(hex_color: str, factor: float) -> tuple[int, int, int]:
    """Blends `hex_color` toward white by `factor` (0 = unchanged, 1 = white)."""
    r, g, b = _hex_to_rgb(hex_color)
    return (
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )


def _darken(hex_color: str, factor: float) -> tuple[int, int, int]:
    """Blends `hex_color` toward black by `factor` (0 = unchanged, 1 = black)."""
    r, g, b = _hex_to_rgb(hex_color)
    return (
        int(r * (1 - factor)),
        int(g * (1 - factor)),
        int(b * (1 - factor)),
    )


def _paste_with_shadow(
    card: Image.Image,
    element: Image.Image,
    position: tuple[int, int],
    blur: int = 16,
    offset: tuple[int, int] = (0, 10),
    opacity: int = 55,
) -> None:
    """Pastes `element` (RGBA) onto `card` with a soft drop shadow shaped
    to its own alpha silhouette — works for circles, rounded rects, etc."""
    ex, ey = position
    ew, eh = element.size
    pad = blur * 2

    shadow_shape = Image.new("L", (ew, eh), 0)
    shadow_shape.paste(element.split()[-1], (0, 0))
    shadow_layer = Image.new("RGBA", (ew + pad * 2, eh + pad * 2), (0, 0, 0, 0))
    shadow_layer.paste(Image.new("RGBA", (ew, eh), (0, 0, 0, opacity)), (pad, pad), shadow_shape)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))

    card.paste(
        shadow_layer,
        (ex - pad + offset[0], ey - pad + offset[1]),
        shadow_layer,
    )
    card.paste(element, (ex, ey), element)


def _draw_background_accents(card: Image.Image, width: int, height: int, color: str) -> None:
    """Two large, softly-blurred tints of the brand color in opposite
    corners — quiet depth behind the white card, never behind text."""
    accents = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    accent_draw = ImageDraw.Draw(accents)
    tint = (*_hex_to_rgb(color), 38)

    r1 = 420
    accent_draw.ellipse((width - r1 * 0.6, -r1 * 0.6, width + r1 * 0.6, r1 * 0.6), fill=tint)

    r2 = 380
    accent_draw.ellipse((-r2 * 0.6, height - r2 * 0.5, r2 * 0.6, height + r2 * 0.5), fill=tint)

    accents = accents.filter(ImageFilter.GaussianBlur(95))
    card.paste(accents, (0, 0), accents)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ("arialbd.ttf", "arial.ttf") if bold else ("arial.ttf",)
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, min_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Shrinks a font size until `text` fits on one line within `max_width`."""
    size = start_size
    while size > min_size:
        font = _font(size, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return _font(min_size, bold=bold)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered_text(draw: ImageDraw.ImageDraw, card_width: int, y: int, text: str, font: ImageFont.FreeTypeFont, fill) -> int:
    """Draws `text` horizontally centered at `y`; returns the text's height."""
    width, height = _text_size(draw, text, font)
    draw.text(((card_width - width) // 2, y), text, fill=fill, font=font)
    return height


def _draw_centered_text_tracked(draw: ImageDraw.ImageDraw, card_width: int, y: int, text: str, font: ImageFont.FreeTypeFont, fill, tracking: int = 0) -> int:
    """Like _draw_centered_text, but with extra pixel spacing between every
    character — a wider, more deliberate "stretched" look for short lines."""
    char_widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total_width = sum(char_widths) + tracking * (len(text) - 1)
    x = (card_width - total_width) / 2
    max_height = 0
    for ch, w in zip(text, char_widths):
        bbox = draw.textbbox((0, 0), ch, font=font)
        draw.text((x, y), ch, font=font, fill=fill)
        max_height = max(max_height, bbox[3] - bbox[1])
        x += w + tracking
    return max_height


def _rounded_corners(image: Image.Image, radius: int) -> Image.Image:
    """Returns `image` with its four corners cut to transparent."""
    image = image.convert("RGBA")
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def _draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, outer_r: float, color) -> None:
    inner_r = outer_r * 0.42
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)


def _draw_star_row(draw: ImageDraw.ImageDraw, card_width: int, y: int, count: int, size: float, gap: float, color) -> int:
    """Centered row of filled 5-point stars (purely decorative — always
    full marks, not tied to any actual rating data)."""
    step = size * 2 + gap
    total_width = count * step - gap
    start_x = (card_width - total_width) / 2
    for i in range(count):
        cx = start_x + i * step + size
        _draw_star(draw, cx, y + size, size, color)
    return int(size * 2)


_ICON_SUPERSAMPLE = 4


def _draw_icon_badge(card: Image.Image, cx: int, cy: int, diameter: int, key: str) -> None:
    """Draws one small circular platform badge centered at (cx, cy), built
    from the real brand logo file in ICON_LOGO_PATHS. Rendered at 4x size
    and downsampled with LANCZOS, since PIL's default drawing has no
    anti-aliasing and a small circle crop comes out visibly jagged
    ("painted") without it."""
    s = _ICON_SUPERSAMPLE
    d = diameter * s
    badge = Image.new("RGBA", (d, d), (0, 0, 0, 0))

    logo_path = ICON_LOGO_PATHS.get(key)
    logo = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
        except Exception:
            logo = None

    if logo is not None:
        # Each asset is a full-bleed square tile with its own background
        # (brand color or white) baked in — cover-fit into the circle so
        # nothing letterboxes.
        tile = ImageOps.fit(logo.convert("RGB"), (d, d), Image.LANCZOS)
        mask = Image.new("L", (d, d), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, d, d), fill=255)
        badge.paste(tile, (0, 0), mask)
    else:
        # Missing asset on disk — flat brand-color circle rather than a
        # blank gap in the row.
        ImageDraw.Draw(badge).ellipse((0, 0, d, d), fill=_ICON_COLORS[key])

    badge = badge.resize((diameter, diameter), Image.LANCZOS)
    card.paste(badge, (cx - diameter // 2, cy - diameter // 2), badge)


def generate_qr_image(
    data_url: str,
    filename: str,
    business_name: str,
    logo_path: str | None = None,
    subtitle: str = "Scan to Leave a Review",
    qr_title: str | None = None,
    primary_color: str | None = None,
    service_type: str | None = None,
) -> str:
    """
    Generate a branded QR poster encoding `data_url` and save it as
    `filename` inside the configured QR code directory.

    Returns the relative file path (usable in <img src="..."> via /static).
    """
    _ensure_qr_dir()

    color = primary_color or DEFAULT_PRIMARY_COLOR
    tagline = (qr_title or "").strip()
    has_logo = bool(logo_path and os.path.exists(logo_path))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=3,
    )
    qr.add_data(data_url)
    qr.make(fit=True)

    qr_img: Image.Image = qr.make_image(
        fill_color="black",
        back_color="white",
    ).convert("RGB")

    # ----------------------------
    # Card Size
    # ----------------------------

    CARD_WIDTH = 800
    LOGO_SIZE = 92
    QR_SIZE = 600
    ICON_DIAMETER = 84
    CARD_HEIGHT = 1417

    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), "white")
    _draw_background_accents(card, CARD_WIDTH, CARD_HEIGHT, color)
    draw = ImageDraw.Draw(card)

    current_y = 80

    # ----------------------------
    # Header lockup: logo beside business name / service type — a compact
    # wordmark rather than a full-width banner, so the rest of the poster
    # stays a clean white card.
    # ----------------------------

    name_font = _fit_font(draw, business_name.strip(), 480, start_size=44, min_size=26, bold=True)
    name_w, name_h = _text_size(draw, business_name.strip(), name_font)

    service_label = " ".join(service_type.strip().upper()) if service_type and service_type.strip() else ""
    service_font = _font(19)
    service_w, service_h = _text_size(draw, service_label, service_font) if service_label else (0, 0)

    text_block_w = max(name_w, service_w)
    text_block_h = name_h + (10 + service_h if service_label else 0)
    lockup_h = max(text_block_h, LOGO_SIZE if has_logo else 0)

    lockup_w = (LOGO_SIZE + 22 if has_logo else 0) + text_block_w
    lockup_x = (CARD_WIDTH - lockup_w) // 2

    if has_logo:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
            mask = Image.new("L", logo.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, logo.width, logo.height), fill=255)
            circular_logo = Image.new("RGBA", logo.size, (0, 0, 0, 0))
            circular_logo.paste(logo, (0, 0), mask)
            logo_y = current_y + (lockup_h - logo.height) // 2
            _paste_with_shadow(card, circular_logo, (lockup_x, logo_y), blur=10, offset=(0, 5), opacity=40)
        except Exception:
            has_logo = False

    text_y = current_y + (lockup_h - text_block_h) // 2
    if has_logo:
        # Sitting beside a logo, the lines read as a wordmark — left-align them.
        text_x = lockup_x + LOGO_SIZE + 22
        draw.text((text_x, text_y), business_name.strip(), font=name_font, fill="#111827")
        if service_label:
            draw.text((text_x, text_y + name_h + 10), service_label, font=service_font, fill="#9aa1b1")
    else:
        # No logo to sit beside — each line centers on its own instead.
        _draw_centered_text(draw, CARD_WIDTH, text_y, business_name.strip(), name_font, "#111827")
        if service_label:
            _draw_centered_text(draw, CARD_WIDTH, text_y + name_h + 10, service_label, service_font, "#9aa1b1")

    current_y += lockup_h + 35

    # ----------------------------
    # Tagline — the poster's main colored heading. Skipped entirely when
    # not set, since the business name is already shown above.
    # ----------------------------

    MAX_TEXT_WIDTH = CARD_WIDTH - 100
    if tagline:
        tagline_font = _fit_font(draw, tagline, MAX_TEXT_WIDTH, start_size=38, min_size=22, bold=True)
        current_y += _draw_centered_text(draw, CARD_WIDTH, current_y, tagline, tagline_font, _darken(color, 0.15)) + 40

    # ----------------------------
    # Subtitle
    # ----------------------------

    subtitle_font = _font(26)
    current_y += _draw_centered_text(draw, CARD_WIDTH, current_y, subtitle, subtitle_font, "#6b7280") + 7

    # ----------------------------
    # QR Image
    # ----------------------------

    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.NEAREST)
    qr_x = (CARD_WIDTH - QR_SIZE) // 2
    qr_y = current_y
    card.paste(qr_img, (qr_x, qr_y))

    # QR-center logo — always the static Movya mark, the same on every
    # generated QR code regardless of business. Distinct from the header
    # lockup logo above, which stays business-specific.
    if os.path.exists(MOVYA_LOGO_PATH):
        try:
            movya_logo = Image.open(MOVYA_LOGO_PATH).convert("RGBA")
            CENTER_LOGO_SIZE = 76
            movya_logo.thumbnail((CENTER_LOGO_SIZE, CENTER_LOGO_SIZE), Image.LANCZOS)

            # A small white halo keeps the (black) badge from visually
            # fusing with adjacent black QR modules.
            halo_padding = 6
            halo_size = (movya_logo.width + halo_padding * 2, movya_logo.height + halo_padding * 2)
            halo = Image.new("RGBA", halo_size, (0, 0, 0, 0))
            ImageDraw.Draw(halo).ellipse((0, 0, halo_size[0], halo_size[1]), fill="white")
            halo.paste(movya_logo, (halo_padding, halo_padding), movya_logo)

            center_x = qr_x + (QR_SIZE - halo_size[0]) // 2
            center_y = qr_y + (QR_SIZE - halo_size[1]) // 2
            card.paste(halo, (center_x, center_y), halo)
        except Exception:
            pass

    current_y += QR_SIZE + 7

    # ----------------------------
    # Star rating + thank-you line (decorative — always 5 stars), on a
    # soft amber pill so it reads as one grouped "review" badge.
    # ----------------------------

    STAR_COUNT, STAR_SIZE, STAR_GAP = 5, 19, 10
    star_row_width = STAR_COUNT * (STAR_SIZE * 2 + STAR_GAP) - STAR_GAP
    chip_pad_x, chip_pad_y = 34, 14
    chip_w = star_row_width + chip_pad_x * 2
    chip_h = STAR_SIZE * 2 + chip_pad_y * 2
    chip_x = (CARD_WIDTH - chip_w) // 2
    draw.rounded_rectangle(
        (chip_x, current_y, chip_x + chip_w, current_y + chip_h),
        radius=chip_h // 2,
        fill=_lighten("#f59e0b", 0.9),
    )
    _draw_star_row(draw, CARD_WIDTH, current_y + chip_pad_y, count=STAR_COUNT, size=STAR_SIZE, gap=STAR_GAP, color="#f59e0b")
    current_y += chip_h + 18

    thanks_font = _font(23)
    current_y += _draw_centered_text(draw, CARD_WIDTH, current_y, "Thank you for trusting us!", thanks_font, _darken(color, 0.15)) + 40

    # ----------------------------
    # Social Icons Row — grouped on a light rounded "shelf" with its own
    # soft shadow, rather than floating directly on the white card.
    # ----------------------------

    icon_keys = ("google", "instagram", "facebook", "website", "twitter")
    icon_labels = {
        "google": ("Review on", "Google"),
        "instagram": ("Instagram",),
        "facebook": ("Facebook",),
        "website": ("Website",),
        "twitter": ("Twitter",),
    }
    icon_label_font = _font(18)

    SHELF_MARGIN = 28
    shelf_pad = 22
    label_line_h = _text_size(draw, "Ag", icon_label_font)[1]
    max_lines = max(len(lines) for lines in icon_labels.values())
    label_block_h = max_lines * (label_line_h + 5)
    shelf_w = CARD_WIDTH - SHELF_MARGIN * 2
    shelf_h = ICON_DIAMETER + label_block_h + shelf_pad * 2

    shelf_img = Image.new("RGBA", (shelf_w, shelf_h), (0, 0, 0, 0))
    ImageDraw.Draw(shelf_img).rounded_rectangle((0, 0, shelf_w - 1, shelf_h - 1), radius=24, fill=(248, 249, 251, 255))
    _paste_with_shadow(card, shelf_img, (SHELF_MARGIN, current_y), blur=14, offset=(0, 6), opacity=18)

    icons_top = current_y + shelf_pad
    slot_width = CARD_WIDTH // len(icon_keys)
    for i, key in enumerate(icon_keys):
        slot_cx = slot_width * i + slot_width // 2
        _draw_icon_badge(card, slot_cx, icons_top + ICON_DIAMETER // 2, ICON_DIAMETER, key)

        label_y = icons_top + ICON_DIAMETER + 10
        for line in icon_labels[key]:
            line_w, line_h = _text_size(draw, line, icon_label_font)
            draw.text((slot_cx - line_w // 2, label_y), line, fill="#6b7280", font=icon_label_font)
            label_y += line_h + 5

    current_y += shelf_h + 45

    # ----------------------------
    # Footer
    # ----------------------------

    divider_w = 90
    draw.line(
        (CARD_WIDTH // 2 - divider_w // 2, current_y, CARD_WIDTH // 2 + divider_w // 2, current_y),
        fill=_lighten(color, 0.35),
        width=3,
    )
    current_y += 40

    footer_font = _font(32, bold=True)
    current_y += _draw_centered_text_tracked(draw, CARD_WIDTH, current_y, "Powered by Movya", footer_font, "#9aa1b1", tracking=1) + 12
    _draw_centered_text_tracked(draw, CARD_WIDTH, current_y, "www.movya.com", footer_font, "#9aa1b1", tracking=1)

    card = _rounded_corners(card, radius=32)

    file_path = os.path.join(settings.qr_code_dir, filename)
    card.save(file_path)
    return file_path


def delete_qr_image(file_path: str) -> None:
    """Remove a QR image file from disk if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
