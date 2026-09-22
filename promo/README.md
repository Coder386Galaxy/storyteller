# Storyteller CYOP — promo film

A 30-second ad for **Storyteller CYOP** (`coder386galaxy.github.io/storyteller`),
rendered as three ready-to-post cuts: vertical 9:16, square 1:1 and landscape 16:9.

The film is not a screen recording: the app UI is **re-implemented in code**
(`src/appmock.py`) from the real `index.html` — same palette, same type scale,
same copy, same components — so every pixel is reproducible and can be animated
(typing, branches growing, the player overlay, the share sheet).

## Output

| File | Where it goes |
| --- | --- |
| `out/storyteller-cyop-promo-vertical.mp4` | Reels / Shorts / TikTok / Stories (1080×1920) |
| `out/storyteller-cyop-promo-square.mp4` | Feed posts (1080×1080) |
| `out/storyteller-cyop-promo-landscape.mp4` | YouTube / website hero (1920×1080) |

All three are 30.4 s, 30 fps, H.264 + `+faststart` (safe to upload anywhere).

## Story beats

| # | Scene | Beat |
| --- | --- | --- |
| 1 | `hook` | "WRITE YOUR OWN ADVENTURE" — the brand promise, in the app's own type |
| 2 | `hero` | The landing page; the camera presses in on **Start writing** |
| 3 | `build` | Passage editing, A/B/C choices appearing, then a push to the branch list |
| 4 | `convert` | Paste a messy draft → AI finalizes it → branches wire themselves up |
| 5 | `play` | Tapping through the reader: choice → illustrated scene → 🏆 Victory |
| 6 | `library` | ⚡ Publish (AI age rating, ST-2 school-friendly) → library → share code |
| 7 | `cta` | End card: logo, "Play free in your browser", the URL |

## Running it

```bash
pip install pillow numpy imageio-ffmpeg
python render.py --aspect all      # writes out/*.mp4
python render.py --check           # verify caption/device layout safety
python render.py --stills          # contact sheets in out/stills/
python render.py --aspect vertical --range 0:6   # quick partial render
```

`--check` renders a sparse set of times across the timeline and asserts that the
caption block, frame edges and the phone mockup never collide or over-crop.

## How it is built

- `render.py` — timeline, layouts, camera, scene direction, encoder.
  One timeline drives all three aspects: the phone sits in the frame and the copy
  lives in the text zone for that aspect (top for 9:16, left for 1:1 / 16:9),
  with per-aspect zoom limits so a push-in never eats the product.
- `src/appmock.py` — the app UI: header, tab bar, Home / Build / AI Convert /
  Library tabs, the reader overlay, publish modal and share sheet. Components
  register their screen coordinates in `HIT`, so the camera and the tap ripples
  aim at real buttons instead of hard-coded guesses.
- `src/kit.py` — drawing primitives (anti-aliased rounded rects, gradients,
  glows, drop shadows, paper grain, vignette) with bounded caches so animated
  sizes don't grow the process.
- `tools/build_emoji.py` — bakes the emoji sprites used by the UI into PNGs.

## Assets

- `assets/fonts/` — Playfair Display, Libre Baskerville, EB Garamond (SIL OFL).
- `assets/emoji/` — OpenMoji sprites (CC BY-SA 4.0, <https://openmoji.org>).
- `assets/photos/` — three storybook illustrations made for the sample adventure
  ("The Lantern on Blackrock Point") shown in the reader and library.
- `assets/icon-512.png` — the app icon, taken from the repo root.

## Editing notes

- Scene timings live in `SCENES`; copy lives in `COPY`.
- The product story is fictional but consistent: a four-passage adventure called
  **The Lantern on Blackrock Point** in the series **The Lantern Chronicles**.
- Keep the end card's URL in sync with the app's real host if it ever moves.
