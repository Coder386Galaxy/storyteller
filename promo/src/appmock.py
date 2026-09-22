"""A faithful, animatable mockup of the Storyteller CYOP app UI.

Everything is authored in the app's real CSS-pixel space (a 430 x 932 phone
viewport) at the app's real type scale (16px body, 2em hero), and rasterised at
a device scale — so the ad shows the product at phone size exactly as a reader
would see it: same palette, same components, same copy as index.html.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageChops, ImageDraw

from kit import (
    ASSETS,
    strip_emoji,
    BLUE,
    BROWN,
    CARD,
    CREAM,
    GOLD,
    GOLD_LT,
    GREEN,
    INK,
    INK_SOFT,
    MAROON,
    MAROON_LT,
    PARCH,
    PHOTOS,
    RED,
    TAN,
    VIOLET,
    circle,
    clamp,
    cover,
    ease_out_cubic,
    emoji as emoji_img,
    fit,
    font,
    gradient,
    mix,
    paste,
    paste_c,
    radial_glow,
    rr,
    rounded,
    seg,
    shadow,
    text_spaced,
    wrap,
)

APP_W = 430.0
APP_H = 932.0
CHROME_TOP = 30.0   # status bar (over the header)
CHROME_BOT = 44.0   # safari url bar
HEADER_H = 96.0
NAV_H = 46.0
CONTENT_TOP = HEADER_H + NAV_H
VIEW_H = APP_H - CHROME_BOT
WIN_H = VIEW_H - CONTENT_TOP  # visible content height

_URL = "coder386galaxy.github.io/storyteller"

# screen/content-space css coordinates of animatable targets, refreshed every
# render. Content-space entries (prefixed "c_") are relative to the top of the
# scrolling content area; draw_* helpers use plain screen space.
HIT: dict = {}
_LOGO = os.path.join(ASSETS, "icon-512.png")


# --------------------------------------------------------------------------
# drawing context (css coordinates -> device pixels)
# --------------------------------------------------------------------------
class Ctx:
    def __init__(self, w_css, h_css, scale, bg=(0, 0, 0, 0)):
        self.s = scale
        self.w_css, self.h_css = w_css, h_css
        self.w = max(1, int(round(w_css * scale)))
        self.h = max(1, int(round(h_css * scale)))
        self.img = Image.new("RGBA", (self.w, self.h), bg if len(bg) == 4 else bg + (255,))
        self.d = ImageDraw.Draw(self.img)

    def L(self, v):
        return v * self.s

    def P(self, x, y):
        return (x * self.s, y * self.s)

    def rect(self, x, y, w, h, radius=0, fill=None, outline=None, ow=1, alpha=255):
        img = rr(self.L(w), self.L(h), self.L(radius), fill=fill, outline=outline, ow=self.L(ow))
        paste(self.img, img, self.P(x, y), alpha)

    def circle_at(self, cx, cy, d, fill=None, outline=None, ow=1, alpha=255):
        img = circle(self.L(d), fill=fill, outline=outline, ow=self.L(ow))
        paste_c(self.img, img, self.L(cx), self.L(cy), alpha)

    def line(self, pts, fill, width=1.0):
        self.d.line([(x * self.s, y * self.s) for x, y in pts], fill=fill,
                    width=max(1, int(round(width * self.s))))

    def arrow(self, x, y, length, color=GOLD, thickness=1.8, alpha=255):
        """Vector right-arrow, centred vertically on y."""
        col = color + (alpha,) if len(color) == 3 else color
        head = max(4.0, length * 0.40)
        w = max(1, int(round(thickness * self.s)))
        self.d.line([(self.L(x), self.L(y)), (self.L(x + length - head * 0.6), self.L(y))],
                    fill=col, width=w)
        self.d.line([(self.L(x + length - head), self.L(y - head * 0.52)),
                     (self.L(x + length), self.L(y)),
                     (self.L(x + length - head), self.L(y + head * 0.52))],
                    fill=col, width=w, joint="curve")

    def play_tri(self, cx, cy, size, color=INK, alpha=255):
        col = color + (alpha,) if len(color) == 3 else color
        h = size * 0.46
        self.d.polygon([(self.L(cx - size * 0.34), self.L(cy - h)),
                        (self.L(cx - size * 0.34), self.L(cy + h)),
                        (self.L(cx + size * 0.52), self.L(cy))], fill=col)

    def row_arrow(self, cx, y, left, right, size=25, color=MAROON, name="display",
                  weight="bold", arrow_color=GOLD, alpha=255):
        """'Paste Story -> AI Finalizes' style paired heading, centred on cx."""
        f = self.font(size, name, weight)
        lw = f.getlength(left) / self.s
        rw = f.getlength(right) / self.s
        aw = size * 0.9
        gap = size * 0.32
        total = lw + gap + aw + gap + rw
        x0 = cx - total / 2
        self.text(x0, y, left, size=size, color=color, name=name, weight=weight, alpha=alpha)
        self.arrow(x0 + lw + gap, y + size * 0.60, aw, arrow_color, max(1.6, size * 0.072), alpha)
        self.text(x0 + lw + gap + aw + gap, y, right, size=size, color=color, name=name,
                  weight=weight, alpha=alpha)
        return total

    def bezier(self, p0, p1, p2, p3, fill, width=1.5, n=24):
        pts = []
        for i in range(n + 1):
            t = i / n
            u = 1 - t
            pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                        u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
        self.line(pts, fill, width)

    # type
    def font(self, size, name="body", weight="regular"):
        return font(name, self.L(size), weight)

    def text(self, x, y, s, size=16, color=INK, name="body", weight="regular",
             anchor="la", spacing=0.0, alpha=255):
        f = self.font(size, name, weight)
        col = color if len(color) == 4 else color + (alpha,)
        s = strip_emoji(s)
        if not s:
            return
        if spacing:
            text_spaced(self.d, (self.L(x), self.L(y)), s, f, col, self.L(spacing), anchor)
        else:
            self.d.text((self.L(x), self.L(y)), s, font=f, fill=col, anchor=anchor)

    def para(self, x, y, s, maxw_css, line_h, size=16, color=INK, name="body",
             weight="regular", alpha=255, align="left", cx=None):
        s = strip_emoji(s)
        f = self.font(size, name, weight)
        lines = wrap(s, f, self.L(maxw_css))
        col = color + (alpha,) if len(color) == 3 else color
        for i, ln in enumerate(lines):
            ax = self.L(x) if align == "left" else self.L(cx) - f.getlength(ln) / 2
            self.d.text((ax, self.L(y + i * line_h)), ln, font=f, fill=col)
        return y + len(lines) * line_h

    # emoji
    def emo(self, code, x, y, size, alpha=255, anchor="lt"):
        im = emoji_img(code, self.L(size))
        if anchor == "lt":
            px, py = self.P(x, y)
        elif anchor == "ct":
            px, py = self.L(x) - im.width / 2, self.L(y)
        elif anchor == "lm":
            px, py = self.P(x, y - size / 2)
        else:
            px, py = self.L(x) - im.width / 2, self.L(y) - im.height / 2
        paste(self.img, im, (px, py), alpha)

    def emo_c(self, code, cx, cy, size, alpha=255):
        self.emo(code, cx, cy, size, alpha, anchor="cc")

    def photo(self, path, x, y, w, h, radius=8, alpha=255):
        im = cover(_photo(path), (int(self.L(w)), int(self.L(h))))
        paste(self.img, rounded(im, int(self.L(radius))), self.P(x, y), alpha)

    def btn(self, x, y, w, h, label, fill=GOLD, color=INK, radius=9, size=16,
            weight="bold", icon=None, border=None, alpha=255, icon_size=None):
        self.rect(x, y, w, h, radius, fill=fill, outline=border, ow=1.5, alpha=alpha)
        cx = x + w / 2
        if icon:
            iw = icon_size or size * 1.3
            tw = self.font(size, weight=weight).getlength(label) / self.s
            gap = size * 0.42
            total = iw + gap + tw
            self.emo(icon, cx - total / 2 + iw / 2, y + h / 2, iw, alpha, anchor="cc")
            self.text(cx - total / 2 + iw + gap, y + h / 2, label, size=size, color=color,
                      weight=weight, anchor="lm", alpha=alpha)
        else:
            self.text(cx, y + h / 2, label, size=size, color=color, weight=weight,
                      anchor="mm", alpha=alpha)
        return (x, y, w, h)

    def badge(self, x, y, label, fill=GOLD, color=INK, size=12, padx=9, h=24, radius=12,
              icon=None, alpha=255, border=None, tri=False):
        f = self.font(size, weight="bold")
        tw = f.getlength(label) / self.s + (size * 1.35 if icon else 0)
        tw += size * 1.25 if tri else 0
        w = tw + padx * 2
        self.rect(x, y, w, h, radius, fill=fill, outline=border, ow=1.2, alpha=alpha)
        if tri:
            self.play_tri(x + padx + size * 0.42, y + h / 2, size * 0.92, color, alpha)
            self.text(x + padx + size * 1.25, y + h / 2, label, size=size, color=color,
                      weight="bold", anchor="lm", alpha=alpha)
        elif icon:
            self.emo(icon, x + padx + size * 0.6, y + h / 2, size * 1.1, alpha, anchor="cc")
            self.text(x + padx + size * 1.35, y + h / 2, label, size=size, color=color,
                      weight="bold", anchor="lm", alpha=alpha)
        else:
            self.text(x + w / 2, y + h / 2, label, size=size, color=color, weight="bold",
                      anchor="mm", alpha=alpha)
        return w


_PHOTO_CACHE = {}


def _photo(path):
    if path not in _PHOTO_CACHE:
        p = os.path.join(PHOTOS, path) if not os.path.isabs(path) else path
        im = Image.open(p).convert("RGB")
        bx, by = int(im.width * 0.055), int(im.height * 0.075)
        _PHOTO_CACHE[path] = im.crop((bx, by, im.width - bx, im.height - by))
    return _PHOTO_CACHE[path]


def logo(size):
    key = ("logo", int(size))
    if key not in _PHOTO_CACHE:
        _PHOTO_CACHE[key] = Image.open(_LOGO).convert("RGBA").resize(
            (int(size), int(size)), Image.LANCZOS)
    return _PHOTO_CACHE[key]


# --------------------------------------------------------------------------
# app chrome
# --------------------------------------------------------------------------
TABS = [("home", "1F3E0", "Home"), ("build", "1F500", "Build"),
        ("convert", "2728", "AI Convert"), ("lib", "1F4DA", "Library")]


def draw_header(c: Ctx, t=0.0, install_pulse=0.0):
    """Ink header. The app ships black-translucent status bar chrome, so the
    status bar sits *inside* the header block, exactly as on a real phone."""
    c.rect(0, 0, APP_W, HEADER_H, 0, fill=INK)
    paste(c.img, gradient((c.w, int(c.L(HEADER_H))), INK, INK_SOFT, "d").convert("RGBA"), (0, 0))
    c.line([(0, HEADER_H - 2.5), (APP_W, HEADER_H - 2.5)], GOLD, 2.5)
    paste(c.img, rounded(logo(c.L(38)), c.L(8)), c.P(14, 44))
    c.text(60, 42, "STORYTELLER", size=23, color=PARCH, name="display", weight="bold", spacing=0.8)
    c.text(61, 68, "WRITE YOUR OWN", size=9.5, color=GOLD_LT, name="garamond", spacing=2.6)
    # install + age pills
    a = 255 if install_pulse else 235
    c.rect(APP_W - 100, 47, 62, 27, 7, fill=GOLD, alpha=a)
    c.emo("1F4F1", APP_W - 90, 60, 16, anchor="cc")
    c.text(APP_W - 58, 60, "Install", size=12, color=INK, weight="bold", anchor="mm")
    c.rect(APP_W - 164, 48, 58, 25, 12, fill=(255, 255, 255, 55),
           outline=(255, 255, 255, 95), ow=1)
    c.emo("1F464", APP_W - 154, 60, 13, anchor="cc")
    c.text(APP_W - 140, 60, "Age 14", size=11, color=PARCH, anchor="lm")


def draw_nav(c: Ctx, active="home", t=0.0):
    y = HEADER_H
    c.rect(0, y, APP_W, NAV_H, 0, fill=CARD)
    c.line([(0, y + NAV_H), (APP_W, y + NAV_H)], TAN, 2)
    x = 4
    for key, icon, label in TABS:
        f = c.font(15)
        lw = f.getlength(label) / c.s
        w = lw + 38
        on = key == active
        col = (VIOLET if on else mix(VIOLET, BROWN, 0.3)) if key == "convert" else \
              (MAROON if on else INK)
        c.emo(icon, x + 16, y + NAV_H / 2, 16, anchor="cc")
        c.text(x + 29, y + NAV_H / 2, label, size=15, color=col,
               weight="bold" if on else "regular", anchor="lm")
        if key == "lib":
            bx = x + 29 + lw + 5
            c.rect(bx, y + NAV_H / 2 - 10, 21, 20, 10, fill=GOLD)
            c.text(bx + 10.5, y + NAV_H / 2, "3", size=11, color=INK, weight="bold", anchor="mm")
        if on:
            c.rect(x, y + NAV_H - 3, w, 3, 0, fill=VIOLET if key == "convert" else MAROON)
        x += w + 1


# --------------------------------------------------------------------------
# tab content — authored at the app's real type scale
# --------------------------------------------------------------------------
# content-relative y of the things the camera targets
BUILD_CHOICE_Y = [438, 490, 542]
HOME_CTA_Y = 180


def content_home(c: Ctx, st, t):
    y = 20
    c.text(APP_W / 2, y, "Storyteller CYOP", size=28, color=MAROON, name="display",
           weight="bold", anchor="ma")
    tw = c.font(28, "display", "bold").getlength("Storyteller CYOP") / c.s
    c.emo("2728", APP_W / 2 - tw / 2 - 13, y + 3, 22, anchor="cc")
    c.emo("2728", APP_W / 2 + tw / 2 + 13, y + 3, 22, anchor="cc")
    y += 40
    c.text(APP_W / 2, y, "Write Your Own Adventure", size=25, color=MAROON, name="display",
           weight="bold", anchor="ma")
    y += 36
    y = c.para(APP_W / 2 - 165, y, "Build branching choose-your-own-path stories right in your "
               "browser. Write scenes, add choices,", 330, 20, size=15, color=BROWN,
               name="garamond_i", align="center", cx=APP_W / 2)
    y = c.para(APP_W / 2 - 165, y, "end in death or victory.", 330, 20, size=15, color=BROWN,
               name="garamond_i", align="center", cx=APP_W / 2)
    y += 18
    hl = int(28 * (0.5 + 0.5 * math.sin(t * 7.0))) if st.get("hl_start") else 0
    c.btn(20, y, 390, 52, "Start writing", fill=mix(GOLD, GOLD_LT, hl / 28 * 0.85), size=19,
          radius=10, icon="1F4DD", icon_size=24)
    HIT["c_start_btn"] = (215, y + 26)
    y += 62
    c.btn(20, y, 390, 50, "Paste a story — AI finalizes it", fill=mix(VIOLET, BLUE, 0.45),
          color=(255, 255, 255), size=17, radius=10, icon="2728", icon_size=21)
    HIT["c_ai_btn"] = (215, y + 25)
    y += 60
    c.btn(20, y, 390, 46, "Play your story", fill=MAROON, color=(255, 255, 255), size=16, radius=10,
          icon="25B6", icon_size=18)
    HIT["c_play_btn"] = (215, y + 23)
    y += 62
    tiles = [("1F500", "Build", "Write passages. Add choices, branches, death, and victory endings."),
             ("2728", "AI Convert", "Paste a story — with or without inline choices."),
             ("1F4DA", "Library", "Published stories grouped by series, real play counts."),
             ("25B6", "Play", "Test your adventure, or import a friend's share code.")]
    tw, th = 190, 158
    for i, (ic, h, p) in enumerate(tiles):
        x = 20 + (i % 2) * (tw + 10)
        yy = y + (i // 2) * (th + 10)
        c.rect(x, yy, tw, th, 11, fill=CARD, outline=TAN, ow=1.6)
        c.emo_c(ic, x + tw / 2, yy + 34, 40)
        c.text(x + tw / 2, yy + 60, h, size=20, color=MAROON, name="display", weight="bold",
               anchor="ma")
        c.para(x + 14, yy + 92, p, tw - 28, 19, size=14, color=BROWN, name="garamond")
    y += 2 * (th + 10) + 12
    c.rect(20, y, 390, 250, 11, fill=CARD, outline=TAN, ow=1.6)
    c.emo("1F3AF", 44, y + 26, 22, anchor="cc")
    c.text(60, y + 16, "How it works", size=20, color=MAROON, name="display", weight="bold")
    steps = ["Hit Start writing — a passage named start is waiting.",
             "Write a scene. Use Continue, or + Add Choice to branch.",
             "Each choice can lead to a death or victory ending.",
             "Publish: AI age-rates it and saves it to your library.",
             "Share with a friend — they paste your code and play."]
    yy = y + 52
    for i, s in enumerate(steps):
        c.text(34, yy, f"{i + 1}.", size=14, color=MAROON, weight="bold")
        yy = c.para(48, yy, s, 340, 19, size=14, color=BROWN, name="garamond") + 8
    return y + 275


def content_build(c: Ctx, st, t):
    y = 16
    c.rect(20, y, 390, 64, 10, fill=CARD, outline=TAN, ow=1.6)
    c.text(34, y + 10, "STORY TITLE", size=11, color=MAROON, weight="bold", spacing=0.8)
    c.text(34, y + 30, "The Lantern on Blackrock Point", size=20, color=INK, name="display")
    y += 76
    c.text(20, y, "PASSAGES", size=11, color=BROWN, weight="bold", spacing=1.4)
    y += 18
    chips = ["start", "lantern", "rocks", "harbor"]
    x = 20
    for i, label in enumerate(chips):
        k = seg(st.get("chips_reveal", 1.0), i * 0.12, i * 0.12 + 0.3)
        if k <= 0:
            continue
        on = i == st.get("chip_active", 0)
        w = 22 + c.font(15, weight="bold").getlength(label) / c.s
        c.rect(x, y, w, 34, 17, fill=CREAM if on else (255, 255, 255, 230),
               outline=GOLD if on else TAN, ow=2.2 if on else 1.6)
        c.text(x + w / 2, y + 17, label, size=15, color=MAROON if on else BROWN, weight="bold",
               anchor="mm")
        HIT[f"c_chip_{label}"] = (x + w / 2, y + 17)
        x += w + 8
    y += 46
    card_y = y
    c.rect(20, y, 390, 420, 11, fill=CARD, outline=TAN, ow=1.6)
    c.text(34, y + 14, "PASSAGE TEXT", size=11, color=MAROON, weight="bold", spacing=0.8)
    c.rect(32, y + 32, 366, 130, 8, fill=(255, 255, 255, 255), outline=TAN, ow=1.3)
    body = ("The lighthouse door is already open.\n"
            "A gull screams somewhere behind the fog.\n"
            "Inside, a lantern still burns.")
    shown = body[: int(round(len(body) * clamp(st.get("type_p", 0.0))))]
    c.para(42, y + 42, shown, 348, 23, size=16, color=INK, name="garamond")
    if st.get("caret") and int(t * 2) % 2 == 0:
        lines = shown.split("\n")
        f = c.font(16, "garamond")
        lx = 42 + f.getlength(lines[-1]) / c.s
        ly = y + 42 + (len(lines) - 1) * 23
        c.rect(lx + 2, ly + 3, 1.6, 18, 0, fill=MAROON)
    c.text(34, y + 178, "WHAT KIND OF PASSAGE IS THIS?", size=11, color=MAROON, weight="bold")
    types = [("1F4D6", "Normal", 0), ("1F4AC", "Continue", 1), ("1F480", "Death", 2),
             ("1F3C6", "Victory", 3)]
    x = 32
    for ic, label, idx in types:
        on = idx == st.get("ptype", 0)
        w = 24 + c.font(14, weight="bold").getlength(label) / c.s + 12
        c.rect(x, y + 196, w, 34, 8, fill=CREAM if on else (255, 255, 255, 235),
               outline=GOLD if on else TAN, ow=1.8)
        c.emo(ic, x + 16, y + 213, 15, anchor="cc")
        c.text(x + 26, y + 213, label, size=14, color=MAROON if on else BROWN, weight="bold",
               anchor="lm")
        x += w + 5
    c.text(34, y + 242, "CHOICES", size=11, color=MAROON, weight="bold", spacing=0.8)
    rev = st.get("choices_reveal", 0.0)
    # register all three rows up-front so the camera can aim before they animate in
    for _j, _l in enumerate("ABC"):
        HIT[f"c_choice_{_l}"] = (215, y + 260 + _j * 52 + 22)
    choices = [("A", "Take the lantern and step inside", "lantern"),
               ("B", "Search the rocks below", "rocks"),
               ("C", "Row back to the harbor", "harbor")]
    cy = y + 260
    for i, (letter, text, tgt) in enumerate(choices):
        k = seg(rev, i * 0.16, i * 0.16 + 0.42)
        h = 44 if k > 0 else 0
        if k <= 0:
            continue
        e = ease_out_cubic(k)
        sel = st.get("choice_sel") == i
        c.rect(32, cy, 366, h * e, 8, fill=CREAM if sel else (255, 255, 255, 240),
               outline=GOLD if sel else TAN, ow=2.2 if sel else 1.3)
        if e > 0.45:
            c.circle_at(52, cy + 22, 26, fill=MAROON)
            c.text(52, cy + 22, letter, size=13, color=(255, 255, 255), weight="bold", anchor="mm")
            c.text(70, cy + 22, text, size=14.5, color=INK, name="garamond", anchor="lm")
            c.text(386, cy + 22, f"→ {tgt}", size=12.5, color=MAROON, name="garamond_i",
                   anchor="rm")
        HIT[f"c_choice_{letter}"] = (215, cy + 22)
        cy += 52
    y += 432
    c.btn(20, y, 390, 44, "Add Choice", fill=TAN, color=INK, size=15, radius=10)
    y += 54
    c.rect(20, y, 390, 40, 9, fill=(255, 255, 255, 205), outline=TAN, ow=1.3)
    c.text(34, y + 20, "4 passages · 3 choices · autosaves as you type", size=13.5, color=BROWN,
           name="garamond_i", anchor="lm")
    return y + 60


def content_convert(c: Ctx, st, t):
    y = 16
    c.row_arrow(APP_W / 2 + 16, y, "Paste Story", "AI Finalizes", size=25)
    c.emo("2728", APP_W / 2 - 168, y + 16, 26, anchor="cc")
    y += 36
    y = c.para(APP_W / 2 - 190, y, "Paste your writing and your choices below. AI connects "
               "everything into a playable CYOP — adding Continue → links, filling in missing "
               "endings, wiring your choices.", 380, 20, size=14.5, color=BROWN,
               name="garamond_i")
    y += 14
    c.text(20, y, "PASTE YOUR STORY (WITH OR WITHOUT CHOICES)", size=11, color=MAROON,
           weight="bold", spacing=0.8)
    y += 18
    c.rect(20, y, 390, 224, 9, fill=(255, 254, 249, 255), outline=TAN, ow=1.6)
    paste_text = ("You wake on a strange shore. Far off, a lantern\n"
                  "burns in the window of the lighthouse.\n"
                  "\n"
                  "A) Take the lantern and step inside\n"
                  "B) Search the rocks below\n"
                  "C) Row back to the harbor")
    shown = paste_text[: int(round(len(paste_text) * clamp(st.get("paste_p", 0.0))))]
    c.para(32, y + 14, shown, 366, 22, size=15, color=INK, name="garamond")
    y += 240
    c.btn(20, y, 250, 48, "Finalize Into CYOP", fill=mix(VIOLET, BLUE, 0.45), color=(255, 255, 255),
          size=15.5, icon="2728", icon_size=19)
    HIT["c_finalize_btn"] = (145, y + 24)
    c.btn(280, y, 130, 48, "Load example", fill=(236, 236, 236), color=INK, size=13, icon="1F4C4",
          icon_size=15)
    y += 64
    done = st.get("done", 0.0)
    c.rect(20, y, 390, 300, 11, fill=CARD, outline=GOLD if done > 0.5 else TAN,
           ow=2.2 if done > 0.5 else 1.6)
    if done < 0.5:
        c.emo("1F9E0", 52, y + 40, 40, anchor="cc")
        status = ["Reading your story…", "Parsing scenes into passages…",
                  "Wiring choices to their branches…", "Planting 💀 death and 🏆 victory endings…"][
            int(t * 1.6) % 4]
        c.text(82, y + 28, "AI Finalizing…", size=17, color=VIOLET, weight="bold", anchor="lm")
        c.text(82, y + 52, status, size=14, color=BROWN, name="garamond_i", anchor="lm")
        p = clamp(st.get("prog", 0.0))
        c.rect(34, y + 80, 362, 12, 6, fill=(255, 255, 255, 240), outline=TAN, ow=1.2)
        c.rect(34, y + 80, max(6, 362 * p), 12, 6, fill=mix(GOLD, GOLD_LT, 0.5))
        for i in range(3):
            a = 90 + int(160 * (0.5 + 0.5 * math.sin(t * 5 - i * 0.9)))
            c.circle_at(APP_W / 2 - 18 + i * 18, y + 118, 11, fill=(139, 37, 0, a))
        for i, ln in enumerate(["Each paragraph becomes a scene, chained with Continue.",
                                "A)/B)/bullets become real path buttons.",
                                "Loose ends resolve into clean endings."]):
            c.text(40, y + 150 + i * 24, "•  " + ln, size=13.5, color=BROWN, name="garamond")
    else:
        c.rect(20, y, 390, 300, 11, fill=CARD, outline=GOLD, ow=2.2)
        c.circle_at(60, y + 44, 44, fill=GREEN)
        c.emo("2705", 60, y + 44, 30, anchor="cc")
        HIT["c_ready"] = (60, y + 44)
        c.text(94, y + 32, "Ready to play!", size=19, color=GREEN, weight="bold")
        c.text(94, y + 54, "6 passages · 3 choices · 2 endings", size=13.5, color=BROWN,
               name="garamond_i")
        gx, gy = 44, y + 100
        nodes = [("start", 0, 0), ("lantern", 1, -1), ("rocks", 1, 0), ("harbor", 1, 1),
                 ("victory", 2, -1), ("death", 2, 1)]
        pos = {n: (gx + col * 130 + 30, gy + 60 + row * 42) for n, col, row in nodes}
        gp = ease_out_cubic(clamp(st.get("graph", 0.0)))
        edges = [("start", "lantern"), ("start", "rocks"), ("start", "harbor"),
                 ("lantern", "victory"), ("rocks", "death"), ("harbor", "victory")]
        for i, (a, b) in enumerate(edges):
            k = clamp(gp * len(edges) - i)
            if k <= 0:
                continue
            x0, y0 = pos[a]
            x1, y1 = pos[b]
            mx = (x0 + x1) / 2
            c.bezier((x0 + 17, y0), (mx - 8, y0), (mx + 8, y1), (x1 - 17, y1), fill=GOLD,
                     width=1.7, n=int(10 + 16 * k))
        for name, col, row in nodes:
            px, py = pos[name]
            k = clamp(gp * 1.8 - col * 0.4)
            if k <= 0:
                continue
            fill = GREEN if name == "victory" else (RED if name == "death" else MAROON)
            c.circle_at(px, py, 36 * k, fill=fill)
            ic = "1F3C6" if name == "victory" else ("1F480" if name == "death" else None)
            if ic:
                c.emo(ic, px, py, 20 * k, anchor="cc")
            else:
                c.text(px, py, name[:5], size=9, color=(255, 255, 255), weight="bold", anchor="mm")
        c.text(APP_W / 2, y + 278, "AI wired every branch into a playable path", size=13.5,
               color=BROWN, name="garamond_i", anchor="ma")
    return y + 320


def content_lib(c: Ctx, st, t):
    y = 16
    c.text(APP_W / 2 + 16, y, "Adventures Library", size=25, color=MAROON, name="display",
           weight="bold", anchor="ma")
    c.emo("1F4DA", APP_W / 2 - 130, y + 16, 26, anchor="cc")
    y += 36
    y = c.para(APP_W / 2 - 180, y, "Play adventures from the community and your own published "
               "stories.", 360, 20, size=14.5, color=BROWN, name="garamond_i")
    y += 14
    c.rect(20, y, 390, 88, 10, fill=CARD, outline=TAN, ow=1.6)
    c.emo("1F4E5", 42, y + 20, 15, anchor="cc")
    c.text(52, y + 12, "PLAY A FRIEND'S ADVENTURE", size=11, color=MAROON, weight="bold")
    c.rect(34, y + 32, 236, 42, 8, fill=(255, 255, 255, 255), outline=TAN, ow=1.3)
    c.text(44, y + 53, st.get("import_text", "cyop_YW5kIHlvdXIgc3Rvcnk"), size=13.5,
           color=BROWN, name="garamond", anchor="lm")
    c.btn(282, y + 32, 118, 42, "Import", fill=GOLD, size=13, icon="1F4E5", icon_size=15)
    HIT["c_import_btn"] = (341, y + 53)
    y += 100
    c.rect(20, y, 390, 44, 9, fill=(230, 244, 232, 255), outline=GREEN, ow=1.6)
    c.emo("2705", 44, y + 22, 20, anchor="cc")
    c.text(62, y + 22, "Published · rated ST-2 · school-friendly", size=14, color=GREEN,
           weight="bold", anchor="lm")
    y += 58
    for series, stories in [
        ("THE LANTERN CHRONICLES",
         [("The Lantern on Blackrock Point", "lighthouse.jpg", "47 plays · 🏆 12% win", "ST-2"),
          ("The Keeper's Map", "harbor.jpg", "18 plays · 🏆 9% win", "ST-2")]),
        ("DARKWOOD TALES",
         [("The Sleeping Hoard", "dragon.jpg", "31 plays · 🏆 6% win", "ST-3")]),
    ]:
        c.text(20, y, series, size=12, color=GOLD, weight="bold", spacing=1.8)
        c.line([(24 + c.font(12, weight="bold").getlength(series) / c.s + 14, y + 8),
                (APP_W - 20, y + 8)], TAN, 1.2)
        y += 22
        for title, photo, meta, rate in stories:
            c.rect(20, y, 390, 124, 11, fill=CARD, outline=TAN, ow=1.6)
            c.photo(photo, 30, y + 12, 120, 100, radius=9)
            c.text(164, y + 16, title, size=17, color=MAROON, name="display", weight="bold")
            c.text(164, y + 42, meta, size=13.5, color=BROWN, name="garamond")
            c.badge(164, y + 64, rate, fill=(255, 255, 255, 0), color=GREEN, size=12.5, padx=0)
            c.badge(164, y + 90, "Read & Play", fill=MAROON, color=(255, 255, 255), size=12.5,
                    h=26, radius=13, tri=True)
            HIT[f"c_card_{title[:6]}"] = (240, y + 100)
            y += 136
        y += 12
    return y + 24


CONTENT = {"home": content_home, "build": content_build, "convert": content_convert,
           "lib": content_lib}


# --------------------------------------------------------------------------
# player overlay (mirrors the real .player markup)
# --------------------------------------------------------------------------
PLAY_CHOICES = [("A", "Take the lantern and step inside"), ("B", "Search the rocks below"),
                ("C", "Row back to the harbor")]
# css y of each choice button's centre on screen (no scroll)
PLAY_CHOICE_SCREEN_Y = [0, 0, 0]


def draw_player(c: Ctx, st, t):
    scene = st.get("scene", 0)
    c.rect(0, 0, APP_W, APP_H, 0, fill=(20, 10, 5, 170))
    pw = APP_W - 36
    px = 18
    ph = {0: 336, 1: 432, 2: 372}[scene]
    py = (VIEW_H - ph) / 2
    sh, pad = shadow(pw, ph, 14, blur=26, opacity=0.5)
    paste(c.img, sh, c.P(px - pad / c.s, py - pad / c.s))
    c.rect(px, py, pw, ph, 13, fill=PARCH, outline=GOLD, ow=3.2)
    c.text(px + pw - 16, py + 12, "✕", size=16, color=BROWN, anchor="ra")
    ix, iw = px + 24, pw - 48
    cy = py + 28
    if scene == 0:
        c.text(ix + iw / 2, cy, "START", size=11, color=GOLD, weight="bold", spacing=2.4,
               anchor="ma")
        cy += 26
        body = ("You wake on a strange shore. Far off, a lantern burns in the window of the "
                "lighthouse.")
        shown = body[: int(round(len(body) * clamp(st.get("text_p", 1.0))))]
        cy = c.para(ix, cy, shown, iw, 27, size=16, color=INK, name="garamond") + 18
        rev = st.get("choices_reveal", 0.0)
        for i, (letter, label) in enumerate(PLAY_CHOICES):
            k = seg(rev, i * 0.14, i * 0.14 + 0.4)
            if k <= 0:
                continue
            e = ease_out_cubic(k)
            h = 52 * e
            sel = st.get("tap_sel") == i
            c.rect(ix, cy, iw, h, 9, fill=CREAM if sel else (255, 255, 255, 255),
                   outline=GOLD if sel else TAN, ow=2.2)
            c.rect(ix + 1.5, cy + 1.5, 6, max(0, h - 3), 3, fill=GOLD if sel else MAROON)
            HIT[f"p_choice_{letter}"] = (215, cy + 26)
            if e > 0.4:
                c.circle_at(ix + 30, cy + h / 2, 30, fill=GOLD if sel else MAROON)
                c.text(ix + 30, cy + h / 2, letter, size=14,
                       color=INK if sel else (255, 255, 255), weight="bold", anchor="mm")
                c.text(ix + 54, cy + h / 2, label, size=15.5, color=INK, name="garamond",
                       anchor="lm")
                PLAY_CHOICE_SCREEN_Y[i] = cy + h / 2
            cy += h + 10
    elif scene == 1:
        c.photo(st.get("photo", "harbor.jpg"), ix, cy, iw, 192, radius=10)
        c.text(ix + iw / 2, cy + 200, "The harbor at dawn — the keeper's boat is still moored.",
               size=12, color=BROWN, name="garamond_i", anchor="ma")
        cy += 224
        body = "You take the lantern. The keeper's boat is still moored at the harbor."
        shown = body[: int(round(len(body) * clamp(st.get("text_p", 1.0))))]
        cy = c.para(ix, cy, shown, iw, 27, size=16, color=INK, name="garamond") + 16
        k = clamp(st.get("cont_reveal", 0.0))
        HIT["p_continue"] = (215, cy + 26)
        if k > 0:
            e = ease_out_cubic(k)
            c.rect(ix, cy, iw, 52 * e, 9, fill=CREAM, outline=GOLD, ow=2.2)
            if e > 0.4:
                cyc = cy + 26 * e
                c.circle_at(ix + 30, cyc, 30, fill=GOLD)
                c.arrow(ix + 22, cyc, 16, INK, 2.2)
                c.text(ix + 54, cyc, "Continue", size=15.5, color=MAROON, name="garamond_i",
                       anchor="lm")
                lw = c.font(15.5, "garamond_i").getlength("Continue") / c.s
                c.arrow(ix + 62 + lw, cyc, 18, MAROON, 1.9)
    else:
        win = st.get("victory", True)
        e = ease_out_cubic(clamp(st.get("end_p", 0.0)))
        c.circle_at(APP_W / 2, py + 92, 152 * (0.5 + 0.5 * e),
                    fill=(230, 244, 232, 255) if win else (250, 230, 230, 255))
        HIT["p_result"] = (215, py + 92)
        c.emo("1F3C6" if win else "1F480", APP_W / 2, py + 92, 94 * (0.6 + 0.4 * e), anchor="cc")
        c.text(APP_W / 2, py + 168, "Victory!" if win else "You have died…", size=30,
               color=GREEN if win else RED, name="display", weight="bold", anchor="ma")
        c.para(ix, py + 214, "You light the lamp and the ship clears the rocks. Blackrock keeps "
               "its keeper." if win else "The tide takes you. The lantern gutters out.",
               iw, 27, size=16, color=INK, name="garamond")
        c.btn(px + 28, py + 290, 170, 50, "Play Again", fill=GREEN if win else RED,
              color=(255, 255, 255), size=15, radius=10)
        c.btn(px + pw - 198, py + 290, 170, 50, "Back to Builder", fill=TAN, color=INK, size=15,
              radius=10)
    return (px, py, pw, ph)


# --------------------------------------------------------------------------
# publish modal + share sheet
# --------------------------------------------------------------------------
def draw_publish(c: Ctx, st, t):
    c.rect(0, 0, APP_W, APP_H, 0, fill=(20, 10, 5, 175))
    pw, ph, px, py = APP_W - 44, 430, 22, 236
    sh, pad = shadow(pw, ph, 14, blur=24, opacity=0.5)
    paste(c.img, sh, c.P(px - pad / c.s, py - pad / c.s))
    c.rect(px, py, pw, ph, 13, fill=CARD, outline=GOLD, ow=2.8)
    c.text(px + pw / 2, py + 18, "⚡ Publish Adventure", size=21, color=MAROON, name="display",
           weight="bold", anchor="ma")
    c.line([(px + 20, py + 52), (px + pw - 20, py + 52)], GOLD, 1.6)
    yy = py + 68
    c.text(px + 20, yy, "TITLE", size=11, color=MAROON, weight="bold", spacing=1)
    c.rect(px + 20, yy + 16, pw - 40, 40, 8, fill=(255, 255, 255, 255), outline=TAN, ow=1.3)
    c.text(px + 30, yy + 36, "The Lantern on Blackrock Point", size=15, color=INK,
           name="display", anchor="lm")
    yy += 70
    c.text(px + 20, yy, "SERIES", size=11, color=MAROON, weight="bold", spacing=1)
    c.rect(px + 20, yy + 16, pw - 40, 40, 8, fill=(255, 255, 255, 255), outline=TAN, ow=1.3)
    c.text(px + 30, yy + 36, "The Lantern Chronicles", size=15, color=INK, name="garamond",
           anchor="lm")
    yy += 70
    c.rect(px + 20, yy, pw - 40, 90, 9, fill=(255, 255, 255, 215), outline=TAN, ow=1.3)
    c.emo("1F9E0", px + 48, yy + 45, 30, anchor="cc")
    c.text(px + 72, yy + 14, "AI AGE RATING", size=11, color=VIOLET, weight="bold")
    rated = clamp(st.get("rate_p", 0.0))
    if rated > 0:
        c.badge(px + 72, yy + 32, "ST-2", fill=GOLD, color=INK, size=15, h=28, radius=14)
        if rated > 0.5:
            c.badge(px + 128, yy + 32, "School-friendly", fill=GREEN, color=(255, 255, 255),
                    size=12.5, h=28, radius=14, icon="1F3EB")
        c.text(px + 72, yy + 66, "Mild peril · no intense content", size=12, color=BROWN,
               name="garamond_i")
    else:
        c.text(px + 72, yy + 42, "Rating this story…", size=14, color=BROWN, name="garamond_i")
    yy += 104
    pub = clamp(st.get("publish_p", 0.0))
    if pub <= 0:
        c.btn(px + pw - 168, yy, 148, 48, "Publish", fill=GOLD, size=16, icon="26A1", icon_size=18)
        HIT["m_publish_btn"] = (px + pw - 94, yy + 24)
        c.btn(px + pw - 296, yy, 120, 48, "Cancel", fill=TAN, color=INK, size=15)
    else:
        c.rect(px + 20, yy, pw - 40, 48, 9, fill=(230, 244, 232, 255), outline=GREEN, ow=1.6)
        c.emo("2705", px + 46, yy + 24, 20, anchor="cc")
        c.text(px + 64, yy + 24, "Published to your library", size=15, color=GREEN,
               weight="bold", anchor="lm")


def draw_share(c: Ctx, st, t):
    up = ease_out_cubic(clamp(st.get("share_p", 0.0)))
    sheet_h = 420
    sy = APP_H - sheet_h * up
    c.rect(0, 0, APP_W, APP_H, 0, fill=(20, 10, 5, int(120 * up)))
    c.rect(0, sy, APP_W, sheet_h, 0, fill=CARD)
    c.line([(0, sy), (APP_W, sy)], GOLD, 2.8)
    c.rect(APP_W / 2 - 28, sy + 10, 56, 5, 3, fill=TAN)
    c.text(APP_W / 2 + 14, sy + 28, "Share your story", size=21, color=MAROON, name="display",
           weight="bold", anchor="ma")
    c.emo("1F517", APP_W / 2 - 96, sy + 42, 22, anchor="cc")
    c.text(APP_W / 2, sy + 58, "Friends paste this code and play — no account needed.", size=13.5,
           color=BROWN, name="garamond_i", anchor="ma")
    c.rect(20, sy + 84, APP_W - 40, 58, 10, fill=(255, 255, 255, 255), outline=GOLD, ow=1.8)
    code = "cyop_7fQ2mZk9LpXw"
    settle = clamp(st.get("code_p", 0.0))
    rng = "abcdefghijkmnpqrstuvwxyzACDEFGHJKLMNPQRSTUVWXY23456789"
    chars = []
    for i, ch in enumerate(code):
        keep = clamp(settle * len(code) * 1.15 - i)
        chars.append(ch if keep >= 1 else rng[(i * 7 + int(t * 22)) % len(rng)])
    c.text(APP_W / 2, sy + 113, "".join(chars), size=17, color=INK, name="garamond", anchor="mm",
           spacing=0.8)
    c.btn(20, sy + 156, 190, 48, "Copy code", fill=GOLD, size=14.5, icon="1F4CB", icon_size=17)
    HIT["m_copy_btn"] = (115, sy + 180)
    c.btn(220, sy + 156, 190, 48, "Share this page", fill=MAROON, color=(255, 255, 255),
          size=14.5, icon="1F517", icon_size=17)
    c.btn(20, sy + 212, 390, 48, "Import & Play a friend's adventure", fill=TAN, color=INK,
          size=14.5, icon="1F4E5", icon_size=17)
    c.text(APP_W / 2, sy + 276, "Or open a link — ?story=… loads the adventure straight away",
           size=13, color=BROWN, name="garamond_i", anchor="ma")
    c.rect(20, sy + 302, 390, 92, 10, fill=(255, 255, 255, 190), outline=TAN, ow=1.3)
    c.text(34, sy + 314, "PRIVATE BY DESIGN", size=11, color=MAROON, weight="bold")
    c.para(34, sy + 332, "Stories live in your browser (localStorage). No account, no server, "
           "nothing uploaded — until you share a code.", 360, 19, size=13, color=BROWN,
           name="garamond")
    tp = clamp(st.get("toast_p", 0.0))
    if tp > 0:
        # float above the sheet: at sheet+404 the toast used to run past the
        # bottom of the viewport and get cut off
        e = ease_out_cubic(tp)
        ty = sy - 60 - (1 - e) * 22
        c.rect(APP_W / 2 - 105, ty, 210, 44, 10, fill=INK)
        c.emo("2705", APP_W / 2 - 81, ty + 22, 19, anchor="cc")
        c.text(APP_W / 2 - 64, ty + 22, "Code copied", size=14, color=PARCH, weight="bold",
               anchor="lm")


# --------------------------------------------------------------------------
# full screen / phone
# --------------------------------------------------------------------------
def draw_app_screen(c: Ctx, st, t):
    c.img.paste(Image.new("RGBA", c.img.size, PARCH + (255,)), (0, 0))
    tab = st.get("tab", "home")
    draw_header(c, t, st.get("install_pulse", 0.0))
    draw_nav(c, tab, t)
    scale = c.s
    cw = int(round(APP_W * scale))
    cc = Ctx(APP_W, 1400, scale)
    used = CONTENT[tab](cc, st.get(tab, {}), t)
    content = cc.img.crop((0, 0, cw, int(round(min(1390, used + 24) * scale))))
    scroll = clamp(st.get("scroll", {}).get(tab, 0.0), 0, max(0.0, used + 24 - WIN_H))
    top = int(round(scroll * scale))
    win = content.crop((0, top, cw, min(content.height, top + int(round(WIN_H * scale)))))
    c.img.paste(win, (0, int(round(CONTENT_TOP * scale))), win)
    draw_status_bar(c, t)
    draw_safari_bar(c, st.get("url", _URL))
    ov = st.get("overlay")
    if ov in ("player", "publish", "share"):
        layer = Ctx(APP_W, APP_H, scale, bg=PARCH + (255,))
        layer.img.paste(c.img.crop((0, 0, layer.w, layer.h)), (0, 0))
        if ov == "player":
            draw_player(layer, st.get("player", {}), t)
        elif ov == "publish":
            draw_publish(layer, st.get("publish", {}), t)
            if st.get("share_p", 0) > 0:
                draw_share(layer, st, t)
        else:
            draw_share(layer, st, t)
        c.img = layer.img
        c.d = ImageDraw.Draw(c.img)


def draw_status_bar(c: Ctx, t):
    c.text(26, CHROME_TOP / 2, "9:41", size=13, color=PARCH, weight="bold", anchor="lm")
    x = APP_W - 24
    c.rect(x - 24, CHROME_TOP / 2 - 6, 24, 12, 3, fill=None, outline=PARCH, ow=1.3)
    c.rect(x - 22, CHROME_TOP / 2 - 4, 17, 8, 2, fill=PARCH)
    c.rect(x - 27, CHROME_TOP / 2 - 3, 3, 6, 1.5, fill=PARCH)
    x -= 34
    for i in range(3):
        c.rect(x - 16 + i * 5.5, CHROME_TOP / 2 + 3 - (5 + i * 4), 3.6, 5 + i * 4, 1, fill=PARCH)
    x -= 28
    c.circle_at(x - 8, CHROME_TOP / 2, 15, fill=None, outline=PARCH, ow=1.4)
    c.text(x - 8, CHROME_TOP / 2, "5G", size=8, color=PARCH, weight="bold", anchor="mm")


def draw_safari_bar(c: Ctx, url=_URL):
    y = APP_H - CHROME_BOT
    c.rect(0, y, APP_W, CHROME_BOT, 0, fill=(246, 240, 228, 244))
    c.line([(0, y), (APP_W, y)], (200, 186, 165), 1)
    c.rect(56, y + 8, APP_W - 112, 28, 14, fill=(255, 255, 255, 255), outline=(214, 206, 190), ow=1)
    c.emo("1F512", 70, y + 22, 12, anchor="cc")
    c.text(APP_W / 2 + 4, y + 22, url, size=11.5, color=(70, 62, 55), name="garamond", anchor="mm")
    for i in range(3):
        c.circle_at(APP_W - 30 + i * 6, y + 22, 3.4, fill=(120, 110, 100))


def render_screen(st, t, screen_w=760):
    scale = screen_w / APP_W
    c = Ctx(APP_W, APP_H, scale)
    draw_app_screen(c, st, t)
    return c, scale


def render_phone_full(st, t, screen_w=760):
    """Screen + bezel + glass highlight. Returns (image, scale, bezel).

    The device shell is baked once at a canonical size and resampled per frame,
    so an animated zoom never pays to rebuild a phone-sized rounded rectangle.
    """
    scale = screen_w / APP_W
    c, scale = render_screen(st, t, screen_w)
    screen = c.img
    bezel = 13 * scale
    sw, sh = screen.width, screen.height
    w, h = int(round(sw + bezel * 2)), int(round(sh + bezel * 2))
    phone = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    paste(phone, _shell(w, h), (0, 0))          # bezel frame
    screen_r = screen.copy()
    screen_r.putalpha(rr(sw, sh, max(4.0, 54 * scale - bezel * 0.55),
                         fill=(255, 255, 255, 255)).getchannel("A"))
    paste(phone, screen_r, (int(round(bezel)), int(round(bezel))))  # screen inside it
    paste(phone, _island(w, h), (0, 0))         # dynamic island over the screen
    paste(phone, _sheen(w, h), (0, 0))
    return phone, scale, bezel


def _island(w, h):
    key = ("island", w, h)
    from kit import _CACHE

    if key in _CACHE:
        return _CACHE[key]
    base_w = _SHELL_W
    scale = base_w / APP_W
    k = w / _SHELL_W
    iw, ih = int(96 * scale * k), int(26 * scale * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    blk = rr(iw, ih, int(13 * scale * k), fill=(10, 8, 6, 255))
    paste_c(img, blk, w / 2, (13 + 14) * scale * k)
    _CACHE[key] = img
    return img


_SHELL_W = 880


def _shell(w, h):
    """Scaled device shell + screen mask from a canonical bake."""
    key = ("shell", w, h)
    from kit import _CACHE

    if key in _CACHE:
        return _CACHE[key]
    base_w = _SHELL_W
    base_h = int(round(base_w * APP_H / APP_W))
    bez = int(round((base_w / APP_W) * 13))
    outer_w, outer_h = base_w + bez * 2, base_h + bez * 2
    radius = int(round(54 * base_w / APP_W))
    # a hollow ring: outer rounded rect minus the screen aperture, so the app
    # screen pasted afterwards shows through
    body = rr(outer_w, outer_h, radius, fill=(26, 19, 15, 255),
              outline=(64, 50, 40, 255), ow=max(3, int(2.5 * base_w / APP_W)))
    aperture = Image.new("L", (outer_w, outer_h), 255)
    ImageDraw.Draw(aperture).rounded_rectangle(
        [bez, bez, outer_w - bez - 1, outer_h - bez - 1],
        radius=max(4, radius - bez), fill=0)
    body.putalpha(ImageChops.multiply(body.getchannel("A"), aperture))
    shell = body.resize((w, h), Image.LANCZOS)
    _CACHE[key] = shell
    return shell


def _sheen(w, h):
    key = ("sheen", w, h)
    from kit import _CACHE

    if key in _CACHE:
        return _CACHE[key]
    import numpy as np

    base_w = _SHELL_W
    base_h = int(round(base_w * APP_H / APP_W))
    y, x = np.mgrid[0:base_h, 0:base_w].astype(np.float32)
    band = np.exp(-(((x - y * 1.15 + base_w * 0.55) / (base_w * 0.16)) ** 2)) * 24
    a = np.clip(band, 0, 255).astype(np.uint8)
    rgb = np.dstack([a, a, a]).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, a]), "RGBA")
    radius = int(round(54 * base_w / APP_W))
    mask = rr(base_w + int(round(13 * base_w / APP_W)) * 2,
              base_h + int(round(13 * base_w / APP_W)) * 2, radius,
              fill=(255, 255, 255, 220)).getchannel("A")
    full = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    full.paste(im, (int(round(13 * base_w / APP_W)), int(round(13 * base_w / APP_W))))
    full.putalpha(ImageChops.multiply(full.getchannel("A"), mask))
    out = full.resize((w, h), Image.LANCZOS)
    _CACHE[key] = out
    return out
