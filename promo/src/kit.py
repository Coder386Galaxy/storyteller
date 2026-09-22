"""Drawing primitives for the Storyteller CYOP promo film.

Everything renders with Pillow. Expensive, static things (rounded rectangles,
gradients, glows, shadows, texture) are pre-rendered at 3x and cached, so the
per-frame cost stays low enough to render a 30s / 30fps film in pure Python.
"""
from __future__ import annotations

import functools
import math
import re
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
EMOJI = os.path.join(ASSETS, "emoji")
PHOTOS = os.path.join(ASSETS, "photos")

# --- brand palette (mirrors index.html) -------------------------------------
INK = (44, 24, 16)  # #2c1810
INK_SOFT = (74, 44, 26)  # #4a2c1a
PARCH = (244, 236, 216)  # #f4ecd8
CARD = (250, 243, 227)  # #faf3e3
CREAM = (255, 248, 231)  # #fff8e7
GOLD = (184, 134, 11)  # #b8860b
GOLD_LT = (212, 160, 23)  # #d4a017
MAROON = (139, 37, 0)  # #8b2500
MAROON_LT = (201, 80, 42)  # #c9502a
RED = (153, 27, 27)  # #991b1b
GREEN = (21, 128, 61)  # #15803d
BROWN = (107, 76, 59)  # #6b4c3b
TAN = (212, 196, 168)  # #d4c4a8
VIOLET = (109, 40, 217)  # #6d28d9
BLUE = (37, 99, 235)  # #2563eb
BLACK = (13, 9, 6)


# --- math -------------------------------------------------------------------
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = clamp(t)
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = clamp(t)
    return t ** 3


def ease_out_quint(t):
    t = clamp(t)
    return 1 - (1 - t) ** 5


def ease_out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t, s=1.70158):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def ease_out_elastic(t):
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def seg(t, start, end):
    """Normalised progress of t inside [start, end]."""
    if end <= start:
        return 1.0 if t >= end else 0.0
    return clamp((t - start) / (end - start))


def ramp(t, start, end):
    return ease_out_cubic(seg(t, start, end))


def pulse(t, start, dur=0.35, rise=0.12):
    """Quick attack / slow release envelope, 0 outside [start, start+dur]."""
    dt = t - start
    if dt < 0 or dt > dur:
        return 0.0
    if dt < rise:
        return dt / rise
    return max(0.0, 1 - (dt - rise) / (dur - rise))


# --- cache ------------------------------------------------------------------
_CACHE: dict = {}


CACHE_LIMIT = 500


def _cached(key, build):
    hit = _CACHE.get(key)
    if hit is None:
        if len(_CACHE) >= CACHE_LIMIT:
            # animating sizes produce unique keys every frame; drop the lot
            # rather than let the process grow without bound
            _CACHE.clear()
            _EMOJI_CACHE.clear()
        hit = _CACHE[key] = build()
    return hit


def _ss_for(w, h, want=3):
    """Supersampling factor that keeps scratch images sane."""
    px = max(1, w) * max(1, h)
    if px < 60_000:
        return want
    if px < 400_000:
        return max(2, min(want, 2))
    return 1


def _ss(v):
    return max(1, int(round(v)))


# --- shapes -----------------------------------------------------------------
def rr(w, h, radius, fill=None, outline=None, ow=0, ss=3):
    """Anti-aliased rounded rectangle, rendered at ss x then downsampled."""
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    ss = _ss_for(w, h, ss)
    radius = int(round(radius))
    key = ("rr", w, h, radius, fill, outline, ow, ss)

    def build():
        im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pad = 0
        d.rounded_rectangle(
            [pad, pad, w * ss - 1 - pad, h * ss - 1 - pad],
            radius=max(0, radius * ss),
            fill=fill,
            outline=outline,
            width=int(round(ow * ss)),
        )
        return im.resize((w, h), Image.LANCZOS)

    return _cached(key, build)


def circle(d, fill=None, outline=None, ow=0, ss=4):
    d = max(1, int(round(d)))
    ss = _ss_for(d, d, ss)
    key = ("circle", d, fill, outline, ow, ss)

    def build():
        im = Image.new("RGBA", (d * ss, d * ss), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.ellipse(
            [0, 0, d * ss - 1, d * ss - 1],
            fill=fill,
            outline=outline,
            width=int(round(ow * ss)),
        )
        return im.resize((d, d), Image.LANCZOS)

    return _cached(key, build)


def ring(d, color=GOLD, width=3, ss=4):
    return circle(d, outline=color, ow=width, ss=ss)


def shadow(w, h, radius, blur=28, opacity=0.42, color=(20, 10, 5)):
    """Soft drop shadow shaped like a rounded rect. Returns (img, pad)."""
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    blur = int(round(blur))
    key = ("shadow", w, h, radius, blur, round(opacity, 3), color)

    def build():
        pad = blur * 2
        big = Image.new("L", (w + pad * 2, h + pad * 2), 0)
        ImageDraw.Draw(big).rounded_rectangle(
            [pad, pad, pad + w, pad + h], radius=radius, fill=int(255 * clamp(opacity))
        )
        big = big.filter(ImageFilter.GaussianBlur(blur))
        out = Image.new("RGBA", big.size, color + (0,))
        out.putalpha(big)
        return out, pad

    return _cached(key, build)


def gradient(size, c1, c2, direction="v"):
    """Linear gradient image."""
    w, h = int(size[0]), int(size[1])
    key = ("grad", w, h, c1, c2, direction)

    def build():
        if direction == "v":
            ramp = np.broadcast_to(np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None], (h, w))
        elif direction == "h":
            ramp = np.broadcast_to(np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :], (h, w))
        else:  # diagonal
            yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
            xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
            ramp = np.broadcast_to((yy + xx) / 2.0, (h, w))
        a = np.array(c1, dtype=np.float32)[None, None, :]
        b = np.array(c2, dtype=np.float32)[None, None, :]
        arr = a + (b - a) * ramp[..., None]
        return Image.fromarray(arr.astype(np.uint8), "RGB")

    return _cached(key, build)


def radial_glow(d, color=GOLD_LT, power=2.2, alpha=255):
    """Soft circular glow, additive-ish when alpha-composited."""
    d = max(2, int(round(d)))
    key = ("glow", d, color, round(power, 2))

    def build():
        y, x = np.mgrid[0:d, 0:d].astype(np.float32)
        c = (d - 1) / 2
        r = np.sqrt((x - c) ** 2 + (y - c) ** 2) / (d / 2)
        a = (np.clip(1 - r, 0, 1) ** power * alpha).astype(np.uint8)
        rgb = np.zeros((d, d, 3), np.uint8)
        rgb[..., 0], rgb[..., 1], rgb[..., 2] = color
        return Image.fromarray(np.dstack([rgb, a]), "RGBA")

    return _cached(key, build)


def vignette(size, strength=0.5, color=(0, 0, 0), power=1.7):
    w, h = int(size[0]), int(size[1])
    key = ("vig", w, h, round(strength, 3), color, round(power, 2))

    def build():
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2) / 1.4142
        a = (np.clip(r, 0, 1) ** power * 255 * strength).astype(np.uint8)
        rgb = np.zeros((h, w, 3), np.uint8)
        rgb[..., 0], rgb[..., 1], rgb[..., 2] = color
        return Image.fromarray(np.dstack([rgb, a]), "RGBA")

    return _cached(key, build)


def paper(size, base=PARCH, amount=16, seed=7):
    """Warm paper grain: blurred noise + fibre streaks, tiled alpha overlay."""
    w, h = int(size[0]), int(size[1])
    key = ("paper", w, h, base, amount, seed)

    def build():
        rs = np.random.RandomState(seed)
        n = rs.normal(0, 1, (h, w)).astype(np.float32)
        n = np.array(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(1.1)), dtype=np.float32
        ) / 255.0
        coarse = rs.normal(0, 1, (max(2, h // 8), max(2, w // 8))).astype(np.float32)
        coarse = np.array(
            Image.fromarray(((coarse * 0.5 + 0.5) * 255).astype(np.uint8))
            .resize((w, h), Image.BICUBIC)
            .filter(ImageFilter.GaussianBlur(3)),
            dtype=np.float32,
        ) / 255.0
        shade = (n * 0.55 + coarse * 0.45) - 0.5
        alpha = np.clip(np.abs(shade) * 2.0 * amount, 0, 255).astype(np.uint8)
        lum = np.where(shade > 0, 255, 0).astype(np.uint8)
        rgb = np.zeros((h, w, 3), np.uint8)
        rgb[..., 0] = np.where(lum == 255, 255, max(0, base[0] - 60))
        rgb[..., 1] = np.where(lum == 255, 250, max(0, base[1] - 60))
        rgb[..., 2] = np.where(lum == 255, 235, max(0, base[2] - 60))
        return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")

    return _cached(key, build)


def grain(size, count=6, amount=6, seed=11):
    """Small set of animated film-grain tiles."""
    w, h = int(size[0]), int(size[1])
    key = ("grain", w, h, count, amount, seed)

    def build():
        tiles = []
        rs = np.random.RandomState(seed)
        for _ in range(count):
            n = rs.normal(0, 1, (h, w)).astype(np.float32)
            n = np.array(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(0.7)), dtype=np.float32) / 255.0 * 2 - 1
            a = np.clip(np.abs(n) * amount * 2.2, 0, 255).astype(np.uint8)
            lum = (n > 0) * 255
            rgb = np.dstack([lum, lum, lum]).astype(np.uint8)
            tiles.append(Image.fromarray(np.dstack([rgb, a]), "RGBA"))
        return tiles

    return _cached(key, build)


# --- text -------------------------------------------------------------------
_FONT_CACHE: dict = {}
FONT_FILES = {
    "display": "PlayfairDisplay[wght].ttf",
    "display_i": "PlayfairDisplay-Italic[wght].ttf",
    "body": "LibreBaskerville[wght].ttf",
    "body_i": "LibreBaskerville-Italic[wght].ttf",
    "garamond": "EBGaramond[wght].ttf",
    "garamond_i": "EBGaramond-Italic[wght].ttf",
}
_WEIGHTS = {
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700,
    "black": 900,
}


def font(name="body", size=32, weight=None):
    size = max(1, int(round(size)))
    key = (name, size, weight)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    path = os.path.join(FONTS, FONT_FILES[name])
    f = ImageFont.truetype(path, size)
    if weight:
        w = _WEIGHTS.get(weight, weight) if isinstance(weight, str) else weight
        try:
            f.set_variation_by_axes([w])
        except Exception:
            pass
    _FONT_CACHE[key] = f
    return f


def tlen(font_obj, text):
    return font_obj.getlength(text)


def wrap(text, font_obj, maxw):
    """Greedy wrap honouring explicit newlines; maxw<=0 disables wrapping."""
    out = []
    for para in text.split("\n"):
        if maxw <= 0 or font_obj.getlength(para) <= maxw:
            out.append(para)
            continue
        line = ""
        for word in para.split(" "):
            trial = word if not line else line + " " + word
            if font_obj.getlength(trial) <= maxw or not line:
                line = trial
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def text_spaced(draw, xy, text, font_obj, fill, spacing=0.0, anchor="la", alpha=255):
    """Draw text with optional letter-spacing (spacing in px)."""
    if spacing <= 0:
        draw.text(xy, text, font=font_obj, fill=fill, anchor=anchor)
        return
    total = sum(font_obj.getlength(c) for c in text) + spacing * max(0, len(text) - 1)
    x, y = xy
    if anchor.startswith("m"):
        x -= total / 2
    elif anchor.startswith("r"):
        x -= total
    for c in text:
        draw.text((x, y), c, font=font_obj, fill=fill, anchor="l" + anchor[1])
        x += font_obj.getlength(c) + spacing


def draw_para(draw, xy, lines, font_obj, fill, line_h, align="left", maxw=0):
    x, y = xy
    for i, ln in enumerate(lines):
        if align == "center":
            draw.text((x + maxw / 2, y + i * line_h), ln, font=font_obj, fill=fill, anchor="ma")
        else:
            draw.text((x, y + i * line_h), ln, font=font_obj, fill=fill)
    return y + len(lines) * line_h


_ORNAMENT = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002190-\U000021FF"
    "\U0000FE0F\U00002B00-\U00002BFF\U0001F1E6-\U0001F1FF]+"
)


def strip_emoji(s: str) -> str:
    """Drop emoji/ornament glyphs so fallback fonts never draw tofu boxes."""
    return _ORNAMENT.sub("", s).replace("  ", " ").strip()


def typewriter(text, progress):
    """Visible portion of text for a 0..1 typing progress."""
    n = int(round(len(text) * clamp(progress)))
    return text[:n]


# --- emoji ------------------------------------------------------------------
_EMOJI_CACHE: dict = {}


_BLANK = None


def code_for(sym: str) -> str:
    """'🏠' -> '1F3E0' (OpenMoji file naming: uppercased codepoints, no FE0F)."""
    if all(ch in "0123456789ABCDEF-" for ch in sym) and len(sym) > 3:
        return sym
    cps = [c for c in ("%X" % ord(ch) for ch in sym) if c != "FE0F"]
    return "-".join(cps)


def emoji(code, size):
    """Load a cached OpenMoji sprite (codepoint string or emoji char)."""
    global _BLANK
    size = max(2, int(round(size)))
    code = code_for(code) if not isinstance(code, str) or len(code) < 4 else code
    key = (code, size)
    if key in _EMOJI_CACHE:
        return _EMOJI_CACHE[key]
    path = os.path.join(EMOJI, f"{code}.png")
    if not os.path.exists(path):
        if _BLANK is None:
            _BLANK = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        return _BLANK.resize((size, size), Image.NEAREST)
    im = Image.open(path).convert("RGBA")
    if size != im.width:
        im = im.resize((size, size), Image.LANCZOS)
    _EMOJI_CACHE[key] = im
    return im


def paste(base: Image.Image, img: Image.Image, xy, alpha=255):
    x, y = int(round(xy[0])), int(round(xy[1]))
    if alpha < 255:
        img = _with_alpha(img, alpha)
    if base.mode == "RGBA":
        base.alpha_composite(img, (max(-4000, x), max(-4000, y)))
    else:
        base.paste(img, (x, y), img)


def paste_c(base: Image.Image, img: Image.Image, cx, cy, alpha=255):
    paste(base, img, (cx - img.width / 2, cy - img.height / 2), alpha)


def _with_alpha(img: Image.Image, alpha):
    if alpha >= 255:
        return img
    out = img.copy()
    a = np.asarray(out.getchannel("A"), dtype=np.uint16)
    out.putalpha(Image.fromarray(((a * max(0, alpha)) // 255).astype(np.uint8), "L"))
    return out


def alpha_mix(img, alpha):
    return _with_alpha(img, alpha)


def fit(img: Image.Image, w=None, h=None):
    if w and not h:
        h = int(round(img.height * w / img.width))
    if h and not w:
        w = int(round(img.width * h / img.height))
    return img.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)


def cover(img: Image.Image, size):
    """Scale + center-crop to exactly fill size."""
    tw, th = int(size[0]), int(size[1])
    s = max(tw / img.width, th / img.height)
    im = img.resize((max(1, int(img.width * s + 0.5)), max(1, int(img.height * s + 0.5))), Image.LANCZOS)
    x = (im.width - tw) // 2
    y = (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def rounded(img: Image.Image, radius):
    mask = rr(img.width, img.height, radius, fill=(255, 255, 255, 255))
    out = img.convert("RGBA")
    out.putalpha(ImageChops.multiply(out.getchannel("A"), mask.getchannel("A")))
    return out


def screen_blend(base, img, alpha=255):
    """Approximate additive light bloom without numpy per-frame cost."""
    if alpha < 255:
        img = _with_alpha(img, alpha)
    base.alpha_composite(img)
