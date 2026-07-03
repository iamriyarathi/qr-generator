"""
QR code rendering engine.

Design notes
------------
We only use the `qrcode` package for what it is actually good at and
extremely stable at: encoding data + error-correction into a boolean
module matrix (`QRCode.get_matrix()`). Every visual concern — box size,
colors, rounded modules, transparency, logo compositing, quiet zone —
is then handled by us with Pillow (for PNG/JPG) or hand-built SVG markup.
This keeps rendering fully deterministic and avoids depending on the
narrower/less consistent styling APIs of third-party image factories.
"""
import base64
import io

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)
from PIL import Image, ImageDraw

EC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

MIN_SIZE = 120
MAX_SIZE = 2000


def hex_to_rgb(hex_color, default=(0, 0, 0)):
    try:
        h = (hex_color or "").lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            return default
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    except (ValueError, TypeError):
        return default


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def get_qr_matrix(data, error_correction="M", border=4):
    """Encode `data` and return the boolean module matrix (border included)."""
    ec = EC_MAP.get((error_correction or "M").upper(), ERROR_CORRECT_M)
    border = int(clamp(border, 0, 20))
    qr = qrcode.QRCode(version=None, error_correction=ec, box_size=1, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.get_matrix()


# ----------------------------------------------------------------------
# PNG / JPG rendering (Pillow)
# ----------------------------------------------------------------------

def render_pil_image(matrix, size=400, fg_color="#000000", bg_color="#FFFFFF",
                      rounded=False, transparent=False, logo_bytes=None):
    """Render the matrix to an RGBA PIL Image."""
    size = int(clamp(size, MIN_SIZE, MAX_SIZE))
    n = len(matrix)
    box = max(1, size // n)
    img_size = box * n

    fg = hex_to_rgb(fg_color, (0, 0, 0))
    bg = hex_to_rgb(bg_color, (255, 255, 255))
    bg_pixel = (*bg, 0) if transparent else (*bg, 255)
    fg_pixel = (*fg, 255)

    img = Image.new("RGBA", (img_size, img_size), bg_pixel)
    draw = ImageDraw.Draw(img)
    radius = box * 0.3 if rounded else 0

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if not val:
                continue
            x0, y0 = x * box, y * box
            x1, y1 = x0 + box - 1, y0 + box - 1
            if rounded:
                draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fg_pixel)
            else:
                draw.rectangle([x0, y0, x1, y1], fill=fg_pixel)

    if img_size != size:
        img = img.resize((size, size), Image.LANCZOS)

    if logo_bytes:
        img = _apply_logo(img, logo_bytes, size)

    return img


def _apply_logo(img, logo_bytes, size):
    """Paste a centered logo with a rounded white backing plate on top of img."""
    try:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    except Exception:
        return img

    logo_target = int(size * 0.22)
    logo.thumbnail((logo_target, logo_target), Image.LANCZOS)

    pad = max(6, int(logo_target * 0.16))
    plate_w, plate_h = logo.width + pad * 2, logo.height + pad * 2
    plate = Image.new("RGBA", (plate_w, plate_h), (255, 255, 255, 255))
    mask = Image.new("L", (plate_w, plate_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, plate_w - 1, plate_h - 1], radius=int(min(plate_w, plate_h) * 0.22), fill=255
    )
    plate.putalpha(mask)
    plate.paste(logo, (pad, pad), logo)

    bx = (img.width - plate_w) // 2
    by = (img.height - plate_h) // 2
    img.alpha_composite(plate, (bx, by))
    return img


def pil_to_png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def pil_to_jpg_bytes(img, bg_color="#FFFFFF"):
    bg = hex_to_rgb(bg_color, (255, 255, 255))
    flat = Image.new("RGB", img.size, bg)
    if img.mode == "RGBA":
        flat.paste(img, mask=img.split()[3])
    else:
        flat.paste(img)
    buf = io.BytesIO()
    flat.save(buf, format="JPEG", quality=93, optimize=True)
    buf.seek(0)
    return buf


def pil_to_data_uri(img):
    buf = pil_to_png_bytes(img)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# ----------------------------------------------------------------------
# SVG rendering (hand-built, so colors/rounding/transparency are exact)
# ----------------------------------------------------------------------

def render_svg(matrix, size=400, fg_color="#000000", bg_color="#FFFFFF",
                rounded=False, transparent=False, logo_bytes=None):
    size = int(clamp(size, MIN_SIZE, MAX_SIZE))
    n = len(matrix)
    box = size / n
    radius = box * 0.3 if rounded else 0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" shape-rendering="crispEdges">'
    ]
    if not transparent:
        parts.append(f'<rect width="{size}" height="{size}" fill="{bg_color}"/>')

    parts.append(f'<g fill="{fg_color}">')
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if not val:
                continue
            x0, y0 = x * box, y * box
            if rounded:
                parts.append(
                    f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{box:.2f}" height="{box:.2f}" '
                    f'rx="{radius:.2f}" ry="{radius:.2f}"/>'
                )
            else:
                parts.append(
                    f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{box:.2f}" height="{box:.2f}"/>'
                )
    parts.append("</g>")

    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            logo_target = int(size * 0.22)
            logo.thumbnail((logo_target, logo_target), Image.LANCZOS)
            pad = max(6, int(logo_target * 0.16))
            plate_w, plate_h = logo.width + pad * 2, logo.height + pad * 2
            plate = Image.new("RGBA", (plate_w, plate_h), (255, 255, 255, 255))
            mask = Image.new("L", (plate_w, plate_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, plate_w - 1, plate_h - 1], radius=int(min(plate_w, plate_h) * 0.22), fill=255
            )
            plate.putalpha(mask)
            plate.paste(logo, (pad, pad), logo)
            buf = io.BytesIO()
            plate.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            bx = (size - plate_w) / 2
            by = (size - plate_h) / 2
            parts.append(
                f'<image x="{bx:.2f}" y="{by:.2f}" width="{plate_w}" height="{plate_h}" '
                f'href="data:image/png;base64,{b64}"/>'
            )
        except Exception:
            pass

    parts.append("</svg>")
    return "".join(parts)


# ----------------------------------------------------------------------
# High level convenience API used by the routes
# ----------------------------------------------------------------------

def generate(qr_data, options):
    """
    Build the QR matrix once and return a dict of renderers.

    `options` keys (all optional, sane defaults applied):
      size, fg_color, bg_color, border, error_correction,
      rounded, transparent, logo_bytes
    """
    size = int(options.get("size") or 400)
    fg_color = options.get("fg_color") or "#000000"
    bg_color = options.get("bg_color") or "#FFFFFF"
    border = int(options.get("border") if options.get("border") not in (None, "") else 4)
    error_correction = (options.get("error_correction") or "M").upper()
    rounded = bool(options.get("rounded"))
    transparent = bool(options.get("transparent"))
    logo_bytes = options.get("logo_bytes")

    # Logos need higher error correction to remain scannable.
    if logo_bytes and error_correction not in ("Q", "H"):
        error_correction = "H"

    matrix = get_qr_matrix(qr_data, error_correction=error_correction, border=border)

    render_opts = dict(
        size=size,
        fg_color=fg_color,
        bg_color=bg_color,
        rounded=rounded,
        transparent=transparent,
        logo_bytes=logo_bytes,
    )

    pil_img = render_pil_image(matrix, **render_opts)

    return {
        "matrix": matrix,
        "pil_image": pil_img,
        "png_bytes": lambda: pil_to_png_bytes(pil_img),
        "jpg_bytes": lambda: pil_to_jpg_bytes(pil_img, bg_color=bg_color),
        "svg_string": lambda: render_svg(matrix, **render_opts),
        "data_uri": lambda: pil_to_data_uri(pil_img),
        "error_correction_used": error_correction,
    }
