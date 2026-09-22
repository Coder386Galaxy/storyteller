"""Bake the OpenMoji sprites the film needs into promo/assets/emoji/.

OpenMoji is CC BY-SA 4.0 (https://openmoji.org). The film only needs a couple
of dozen glyphs; they are cached as PNG so rendering never needs the source
SVG set. Run with an OpenMoji distribution available:

    python tools/build_emoji.py /path/to/openmoji_dist-17.0.0-py3-none-any.whl
"""
from __future__ import annotations

import io
import os
import sys
import zipfile

import resvg_py
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "emoji")

# codepoint -> the emoji the ad uses
GLYPHS = {
    "1F4D6": "open book (app logo)",
    "2728": "sparkles (AI)",
    "1F500": "shuffle (build/branch)",
    "1F4DA": "books (library)",
    "25B6": "play triangle",
    "1F480": "skull (death ending)",
    "1F3C6": "trophy (victory ending)",
    "1F4DD": "memo (write)",
    "1F4AC": "speech balloon",
    "1F517": "link (share codes)",
    "1F512": "lock (private)",
    "1F464": "bust (age/account)",
    "1F4C1": "folder (series)",
    "1F3EB": "school (school-friendly)",
    "1F3AF": "target",
    "26A1": "high voltage (publish)",
    "1F4E5": "inbox tray (import)",
    "2705": "check mark button",
    "2B50": "star",
    "1F4A1": "light bulb (tip)",
    "1F5BC": "framed picture (media pro)",
    "1F3AC": "clapper board (video)",
    "1F50A": "speaker high volume (sound)",
    "1F4C4": "page facing up",
    "1F9E0": "brain (AI convert)",
    "1F680": "rocket",
    "1F4F1": "mobile phone",
    "1F310": "globe",
    "1F4B0": "money bag (free)",
    "1F525": "fire",
    "1F441": "eye",
    "1F9ED": "compass",
    "1F5FA": "world map",
    "23F1": "stopwatch",
    "1F4CA": "bar chart (stats)",
    "1F3E0": "house (home tab)",
    "1F4CB": "clipboard (copy code)",
    "1F5A5": "desktop computer",
    "1F4BE": "floppy disk (save)",
    "1F4E4": "outbox tray (export)",
    "1F4E5": "inbox tray (import)",
    "1F4B3": "credit card (pro)",
}


def main(src: str) -> None:
    os.makedirs(OUT, exist_ok=True)
    zf = zipfile.ZipFile(src)
    names = {os.path.basename(n): n for n in zf.namelist() if n.endswith(".svg")}
    made = 0
    for code, label in GLYPHS.items():
        name = f"{code}.svg"
        if name not in names:
            print(f"  ! missing {code} ({label})")
            continue
        svg = zf.read(names[name]).decode("utf-8")
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=256, height=256))
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        im.save(os.path.join(OUT, f"{code}.png"))
        made += 1
    print(f"wrote {made} sprites to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "openmoji_dist-17.0.0-py3-none-any.whl")
