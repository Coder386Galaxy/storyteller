"""Storyteller CYOP — promo film.

    python render.py --aspect all        # 9:16, 1:1 and 16:9 mp4s
    python render.py --stills            # contact sheet for review

One timeline drives three layouts: the phone mockup sits in the frame and the
copy lives in the remaining text zone, so the same film reads correctly
full-screen on a phone, in a square feed post, and on a 16:9 player.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from appmock import APP_H, APP_W, CONTENT_TOP, HIT, Ctx, draw_app_screen  # noqa: E402
from appmock import render_phone_full  # noqa: E402
from kit import (  # noqa: E402
    BLACK, BLUE, BROWN, CARD, CREAM, GOLD, GOLD_LT, GREEN, INK, INK_SOFT, MAROON, MAROON_LT,
    PARCH, RED, TAN, VIOLET, circle, clamp, ease_in_out, ease_out_back, ease_out_cubic,
    ease_out_elastic, ease_out_quint, emoji as emoji_img, font, gradient, grain, mix, paper,
    paste, paste_c, pulse, radial_glow, ramp, rr, seg, shadow, text_spaced, wrap,
)

FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "film")
URL = "coder386galaxy.github.io/storyteller"

SCENES = [
    ("hook", 0.0, 3.2),
    ("hero", 3.2, 6.8),
    ("build", 6.8, 11.4),
    ("convert", 11.4, 15.4),
    ("play", 15.4, 21.8),      # the payoff gets the most room
    ("library", 21.8, 25.8),
    ("cta", 25.8, 30.4),
]
TOTAL = SCENES[-1][2]
XFADE = 0.6

COPY = {
    "hero": ("BUILD", "Build, play & publish", "in your browser"),
    "build": ("BRANCH", "Choice by choice", "A/B/C/D — every path leads somewhere"),
    "convert": ("AI CONVERT", "Paste a messy draft", "AI wires the branches for you"),
    "play": ("PLAY", "Read it like a reader", "deaths, victories, honest win rates"),
    "library": ("PUBLISH & SHARE", "Rate it. Share it.", "one code — friends play instantly"),
}

def warm_hits():
    """Render one cheap probe frame so HIT holds every target's coordinates
    before the camera maths runs."""
    probe = base_state(tab="build",
                       build=dict(chips_reveal=1.0, choices_reveal=1.0, type_p=1.0))
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)
    probe = base_state(tab="home", home=dict())
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)
    probe = base_state(tab="lib", overlay="publish", publish=dict(rate_p=1.0, publish_p=0.0))
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)
    probe = base_state(tab="lib", overlay="share", share_p=1.0, code_p=1.0)
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)
    probe = base_state(tab="lib", overlay="player",
                       player=dict(scene=0, choices_reveal=1.0, text_p=1.0))
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)
    probe = base_state(tab="lib", overlay="player",
                       player=dict(scene=1, cont_reveal=1.0, text_p=1.0))
    draw_app_screen(Ctx(APP_W, APP_H, 0.06), probe, 0.0)


def hit_screen(info, name, scroll=0.0):
    """Frame pixels for a target registered by the mockup (screen css space)."""
    if name not in HIT:
        return None
    x, y = HIT[name]
    s = info["scale"]
    return (info["px"] + info["bezel"] + x * s, info["py"] + info["bezel"] + y * s)


def hit_content(info, name, scroll=0.0):
    """Frame pixels for a target registered in content (scrolling) space."""
    if name not in HIT:
        return None
    x, y = HIT[name]
    return hit_screen(info, name, 0) if False else (
        info["px"] + info["bezel"] + x * info["scale"],
        info["py"] + info["bezel"] + (y + CONTENT_TOP - scroll) * info["scale"])


# ---------------------------------------------------------------------------
# layout presets
# ---------------------------------------------------------------------------
def make_layout(aspect: str):
    if aspect == "vertical":
        lay = dict(aspect=aspect, W=1080, H=1920, wide=False, phone_w=650.0,
                   anchor=(540.0, 1888.0), anchor_mode="bottom",
                   text_zone=(64.0, 78.0, 1080 - 128.0, 250.0))
    elif aspect == "square":
        lay = dict(aspect=aspect, W=1080, H=1080, wide=True, phone_w=418.0,
                   anchor=(1042.0, 1064.0), anchor_mode="bottom_right",
                   text_zone=(70.0, 118.0, 490.0, 780.0))
    elif aspect == "landscape":
        lay = dict(aspect=aspect, W=1920, H=1080, wide=True, phone_w=406.0,
                   anchor=(1876.0, 1058.0), anchor_mode="bottom_right",
                   text_zone=(132.0, 168.0, 1130.0, 700.0))
    else:
        raise SystemExit(f"unknown aspect {aspect}")
    return lay


# ---------------------------------------------------------------------------
# background + finish
# ---------------------------------------------------------------------------
def bg(lay, t):
    W, H = lay["W"], lay["H"]
    im = gradient((W, H), (248, 241, 225), (231, 217, 190), "d").convert("RGBA")
    im.alpha_composite(paper((W, H), PARCH, 20, 7))
    ax, ay = lay["anchor"]
    paste_c(im, radial_glow(int(W * 1.6), (255, 216, 145), 2.0, 118), ax, ay - H * 0.5)
    return im


def finish(im, lay, t, vig=0.40):
    W, H = lay["W"], lay["H"]
    im.alpha_composite(_vignette(lay, vig))
    tiles = grain((W, H), 6, 6, 11)
    im.alpha_composite(tiles[int(t * 24) % len(tiles)])
    return im.convert("RGB")


def _vignette(lay, strength):
    from kit import _CACHE, vignette

    return vignette((lay["W"], lay["H"]), strength)


# ---------------------------------------------------------------------------
# camera + phone placement
# ---------------------------------------------------------------------------
# how much extra push-in each aspect can afford (the phone is huge in 9:16)
ZOOM = {"vertical": 0.24, "square": 0.45, "landscape": 0.60}


def cam(focus=(215.0, 466.0), zoom=1.0, offset=(0.0, 0.0), center_on_focus=False):
    return dict(focus=focus, zoom=zoom, offset=offset, center_on_focus=center_on_focus)


def zoom_for(delta, lay):
    """Scale a zoom delta for the aspect."""
    return 1.0 + max(0.0, delta - 1.0) * ZOOM[lay["aspect"]]


def place_phone(frame, lay, st, t, camera):
    screen_w = lay["phone_w"] * camera["zoom"]
    phone, scale, bezel = render_phone_full(st, t, screen_w)
    fx, fy = camera["focus"]
    ax, ay = lay["anchor"]
    ox, oy = camera["offset"]
    if camera.get("center_on_focus"):
        if lay["wide"]:
            # keep the device on its own side; only re-centre vertically
            px = (ax - phone.width if lay["anchor_mode"] == "bottom_right"
                  else ax - phone.width / 2) + ox
            py = lay["H"] * 0.5 - (bezel + fy * scale) + oy
        else:
            # 9:16 push-ins grow from the bottom anchor (a real dolly-in): the
            # device never detaches from the bottom edge, so no dead space opens
            # up under it, and the target content rises into the middle third.
            px = ax - phone.width / 2 + ox
            py = max(lay["H"] * 0.5 - (bezel + fy * scale) + oy,
                     lay["H"] - 32 - phone.height)
    elif lay["anchor_mode"] == "bottom":
        px = ax - phone.width / 2 + ox
        py = ay - phone.height + oy
    else:  # bottom_right
        px = ax - phone.width + ox
        py = ay - phone.height + oy
    # layout guard: keep the device clear of a visible caption block
    cap = SPANS.get("caption")
    if cap:
        overlap_x = min(cap[2], px + phone.width) - max(cap[0], px)
        if py < cap[3] + 10 and overlap_x > 0.25 * phone.width:
            py = cap[3] + 10
    SPANS["phone"] = (px, py, px + phone.width, py + phone.height)
    sh, pad = shadow(phone.width - int(bezel * 2), phone.height - int(bezel * 2),
                     int(bezel * 0.8), blur=max(18, int(32 * scale)), opacity=0.34)
    paste(frame, sh, (px + bezel - pad, py + bezel - pad))
    paste(frame, phone, (px, py))
    return dict(px=px, py=py, bezel=bezel, scale=scale, phone=phone, zoom=camera["zoom"],
                map=lambda cx, cy: (px + bezel + cx * scale, py + bezel + cy * scale))


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------
SPANS: dict = {}   # last-frame bounding boxes, for --check


def fit_font(text, name, weight, max_w, start, min_size=10):
    s = start
    while s > min_size and font(name, s, weight).getlength(text) > max_w:
        s -= 1
    return font(name, s, weight)


def reveal_line(frame, lay, x, y, text, name, weight, size, color, p, spacing=0.0,
                align="center", width=None):
    """Display text that rises into place behind a soft wipe."""
    p = clamp(p)
    if p <= 0.001:
        return
    f = font(name, size, weight)
    tw = f.getlength(text) + spacing * max(0, len(text) - 1)
    box_w = int((width or tw) + 60)
    box_h = int(size * 2.6)
    tmp = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    tx = 30 if align == "left" else (box_w - tw) / 2
    ty = box_h * 0.36
    if spacing:
        text_spaced(d, (tx, ty), text, f, color + (255,), spacing)
    else:
        d.text((tx, ty), text, font=f, fill=color + (255,))
    e = ease_out_quint(p)
    keep = max(1, min(box_h, int(box_h * (0.40 + 0.62 * e)) + 8))
    dy = int((1 - e) * size * 0.34)
    cut = tmp.crop((0, box_h - keep, box_w, box_h))
    paste(frame, cut, (x - box_w / 2, y - box_h * 0.36 + dy + (box_h - keep)))


def caption(frame, lay, kicker, title, sub="", appear=1.0, alpha=1.0):
    """Top-of-frame caption. Returns the y where it ends."""
    a = clamp(appear) * clamp(alpha)
    if a <= 0.01:
        return 0
    e = ease_out_cubic(clamp(appear))
    al = int(255 * a)
    x0, y0, tw, th = lay["text_zone"]
    wide = lay["wide"]
    dy = int((1 - e) * 30)
    cx = x0 if wide else x0 + tw / 2
    align = "left" if wide else "center"
    y = y0 + dy
    d = ImageDraw.Draw(frame)
    if kicker:
        kf = font("body", 26 if wide else 24, "bold")
        kw = kf.getlength(kicker) + 3.4 * (len(kicker) - 1)
        kx = cx if align == "center" else x0
        kx = kx - (kw / 2 if align == "center" else 0)
        rule = 34
        if align == "center":
            rx = kx - rule - 14
            d.line([(rx, y + 16), (rx + rule, y + 16)], fill=GOLD + (al,), width=3)
            d.line([(kx + kw + 14, y + 16), (kx + kw + 14 + rule, y + 16)], fill=GOLD + (al,),
                   width=3)
        text_spaced(d, (kx, y + 4), kicker, kf, GOLD + (al,), 3.4)
        y += 52
    tf = font("display", 62 if wide else 56, "bold")
    sf = font("garamond_i", 38 if wide else 34)
    for ln in wrap(title, tf, int(tw)):
        d.text((cx, y), ln, font=tf, fill=INK + (al,), anchor="la" if wide else "ma")
        y += tf.size * 1.14
    if sub:
        y += 4
        for ln in wrap(sub, sf, int(tw)):
            d.text((cx, y), ln, font=sf, fill=BROWN + (al,), anchor="la" if wide else "ma")
            y += sf.size * 1.28
    SPANS["caption"] = (x0, y0, x0 + tw, y)
    return y


def ripple(frame, cx, cy, p, color=GOLD_LT, radius=70):
    if cx is None or cy is None or p <= 0 or p >= 1:
        return
    e = ease_out_cubic(p)
    r = int(radius * (0.35 + e * 1.25))
    ring = circle(r * 2, fill=None, outline=color + (int(200 * (1 - e)),), ow=max(1, int(7 * (1 - e)) + 1))
    paste_c(frame, ring, cx, cy)
    dot = circle(int(18 * (1 - e * 0.5)), fill=(255, 255, 255, int(150 * (1 - e))))
    paste_c(frame, dot, cx, cy)


def confetti(frame, lay, t, p, origin, spread=520, n=40, seed=5):
    if p <= 0:
        return
    rs = np.random.RandomState(seed)
    xs, ys = rs.rand(n), rs.rand(n)
    sz = rs.randint(7, 22, n)
    cols = [GOLD, GOLD_LT, MAROON_LT, GREEN, (255, 255, 255), MAROON]
    d = ImageDraw.Draw(frame)
    for i in range(n):
        life = clamp(p * 1.5 - ys[i] * 0.55)
        if life <= 0:
            continue
        e = ease_out_cubic(life)
        x = origin[0] + (xs[i] - 0.5) * spread * (0.3 + e)
        y = origin[1] - 60 + (ys[i] - 0.15) * 260 * e + e * e * 240
        a = int(235 * (1 - life * 0.85))
        d.ellipse([x - sz[i] / 2, y - sz[i] / 2 * 0.72, x + sz[i] / 2, y + sz[i] / 2 * 0.72],
                  fill=cols[i % len(cols)] + (a,))


def base_state(**kw):
    st = dict(tab="home", scroll={"home": 0.0, "build": 0.0, "convert": 0.0, "lib": 0.0},
              overlay=None, install_pulse=0.0, url=URL)
    st.update(kw)
    return st


# ---------------------------------------------------------------------------
# scenes
# ---------------------------------------------------------------------------
def scene_hook(im, lay, tl, t):
    W, H = lay["W"], lay["H"]
    wide = lay["wide"]
    cx = lay["text_zone"][0] if wide else W / 2
    base_y = (lay["text_zone"][1] + 120) if wide else 470
    words = [("WRITE", INK), ("YOUR OWN", INK), ("ADVENTURE", MAROON)]
    max_w = W - 170 if not wide else lay["text_zone"][2]
    sizes = [fit_font(w, "display", "black", max_w, int(H * 0.115)).size for w, _ in words]
    y = base_y
    d = ImageDraw.Draw(im)
    for i, ((word, col), sz) in enumerate(zip(words, sizes)):
        p = seg(tl, 0.14 + i * 0.18, 0.58 + i * 0.18)
        reveal_line(im, lay, cx, y, word, "display", "black", sz, col, p, spacing=sz * 0.015,
                    align="left" if wide else "center", width=max_w)
        y += sz * 1.12
    up = ease_out_cubic(seg(tl, 0.92, 1.5))
    if up > 0:
        uw = max_w * 0.72
        ux = cx - (0 if wide else uw / 2)
        d.line([(ux, y + 18), (ux + uw * up, y + 18)], fill=GOLD + (235,), width=6)
    sp = seg(tl, 1.15, 1.8)
    if sp > 0:
        f = font("garamond_i", 42 if wide else 40)
        a = int(255 * ease_out_cubic(sp))
        sy = y + 52
        for ln in wrap("choose-your-own-path stories you write in the browser", f, int(max_w)):
            d.text((cx, sy), ln, font=f, fill=BROWN + (a,), anchor="la" if wide else "ma")
            sy += f.size * 1.24
    icons = ["2728", "1F500", "1F480", "1F3C6"]
    row_y = base_y - 165 if not wide else y + 190
    gap = 132 if not wide else 124
    ex = cx - (gap * (len(icons) - 1) / 2 if not wide else 0)
    for i, ic in enumerate(icons):
        p = seg(tl, 1.7 + i * 0.13, 2.3 + i * 0.13)
        if p <= 0:
            continue
        e = ease_out_elastic(p)
        sprite = emoji_img(ic, max(6, int(104 * e)))
        sprite = sprite.rotate((1 - e) * 20 * (1 if i % 2 else -1), resample=Image.BICUBIC,
                               expand=True)
        paste_c(im, sprite, ex + i * gap + 52, row_y, int(255 * clamp(p * 3)))
    sw = seg(tl, 2.55, 3.35)
    if 0 < sw < 1:
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bx = -320 + ease_in_out(sw) * (W + 760)
        ImageDraw.Draw(band).polygon([(bx, 0), (bx + 200, 0), (bx - 270, H), (bx - 470, H)],
                                     fill=(255, 236, 190, 58))
        im.alpha_composite(band)


def scene_hero(im, lay, tl, t):
    scroll = 0.0
    st = base_state(tab="home", install_pulse=1.0, scroll={"home": scroll},
                    home=dict(hl_start=1.0))
    zoom = zoom_for(1.0 + 0.08 * ease_out_cubic(seg(tl, 0.8, 3.7)), lay)
    off_y = (1 - ease_out_back(seg(tl, 0.0, 0.95))) * 300
    caption(im, lay, *COPY["hero"], appear=seg(tl, 0.1, 0.7), alpha=1 - seg(tl, 3.1, 3.7))
    info = place_phone(im, lay, st, t, cam(focus=(215, 400), zoom=zoom, offset=(0, off_y)))
    hp = seg(tl, 1.7, 2.45)
    px, py = hit_content(info, "c_start_btn", scroll)
    if hp > 0:
        ring = circle(int(230 * (0.6 + 0.45 * hp)), fill=None, outline=(255, 255, 255, int(70 + 60 * (1 - hp))),
                      ow=max(2, int(8 * (1 - hp) + 2)))
        paste_c(im, ring, px, py)
    if tl > 2.05:
        ripple(im, px, py, clamp((tl - 2.05) / 0.8), radius=90 * zoom)
    p2 = seg(tl, 2.6, 3.2)
    if p2 > 0:
        px2, py2 = hit_content(info, "c_ai_btn", scroll)
        ring = circle(int(300 * p2), fill=None, outline=GOLD_LT + (int(130 * (1 - p2)),), ow=4)
        paste_c(im, ring, px2, py2)


def scene_build(im, lay, tl, t):
    st = base_state(tab="build", scroll={"build": 0.0},
                    build=dict(type_p=ease_out_cubic(seg(tl, 0.35, 2.15)),
                               caret=0.2 < tl < 2.2,
                               ptype=0,
                               chips_reveal=ease_out_cubic(seg(tl, 0.05, 1.0)),
                               chip_active=0,
                               choices_reveal=ease_out_cubic(seg(tl, 2.05, 3.5)),
                               choice_sel=0 if tl > 3.9 else None))
    push = ease_out_cubic(seg(tl, 2.35, 4.05))
    zoom = zoom_for(1.0 + 0.30 * push, lay)
    focus_y = BUILD_FOCUS_Y
    caption(im, lay, *COPY["build"], appear=seg(tl, 0.05, 0.6), alpha=1 - seg(tl, 2.3, 2.9))
    c = cam(focus=(215, focus_y), zoom=zoom, center_on_focus=push > 0.002)
    info = place_phone(im, lay, st, t, c)
    if tl > 4.25:
        px, py = hit_content(info, "c_choice_A")
        ripple(im, px, py, clamp((tl - 4.25) / 0.75), radius=64 * zoom)


def scene_convert(im, lay, tl, t):
    st = base_state(tab="convert", scroll={"convert": 0.0},
                    convert=dict(paste_p=ease_out_cubic(seg(tl, 0.35, 1.95)),
                                 prog=ease_out_cubic(seg(tl, 2.05, 2.85)),
                                 done=ease_out_cubic(seg(tl, 2.85, 3.35)),
                                 graph=ease_out_cubic(seg(tl, 3.05, 4.1))))
    zoom = zoom_for(1.0 + 0.14 * ease_out_cubic(seg(tl, 0.4, 2.2)) + 0.08 * ease_out_cubic(seg(tl, 2.6, 4.0)), lay)
    caption(im, lay, *COPY["convert"], appear=seg(tl, 0.05, 0.6), alpha=1 - seg(tl, 2.6, 3.2))
    c = cam(focus=(215, 560), zoom=zoom, offset=(0, -160 * (zoom - 1.0)))
    info = place_phone(im, lay, st, t, c)
    if tl > 2.95:
        px, py = hit_content(info, "c_ready")
        ripple(im, px, py, clamp((tl - 2.95) / 0.8), color=GREEN, radius=52 * zoom)


def scene_play(im, lay, tl, t):
    A, B, C, D = 2.4, 3.1, 4.2, 4.75
    if tl < B:
        scene_i, end_p, tap_sel = 0, 0.0, (0 if tl > A else None)
        text_p = ease_out_cubic(seg(tl, 0.15, 0.95))
        ch_rev = ease_out_cubic(seg(tl, 0.9, 2.1))
        cont_rev = 0.0
    elif tl < D:
        scene_i, end_p, tap_sel = 1, 0.0, None
        text_p = ease_out_cubic(seg(tl, B + 0.1, B + 0.85))
        ch_rev, cont_rev = 0.0, ease_out_cubic(seg(tl, B + 0.5, B + 1.1))
    else:
        scene_i, end_p, tap_sel = 2, ease_out_back(clamp((tl - D) / 0.85)), None
        text_p, ch_rev, cont_rev = 1.0, 0.0, 0.0
    st = base_state(tab="lib", overlay="player", scroll={"lib": 0.0},
                    player=dict(scene=scene_i, text_p=text_p, choices_reveal=ch_rev,
                                cont_reveal=cont_rev, tap_sel=tap_sel, photo="harbor.jpg",
                                end_p=end_p, victory=True))
    push = ease_out_cubic(seg(tl, 1.2, 2.2))
    zoom = zoom_for(1.0 + 0.30 * push, lay)
    caption(im, lay, *COPY["play"], appear=seg(tl, 0.05, 0.55), alpha=1 - seg(tl, 1.25, 1.9))
    info = place_phone(im, lay, st, t, cam(focus=(215, 520), zoom=zoom, center_on_focus=push > 0.002))
    if tl > A:
        px, py = hit_screen(info, "p_choice_A")
        ripple(im, px, py, clamp((tl - A) / 0.75), radius=64 * zoom)
    if tl > C:
        px, py = hit_screen(info, "p_continue")
        ripple(im, px, py, clamp((tl - C) / 0.75), color=GREEN, radius=58 * zoom)
    if tl > D + 0.05:
        confetti(im, lay, t, clamp((tl - D - 0.05) / 1.9), origin=(lay["W"] / 2, lay["H"] * 0.40),
                 spread=lay["W"] * 0.92, n=58, seed=9)


def scene_library(im, lay, tl, t):
    P1, P2 = 1.3, 2.05
    if tl < P1:
        st = base_state(tab="lib", scroll={"lib": 0.0}, overlay="publish",
                        publish=dict(rate_p=ease_out_cubic(seg(tl, 0.25, 0.75)),
                                     publish_p=ease_out_cubic(seg(tl, 0.9, 1.25))))
    elif tl < P2:
        st = base_state(tab="lib", overlay=None, scroll={"lib": ease_in_out(seg(tl, P1, P2)) * 120})
    else:
        st = base_state(tab="lib", overlay="share", scroll={"lib": 120},
                        share_p=ease_out_cubic(seg(tl, P2, P2 + 0.5)),
                        code_p=ease_out_cubic(seg(tl, P2 + 0.45, P2 + 1.3)),
                        toast_p=ease_out_back(seg(tl, P2 + 1.35, P2 + 1.75)),
                        import_text="cyop_7fQ2mZk9LpXw")
    push = ease_out_cubic(seg(tl, 0.0, 0.9))
    zoom = zoom_for(1.0 + 0.16 * push, lay)
    caption(im, lay, *COPY["library"], appear=seg(tl, 0.05, 0.55), alpha=1 - seg(tl, 0.55, 1.15))
    info = place_phone(im, lay, st, t, cam(focus=(215, 500), zoom=zoom, center_on_focus=push > 0.002))
    if tl > 0.95:
        px, py = hit_screen(info, "m_publish_btn")
        ripple(im, px, py, clamp((tl - 0.95) / 0.8), color=GOLD, radius=58 * zoom)
    if tl > P2 + 1.3:
        px, py = hit_screen(info, "m_copy_btn")
        ripple(im, px, py, clamp((tl - P2 - 1.3) / 0.8), radius=52 * zoom)


def scene_cta(im, lay, tl, t):
    W, H = lay["W"], lay["H"]
    wide = lay["wide"]
    dark = ease_out_cubic(seg(tl, 0.0, 0.7))
    ink = gradient((W, H), (28, 18, 13), (11, 8, 6), "v").convert("RGBA")
    ink.putalpha(Image.new("L", (W, H), int(255 * dark)))
    im.alpha_composite(ink)
    cx = (W / 2) if not wide else lay["text_zone"][0] + 300
    cy = H * 0.30
    paste_c(im, radial_glow(int(W * 1.5), (255, 202, 112), 2.1, int(125 * dark)), cx, cy + 60)
    # logo
    lp = seg(tl, 0.25, 1.0)
    logo_size = int(min(W, H) * 0.20)
    if lp > 0:
        e = ease_out_back(lp, 1.2)
        size = max(8, int(logo_size * e))
        tile = rr(size, size, int(size * 0.22), fill=CREAM, outline=GOLD,
                  ow=max(2, int(size * 0.022)))
        inner = int(size * 0.84)
        lg = Image.open(os.path.join(ROOT, "assets", "icon-512.png")).convert("RGBA").resize(
            (inner, inner), Image.LANCZOS)
        tile.alpha_composite(lg, (int(size * 0.08), int(size * 0.08)))
        burst = radial_glow(int(size * 3.4), (255, 214, 140), 2.4,
                            int(170 * (1 - clamp(lp * 1.7 - 0.5))))
        paste_c(im, burst, cx, cy)
        paste_c(im, tile, cx, cy)
        ring_p = ease_out_cubic(seg(tl, 0.4, 1.6))
        if ring_p < 1:
            ring = circle(int(size * (1.4 + 1.0 * ring_p)), fill=None,
                          outline=GOLD_LT + (int(150 * (1 - ring_p)),), ow=4)
            paste_c(im, ring, cx, cy)
    y = cy + logo_size * 0.78
    # wordmark
    wp = seg(tl, 0.8, 1.45)
    if wp > 0:
        wsize = int(min(W * 0.105, H * 0.105)) if not wide else int(W * 0.062)
        y += wsize * 0.6
        reveal_line(im, lay, cx, y, "STORYTELLER", "display", "black", wsize, PARCH, wp,
                    spacing=wsize * 0.05, align="center", width=W)
        y += wsize * 1.02
        sub = font("garamond", 42 if not wide else 38, "semibold")
        a = int(255 * ease_out_cubic(seg(tl, 1.15, 1.75)))
        if a > 4:
            txt = "WRITE YOUR OWN ADVENTURE"
            tw = sum(sub.getlength(c) for c in txt) + 7 * (len(txt) - 1)
            text_spaced(ImageDraw.Draw(im), (cx - tw / 2, y + 8), txt, sub, GOLD_LT + (a,), 7)
        y += 70
    # CTA button
    bp = seg(tl, 1.7, 2.3)
    if bp > 0:
        e = ease_out_back(bp)
        label = "Play free in your browser"
        bw = int(min(W * 0.80, 780))
        bh = int(H * 0.062) if not wide else 100
        by = y + 40 + (1 - e) * 40
        bx = cx - bw / 2
        f = fit_font(label, "display", "bold", bw - 190, int(bh * 0.44))
        a = 0.5 + 0.5 * math.sin(t * 4.4)
        halo = rr(bw + 48, bh + 48, 24, fill=None, outline=GOLD_LT + (int(60 + 70 * a),), ow=4)
        paste_c(im, halo, bx + bw / 2, by + bh / 2)
        paste(im, rr(bw, bh, int(bh * 0.22), fill=GOLD, outline=(255, 228, 155, 255), ow=3), (bx, by))
        ic = emoji_img("25B6", int(bh * 0.44))
        paste_c(im, ic, bx + bh * 0.62, by + bh / 2, int(255 * clamp(bp * 3)))
        ImageDraw.Draw(im).text((bx + bh * 1.0, by + bh / 2), label, font=f, fill=INK, anchor="lm")
        y = by + bh + 34
    # url chip
    up_ = seg(tl, 2.15, 2.75)
    if up_ > 0:
        f = font("garamond", 42 if not wide else 38, "semibold")
        tw = sum(f.getlength(c) for c in URL) + 1.6 * (len(URL) - 1)
        chip = rr(int(tw + 100), int(92), 46, fill=(255, 255, 255, int(26 * up_)),
                  outline=GOLD_LT + (int(150 * up_),), ow=2)
        paste_c(im, chip, cx, y + 46)
        text_spaced(ImageDraw.Draw(im), (cx - tw / 2, y + 20), URL, f,
                    PARCH + (int(255 * up_),), 1.6)
        y += 118
    fp = seg(tl, 2.5, 3.05)
    if fp > 0:
        a = int(240 * ease_out_cubic(fp))
        line = "Free  ·  No account  ·  Private by design  ·  Works offline"
        sf = font("garamond", 34 if not wide else 32)
        ImageDraw.Draw(im).text((cx, y + 14), line, font=sf, fill=(234, 222, 200, a), anchor="ma")
        row = ["1F512", "1F4C1", "1F3EB", "2728"]
        gap = 112
        for i, ic in enumerate(row):
            sprite = emoji_img(ic, 56)
            paste_c(im, sprite, cx - gap * (len(row) - 1) / 2 + i * gap, y + 84, a)
    rs = np.random.RandomState(3)
    for i in range(18):
        ph = (tl * 0.15 + rs.rand()) % 1.0
        a = int(150 * math.sin(math.pi * ph) * dark)
        if a <= 5:
            continue
        sprite = emoji_img("2728" if i % 3 else "2B50", 12 + int(rs.rand() * 10) * 3)
        paste_c(im, sprite, rs.rand() * W, H * (1.06 - ph * 1.16), a)


warm_hits()
# content-space anchors the camera needs before a frame is drawn
BUILD_FOCUS_Y = HIT["c_choice_B"][1] + CONTENT_TOP
PLAY_CHOICE_ENTRY_Y = 0.0

SCENE_FN = {"hook": scene_hook, "hero": scene_hero, "build": scene_build, "convert": scene_convert,
            "play": scene_play, "library": scene_library, "cta": scene_cta}


# ---------------------------------------------------------------------------
# compositor
# ---------------------------------------------------------------------------
_RAMP_CACHE = {}


def ramp_mask(lay):
    key = (lay["W"], lay["H"])
    if key not in _RAMP_CACHE:
        W, H = lay["W"], lay["H"]
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = (x / W) * 0.84 + (y / H) * 0.16
        r -= r.min()
        r /= r.max()
        _RAMP_CACHE[key] = r
    return _RAMP_CACHE[key]


def scene_frame(name, lay, tl, t):
    SPANS.clear()
    im = bg(lay, t)
    SCENE_FN[name](im, lay, tl, t)
    return im


def render_frame(t, lay):
    idx = len(SCENES) - 1
    for i, (n, s, e) in enumerate(SCENES):
        if s <= t < e:
            idx = i
            break
    name, s, e = SCENES[idx]
    cur = scene_frame(name, lay, t - s, t)
    if idx > 0 and (t - s) < XFADE:
        pn, ps, pe = SCENES[idx - 1]
        prev = scene_frame(pn, lay, (pe - ps) - 0.001, t)
        p = ease_in_out((t - s) / XFADE)
        ramp = ramp_mask(lay)
        band = 0.24
        m = np.clip((p * (1 + band) - ramp) / band, 0, 1).astype(np.float32)
        out = Image.composite(cur, prev, Image.fromarray((m * 255).astype(np.uint8), "L"))
        edge = np.exp(-(((m - 0.5) / 0.17) ** 2)).astype(np.float32)
        g = np.dstack([(edge * 255).astype(np.uint8)] * 3).astype(np.uint8)
        gl = Image.fromarray(g, "RGB").convert("RGBA")
        gl.putalpha(Image.fromarray((edge * 150).astype(np.uint8), "L"))
        out.alpha_composite(gl)
        cur = out
    return finish(cur, lay, t)


# ---------------------------------------------------------------------------
# encoding
# ---------------------------------------------------------------------------
def ffmpeg():
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


_WORKER_LAY = None
_WORKER_T0 = 0.0
_WORKER_FPS = FPS


def _worker_init(lay, t0, fps):
    global _WORKER_LAY, _WORKER_T0, _WORKER_FPS
    _WORKER_LAY, _WORKER_T0, _WORKER_FPS = lay, t0, fps


def _worker_frame(i):
    return render_frame(_WORKER_T0 + i / _WORKER_FPS, _WORKER_LAY).tobytes()


def render_video(lay, out_path, fps=FPS, t0=0.0, t1=None, progress=True, jobs=None):
    """Render frames (optionally across processes) straight into ffmpeg."""
    W, H = lay["W"], lay["H"]
    t1 = t1 if t1 is not None else TOTAL
    n = int(round((t1 - t0) * fps))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # crf + maxrate keeps the grain-heavy frames from ballooning the file, which
    # keeps the upload small on every platform ('slow' preset would cost more CPU
    # than the render itself on a small box)
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-tune", "film",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    jobs = jobs or max(1, (os.cpu_count() or 2))
    if jobs > 1:
        import multiprocessing as mp

        with mp.Pool(jobs, initializer=_worker_init, initargs=(lay, t0, fps)) as pool:
            for i, raw in enumerate(pool.imap(_worker_frame, range(n), chunksize=4)):
                proc.stdin.write(raw)
                if progress and i % 120 == 0:
                    print(f"  {os.path.basename(out_path)}  {i}/{n}  t={t0 + i / fps:5.2f}s",
                          flush=True)
    else:
        for i in range(n):
            proc.stdin.write(_worker_frame(i))
            if progress and i % 60 == 0:
                print(f"  {os.path.basename(out_path)}  {i}/{n}  t={t0 + i / fps:5.2f}s",
                      flush=True)
    proc.stdin.close()
    proc.wait()
    return out_path


def render_stills(lay, times, out_dir, tag=""):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for t in times:
        fr = render_frame(float(t), lay)
        p = os.path.join(out_dir, f"{tag}{t:06.2f}.png".replace(" ", "_"))
        fr.save(p)
        paths.append(p)
    return paths


def contact_sheet(paths, cols=4, cell=400, out=None):
    ims = [Image.open(p).convert("RGB") for p in paths]
    rows = (len(ims) + cols - 1) // cols
    cw = cell
    ch = int(cell * ims[0].height / ims[0].width)
    sheet = Image.new("RGB", (cols * cw + (cols + 1) * 8, rows * ch + (rows + 1) * 8), (30, 25, 20))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((cw, ch), Image.LANCZOS),
                    (8 + (i % cols) * (cw + 8), 8 + (i // cols) * (ch + 8)))
    if out:
        sheet.save(out)
    return sheet


def check(lay, times):
    """Numerically verify that captions, chrome and tap targets stay clear of
    the phone mockup across the whole film."""
    problems = []
    for t in times:
        SPANS.clear()
        render_frame(float(t), lay)
        phone = SPANS.get("phone")
        cap = SPANS.get("caption")
        if not phone:
            continue
        if cap and _overlap(cap, phone):
            problems.append(f"t={t:5.2f} caption {_b(cap)} overlaps phone {_b(phone)}")
        if phone[1] < -lay["H"] * 0.40:
            problems.append(f"t={t:5.2f} phone over-cropped at top ({phone[1]:.0f})")
        if phone[3] > lay["H"] + lay["H"] * 0.05:
            problems.append(f"t={t:5.2f} phone over-cropped at bottom ({phone[3]:.0f} > {lay['H']})")
        if lay["wide"] and (phone[0] < -4 or phone[2] > lay["W"] + 4):
            problems.append(f"t={t:5.2f} phone clipped horizontally {_b(phone)}")
    return problems


def _overlap(a, b, pad=6):
    return not (a[2] < b[0] + pad or b[2] < a[0] + pad or a[3] < b[1] + pad or b[3] < a[1] + pad)


def _b(r):
    return f"({r[0]:.0f},{r[1]:.0f})-({r[2]:.0f},{r[3]:.0f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aspect", default="vertical",
                    choices=["vertical", "square", "landscape", "all"])
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--times", default="")
    ap.add_argument("--range", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    aspects = ["vertical", "square", "landscape"] if args.aspect == "all" else [args.aspect]
    for asp in aspects:
        lay = make_layout(asp)
        if args.check:
            times = [round(s + (e - s) * f, 2) for (n, s, e) in SCENES for f in
                     (0.3, 0.45, 0.6, 0.75, 0.9)]
            probs = check(lay, times)
            print(f"[{asp}] {'OK' if not probs else 'ISSUES'}")
            for p in probs:
                print("   ", p)
            continue
        if args.stills:
            times = ([float(x) for x in args.times.split(",")] if args.times
                     else [s + (e - s) * f for (n, s, e) in SCENES for f in (0.4, 0.8)])
            paths = render_stills(lay, times, os.path.join(args.out, "stills", asp), tag=args.tag)
            sheet = contact_sheet(paths, cols=4 if lay["aspect"] == "vertical" else 3,
                                  out=os.path.join(args.out, "stills", f"sheet-{asp}.png"))
            print("sheet:", os.path.join(args.out, "stills", f"sheet-{asp}.png"))
        else:
            t0, t1 = (0.0, TOTAL)
            if args.range:
                a, b = args.range.split(":")
                t0, t1 = float(a), float(b)
            out = os.path.join(args.out, f"storyteller-cyop-promo-{asp}.mp4")
            render_video(lay, out, fps=args.fps, t0=t0, t1=t1)
            print("video:", out)


if __name__ == "__main__":
    main()
