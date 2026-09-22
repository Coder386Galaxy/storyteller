"""Poster stills for the promo film — clean key frames at full resolution.

    python tools/posters.py

Writes out/posters/<aspect>-<name>.png: a hook card, a product shot and the end
card per aspect, framed at each aspect's native size so they can be used as
thumbnails, story covers or press images without reframing.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import render as R  # noqa: E402

# times chosen to land on settled, text-free-of-transition frames
SHOTS = [
    ("hook", 2.85),
    ("product", 5.60),
    ("reader", 19.55),
    ("endcard", 29.80),
]


def main():
    out_dir = os.path.join(R.ROOT, "film", "posters")
    os.makedirs(out_dir, exist_ok=True)
    for aspect in ("vertical", "square", "landscape"):
        lay = R.make_layout(aspect)
        for name, t in SHOTS:
            img = R.render_frame(t, lay)
            path = os.path.join(out_dir, f"{aspect}-{name}.png")
            img.save(path)
            print(f"{aspect:9s} {name:8s} t={t:5.2f}  ->  {os.path.relpath(path, R.ROOT)}")


if __name__ == "__main__":
    main()
