"""Generates and saves QR code images that point to a business's
customer landing page."""

import os

import qrcode
from qrcode.image.pil import PilImage

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from app.config import settings


def _ensure_qr_dir() -> None:
    os.makedirs(settings.qr_code_dir, exist_ok=True)


def generate_qr_image(
    data_url: str,
    filename: str,
    business_name: str,
    logo_path: str | None = None,
    subtitle: str = "Scan to Leave a Review",
) -> str:
    """
    Generate a QR code PNG encoding `data_url` and save it as `filename`
    inside the configured QR code directory.

    Returns the relative file path (usable in <img src="..."> via /static).
    """
    _ensure_qr_dir()

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=5,
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
    CARD_HEIGHT = 860
    card = Image.new(
        "RGB",
        (CARD_WIDTH, CARD_HEIGHT),
        "white",
    )
    draw = ImageDraw.Draw(card)

# ----------------------------
# Fonts
# ----------------------------

    try:
        subtitle_font = ImageFont.truetype("arial.ttf", 30)
        footer_font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        subtitle_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # -------------------------------------------------
    # Dynamic Layout
    # -------------------------------------------------

    current_y = 40

    # ----------------------------
    # Business Name
    # ----------------------------

    title = business_name.strip()

    # Start at the default size and shrink only as much as needed to
    # keep the name on a single line within the card width.
    title_font_size = 45
    MIN_TITLE_FONT_SIZE = 20
    MAX_TITLE_WIDTH = CARD_WIDTH - 80

    while True:
        try:
            title_font = ImageFont.truetype("arial.ttf", title_font_size)
        except Exception:
            title_font = ImageFont.load_default()
            break

        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        if title_width <= MAX_TITLE_WIDTH or title_font_size <= MIN_TITLE_FONT_SIZE:
            break
        title_font_size -= 2

    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]

    draw.text(
        ((CARD_WIDTH - title_width) // 2, current_y),
        title,
        fill="black",
        font=title_font,
    )

    current_y += title_height + 30

    # ----------------------------
    # Subtitle
    # ----------------------------

    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_height = bbox[3] - bbox[1]

    draw.text(
        ((CARD_WIDTH - subtitle_width) // 2, current_y),
        subtitle,
        fill="#666666",
        font=subtitle_font,
    )

    current_y += subtitle_height + 25

    # ----------------------------
    # QR Image
    # ----------------------------

    QR_SIZE = 600

    qr_img = qr_img.resize(
    (QR_SIZE, QR_SIZE),
    Image.NEAREST,
    )

    qr_x = (CARD_WIDTH - QR_SIZE) // 2
    qr_y = current_y

    card.paste(qr_img, (qr_x, qr_y))

    # ----------------------------
    # Add Business Logo (Center)
    # ----------------------------

    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")

            LOGO_SIZE = 72

            logo.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)

            padding = 10

            bg_size = (
                logo.width + padding * 2,
                logo.height + padding * 2,
            )

            logo_bg = Image.new(
                "RGBA",
                bg_size,
                (255, 255, 255, 0),
            )

            bg_draw = ImageDraw.Draw(logo_bg)

            bg_draw.rounded_rectangle(
                (0, 0, bg_size[0], bg_size[1]),
                radius=22,
                fill="white",
            )

            logo_bg.paste(logo, (padding, padding), logo)

            logo_x = qr_x + (QR_SIZE - logo_bg.width) // 2
            logo_y = qr_y + (QR_SIZE - logo_bg.height) // 2

            card.paste(logo_bg, (logo_x, logo_y), logo_bg)

        except Exception:
            pass

    current_y += QR_SIZE + 25

    # ----------------------------
    # Footer
    # ----------------------------

    footer_1 = "Powered by Movya"
    footer_2 = "www.movya.com"

    bbox = draw.textbbox((0, 0), footer_1, font=footer_font)
    footer1_width = bbox[2] - bbox[0]
    footer1_height = bbox[3] - bbox[1]

    draw.text(
        ((CARD_WIDTH - footer1_width) // 2, current_y),
        footer_1,
        fill="#777777",
        font=footer_font,
    )

    current_y += footer1_height + 6

    bbox = draw.textbbox((0, 0), footer_2, font=footer_font)
    footer2_width = bbox[2] - bbox[0]
    footer2_height = bbox[3] - bbox[1]

    draw.text(
        ((CARD_WIDTH - footer2_width) // 2, current_y),
        footer_2,
        fill="#777777",
        font=footer_font,
    )

    current_y += footer2_height + 30

    file_path = os.path.join(
        settings.qr_code_dir,
        filename,
    )
    card.save(file_path)
    return file_path


def delete_qr_image(file_path: str) -> None:
    """Remove a QR image file from disk if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
