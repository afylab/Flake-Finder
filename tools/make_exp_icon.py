"""The experimental-version icon: the logo with an orange "EXP" badge (2026-11-27).

    python3 tools/make_exp_icon.py

Writes flakeid/scope/assets/logo_exp_<n>.png and logo_exp.ico from logo_<n>.png.  The scan program shows it (window,
taskbar) when the installed version is not from the main branch (flakeid/scope/update.py: experimental), and an update
to such a branch copies logo_exp.ico over logo.ico so the desktop shortcut shows it too.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[1] / "flakeid" / "scope" / "assets"
SIZES = (256, 128, 64, 48, 32, 24, 16)
ORANGE, WHITE = (242, 133, 26, 255), (255, 255, 255, 255)
FONTS = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
         "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def font(px):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default()


def badge(im):
    """The badge drawn at 4x and scaled down (smooth edges): a pill with EXP from 48 px up, a dot below."""
    n = im.width
    big = n * 4
    ov = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if n >= 48:
        h, w = int(big * 0.30), int(big * 0.66)
        x0, y0 = int(big * 0.02), big - h - int(big * 0.02)
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=h // 2, fill=ORANGE, outline=WHITE, width=max(4, big // 48))
        f = font(int(h * 0.62))
        tw, th = d.textbbox((0, 0), "EXP", font=f)[2:]
        d.text((x0 + (w - tw) // 2, y0 + (h - th) // 2 - int(h * 0.06)), "EXP", font=f, fill=WHITE)
    else:
        r = int(big * 0.27)
        cx, cy = r + int(big * 0.01), big - r - int(big * 0.01)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE, outline=WHITE, width=max(4, big // 12))
    return Image.alpha_composite(im.convert("RGBA"), ov.resize((n, n), Image.LANCZOS))


def main():
    out = {}
    for n in SIZES:
        src = ASSETS / f"logo_{n}.png"
        im = Image.open(src) if src.is_file() else Image.open(ASSETS / "logo_256.png").resize((n, n), Image.LANCZOS)
        out[n] = badge(im.convert("RGBA").resize((n, n), Image.LANCZOS))
        out[n].save(ASSETS / f"logo_exp_{n}.png")
    out[256].save(ASSETS / "logo_exp.ico", sizes=[(n, n) for n in SIZES])
    print("wrote", ", ".join(f"logo_exp_{n}.png" for n in SIZES), "and logo_exp.ico in", ASSETS)


if __name__ == "__main__":
    main()
