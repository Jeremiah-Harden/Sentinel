"""Generate the Job Scout app icon — cursive gold J on dark navy."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PRIORITY = [
    "C:/Windows/Fonts/VIVALDII.TTF",      # Vivaldi — most elegant
    "C:/Windows/Fonts/ITCEDSCR.TTF",      # ITC Edwardian Script
    "C:/Windows/Fonts/KUNSTLER.TTF",      # Kunstler Script
    "C:/Windows/Fonts/MTCORSVA.TTF",      # Monotype Corsiva
    "C:/Windows/Fonts/SCRIPTBL.TTF",      # Script Bold
]

NAVY      = (10, 22, 48, 255)
GOLD      = (255, 210, 0, 255)
GOLD_DARK = (180, 140, 20, 255)
GOLD_MID  = (212, 175, 55, 255)
GOLD_HI   = (255, 248, 180, 220)
SHADOW    = (60, 45, 0, 200)


def build(size=512, output="assets/job_scout.ico"):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background circle ──────────────────────────────────────────────────
    pad = 8
    draw.ellipse([pad, pad, size - pad, size - pad], fill=NAVY)

    # ── Gold double ring ───────────────────────────────────────────────────
    draw.ellipse([pad, pad, size - pad, size - pad],
                 outline=GOLD_MID, width=14)
    inner = pad + 18
    draw.ellipse([inner, inner, size - inner, size - inner],
                 outline=(255, 215, 0, 120), width=3)

    # ── Load font ──────────────────────────────────────────────────────────
    font = None
    used = None
    for path in FONT_PRIORITY:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, int(size * 0.74))
                used = path
                break
            except Exception:
                pass
    if font is None:
        raise RuntimeError("No cursive font found.")
    print(f"Font: {used}")

    # ── Measure and center the J ───────────────────────────────────────────
    bbox = draw.textbbox((0, 0), "J", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - int(size * 0.04)

    # ── Glow layer ─────────────────────────────────────────────────────────
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), "J", font=font, fill=(255, 200, 0, 140))
    for radius in (28, 18, 10):
        blurred = glow.filter(ImageFilter.GaussianBlur(radius=radius))
        img = Image.alpha_composite(img, blurred)

    draw = ImageDraw.Draw(img)

    # ── Shadow ─────────────────────────────────────────────────────────────
    draw.text((x + 5, y + 6), "J", font=font, fill=SHADOW)

    # ── Main J — layered for depth ─────────────────────────────────────────
    draw.text((x + 2, y + 2), "J", font=font, fill=GOLD_DARK)   # base
    draw.text((x,     y),     "J", font=font, fill=GOLD)         # mid
    draw.text((x - 2, y - 2), "J", font=font, fill=GOLD_HI)     # highlight

    # ── Save as .ico ───────────────────────────────────────────────────────
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 48, 64, 128, 256]
    frames = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    frames[0].save(
        output,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Saved: {output}")
    return output


if __name__ == "__main__":
    build()
