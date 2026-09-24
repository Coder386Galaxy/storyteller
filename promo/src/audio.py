"""Soundtrack for the Storyteller CYOP promo film.

A warm storybook music bed (harp/bell arpeggios, soft pads, low roots) plus
UI sound design cued to the film's timeline: typing ticks while the story is
written, taps on the choices, a flourish on the victory, a ding on publish.

Everything is synthesised from scratch with numpy — no sample libraries — so the
audio is reproducible alongside the video, and the cue list reads against the
same SCENES timeline that drives the picture.

Voicing notes (these matter for how it sounds):
  * Struck tones use *harmonic* partials with piano-like inharmonicity
    (f_n = n*f*sqrt(1 + B*n^2), B ~ 3e-4) and per-partial damping, so a harp
    note rings like a string rather than clanging like a gong.
  * High partials are rolled off instead of being kept at equal amplitude, and
    the whole mix is gently tilted down above ~7 kHz.
  * Noise effects are band-limited per segment with overlapping FFT windows
    rather than a high-Q resonator, so whooshes never whistle.
  * Nothing is soft-clipped: peaks are held with an envelope follower, which
    avoids the fuzzy distortion tanh() limiting adds on loud stacks.
"""
from __future__ import annotations

import os
import wave

import numpy as np

SR = 48000
TOTAL = 30.4


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def _n(dur):
    return int(round(dur * SR))


def _t(dur):
    return np.arange(_n(dur)) / SR


def _fft_lowpass(x, cutoff, order=2.0):
    """Zero-phase low-pass via a smooth spectral mask (no filter ringing to
    speak of, and no per-sample Python loop)."""
    n = len(x)
    if n < 8:
        return x
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = 1.0 / np.sqrt(1.0 + (f / max(1.0, cutoff)) ** (2 * order))
    return np.fft.irfft(spec * mask, n)


def _fft_highshelf_cut(x, corner=7000.0, gain_db=-3.0):
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    amt = 10 ** (gain_db / 20.0)
    w = 0.5 * (1 + np.tanh((f - corner) / (corner * 0.6)))
    return np.fft.irfft(spec * (1 + (amt - 1) * w), n)


def _fft_lowshelf(x, corner=220.0, gain_db=3.0):
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    amt = 10 ** (gain_db / 20.0)
    w = 0.5 * (1 - np.tanh((f - corner) / (corner * 0.7)))
    return np.fft.irfft(spec * (1 + (amt - 1) * w), n)


def taken(buf, sig, at):
    """Add sig into buf at sample offset at, clipped to the buffer length."""
    at = int(round(at))
    if at >= len(buf) or at < 0:
        return
    m = min(len(sig), len(buf) - at)
    if m > 0:
        buf[at:at + m] += sig[:m]


def harp(freq, dur=1.4, amp=0.2, bright=0.55, B=3.2e-4):
    """Struck string: harmonic partials with light inharmonicity and damping.

    bright ~0.5 is a soft harp/pluck, 1.0 a brighter bell.
    """
    t = _t(dur)
    out = np.zeros_like(t)
    for part in range(1, 8):
        f = freq * part * np.sqrt(1.0 + B * part * part)
        if f > SR * 0.45:
            break
        a = bright ** (part - 1) / (part ** 1.35)
        # higher partials decay faster, as on a real string
        damp = 2.4 + 0.9 * (part - 1) + 1.4 / max(dur, 0.25)
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t * damp)
    # soft attack transient, then a clean tail
    env = 1 - np.exp(-t * 420)
    out *= env
    tail = min(len(out), _n(0.06))
    if tail:
        out[-tail:] *= np.linspace(1, 0, tail) ** 1.4
    return out / 2.1 * amp


def piano(freq, dur=2.0, amp=0.15):
    return harp(freq, dur, amp, bright=0.62, B=4.5e-4)


def pad(freqs, dur, amp=0.07, attack=0.7, release=0.9):
    """Breathy sustained chord: three gently detuned voices per note, harmonic
    spectrum rolled off, then low-passed. Warm rather than buzzy."""
    t = _t(dur)
    out = np.zeros_like(t)
    for f in freqs:
        for k, cents in enumerate((-6.0, 0.0, 5.0)):
            # slow chorus drift, deterministic but decorrelated per voice
            lfo = 1 + 0.0009 * np.sin(2 * np.pi * (0.13 + 0.05 * k) * t + k * 2.1)
            fd = f * (2 ** (cents / 1200.0)) * lfo
            ph = 2 * np.pi * np.cumsum(fd) / SR
            voice = np.zeros_like(t)
            for part in range(1, 7):
                voice += np.sin(part * ph + k * 0.7) / (part ** 1.75)
            out += voice
    out /= max(1, len(freqs) * 3)
    out = _fft_lowpass(out, 1900.0, order=2.4)
    out -= out.mean()
    env = np.ones_like(t)
    ai, ri = min(_n(attack), len(t) // 2), min(_n(release), len(t) // 2)
    if ai:
        env[:ai] = np.linspace(0, 1, ai) ** 1.5
    if ri:
        env[-ri:] *= np.linspace(1, 0, ri) ** 1.25
    return out * env * amp * 6.0


def air(dur, f0, f1, amp=0.10, width=1.1, chunks=40):
    """Band-swept noise built from overlapping FFT-filtered segments.

    A single time-varying resonator (the obvious approach) rings at high Q and
    whistles; segmenting keeps the band smooth and artefact-free.
    """
    n = _n(dur)
    src = np.random.randn(n + SR // 10)
    out = np.zeros(n)
    win = np.hanning(n // chunks * 2 + 1)[None, :].ravel()
    step = max(1, (n - len(win)) // max(1, chunks - 1))
    freqs = np.geomspace(max(60.0, f0), max(60.0, f1), chunks)
    for i, fc in enumerate(freqs):
        s = i * step
        seg = src[s:s + len(win)]
        if len(seg) < len(win):
            seg = np.pad(seg, (0, len(win) - len(seg)))
        w = win[: len(seg)]
        spec = np.fft.rfft(seg * w)
        f = np.fft.rfftfreq(len(seg), 1 / SR)
        band = np.exp(-0.5 * ((np.log2(np.maximum(f, 20) / fc)) / (width * 0.6)) ** 2)
        cut = 1.0 / np.sqrt(1.0 + (f / (fc * 4.5)) ** 4)
        shaped = np.fft.irfft(spec * band * cut, len(seg))
        taken(out, shaped * w, s)
    return out * amp * 3.2 / max(0.2, np.abs(out).max() / 0.35)


def click(amp=0.085):
    """UI tap: a soft wooden thock.

    Deliberately dark (noise under 1.6 kHz + a 900 Hz body): the first pass was
    voiced around 2-3 kHz, which read as a bright fizz on phone speakers and was
    what made the typing and the AI-processing sections sound odd.
    """
    t = _t(0.06)
    body = _fft_lowpass(np.random.randn(len(t)), 1600.0, 1.8)
    body *= np.exp(-t * 130)
    body += np.sin(2 * np.pi * 880 * t) * np.exp(-t * 90) * 0.35
    body += np.sin(2 * np.pi * 220 * t) * np.exp(-t * 70) * 0.18
    body = _fft_lowpass(body, 4500.0, 1.4)
    return body / max(1e-9, np.abs(body).max()) * amp


def pop(dur=0.24, f=660.0, amp=0.12):
    """A row or panel appearing: soft marimba-ish blip."""
    v = harp(f, dur, amp, bright=0.42)
    t = _t(dur)
    return v * (1 - np.exp(-t * 90))


def ding(freqs=(1046.5, 1568.0), dur=1.7, amp=0.15):
    out = np.zeros(_n(dur))
    for i, f in enumerate(freqs):
        taken(out, harp(f, dur, amp * (1.0 if i == 0 else 0.62), bright=0.9), 0)
    return out


def flourish(base=587.33, notes=(0, 4, 7, 12, 16), step=0.085, dur=1.9, amp=0.16):
    """Victory: rising harp arpeggio with a ringing top note."""
    total = step * len(notes) + dur
    out = np.zeros(_n(total))
    for i, semi in enumerate(notes):
        f = base * (2 ** (semi / 12))
        taken(out, harp(f, dur, amp * (0.78 + 0.05 * i), bright=0.7), _n(i * step))
    return out


def thud(f=58.0, dur=1.6, amp=0.22):
    """Low, soft boom for the end card — body above 50 Hz so small speakers
    stay clean."""
    t = _t(dur)
    env = np.exp(-t * 3.6) * (1 - np.exp(-t * 70))
    body = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t)
    body = _fft_lowpass(body, 220.0, 2.0)
    rumble = _fft_lowpass(np.random.randn(len(t)), 180.0, 1.5) * np.exp(-t * 9) * 0.25
    return (body * env + rumble) * amp


# ---------------------------------------------------------------------------
# musical bed
# ---------------------------------------------------------------------------
D3, E3, Fs3, G3, A3, B3 = 146.83, 164.81, 185.00, 196.00, 220.00, 246.94
D4, E4, Fs4, G4, A4, B4 = 293.66, 329.63, 369.99, 392.00, 440.00, 493.88
Cs5, D5, E5, Fs5, A5, B5, D6, E6 = 554.37, 587.33, 659.26, 739.99, 880.00, 987.77, 1174.66, 1318.51

BAR = 3.8
# D  A/C#  Bm  G  |  D  A  Bm  G->A  (lift into the victory, home on the card)
PROGRESSION = [
    ([D3, A3, D4, Fs4], [D4, Fs4, A4, D5, A4, Fs4]),
    ([A3, E4, A4, Cs5], [A4, Cs5, E5, A4, E5, Cs5]),
    ([B3, Fs4, B4, D5], [B4, D5, Fs5, D5, Fs5, B5]),
    ([G3, D4, G4, B4], [G4, B4, D5, B4, D5, G4]),
    ([D3, A3, D4, Fs4], [D5, Fs5, A5, D6, A5, Fs5]),
    ([A3, E4, A4, Cs5], [A5, E5, Cs5, E5, A5, Cs5]),
    ([B3, Fs4, B4, D5], [B5, Fs5, D5, Fs5, B5, D6]),
    ([G3, B3, D4, A4], [D6, B5, A5, Fs5, D5, A4]),
]

# energy per scene, so the bed breathes with the edit
ENERGY = [(0.0, 0.0, 0.52), (0.6, 3.2, 0.70), (3.2, 6.8, 0.78), (6.8, 11.4, 0.64),
          (11.4, 15.4, 0.72), (15.4, 21.8, 0.94), (21.8, 25.8, 0.78), (25.8, 30.4, 1.0)]


def energy_env(n):
    env = np.zeros(n)
    level = 0.0
    for a, b, lvl in ENERGY:
        i0, i1 = _n(a), min(n, _n(b))
        if i1 <= i0:
            continue
        env[i0:i1] = lvl
        ramp = min(_n(0.7), (i1 - i0) // 2)
        if ramp:
            env[i0:i0 + ramp] = np.linspace(level, lvl, ramp)
        level = lvl
    return env


def music(n):
    bed = np.zeros(n)
    for bar, (chord, arp) in enumerate(PROGRESSION):
        start = _n(bar * BAR)
        if start >= n:
            break
        taken(bed, pad(chord, BAR * 1.08, amp=0.075), start)
        taken(bed, piano(chord[0] / 2, dur=2.1, amp=0.20), start)
        # a quiet sub-octave root gives the bed weight on phone speakers too
        root = chord[0] / 2
        t = _t(1.9)
        sub = (np.sin(2 * np.pi * root * t) * 0.7 + np.sin(2 * np.pi * root * 2 * t) * 0.3)
        sub *= np.exp(-t * 2.2) * (1 - np.exp(-t * 60)) * 0.085
        taken(bed, sub, start)
        step = BAR / 8
        for i in range(8):
            s = _n(bar * BAR + i * step + (np.random.rand() - 0.5) * 0.008)
            if s >= n:
                break
            note = harp(arp[i % len(arp)], dur=1.5,
                        amp=(0.125 if i % 2 == 0 else 0.092) * (0.93 + 0.14 * np.random.rand()),
                        bright=0.52)
            taken(bed, note, s)
    return bed * energy_env(n)


# ---------------------------------------------------------------------------
# sound design cues (times read against the film's SCENES timeline)
# ---------------------------------------------------------------------------
def cues(n):
    sfx = np.zeros(n)

    def put(sig, at, gain=1.0):
        if at >= n / SR or at < 0:
            return
        taken(sfx, sig * gain, _n(at))

    # hook: soft page rustle, a chime per word, a shimmer under the gold rule
    put(air(0.5, 1500, 400, 0.085), 0.16)
    put(harp(D5, 1.5, 0.10, bright=0.6), 0.52)
    put(harp(Fs5, 1.5, 0.10, bright=0.6), 1.22)
    put(harp(A5, 1.9, 0.12, bright=0.65), 1.90)
    put(air(0.42, 600, 2200, 0.05), 2.55)

    # hero: swipe in, button highlight, tap, AI-button nudge
    put(air(0.45, 2200, 700, 0.08), 3.20)
    put(pop(0.3, 784.0, 0.10), 4.52)
    put(click(0.13), 4.95)
    put(pop(0.3, 880.0, 0.10), 6.18)

    # build: whoosh in, typing ticks, the three choice rows landing
    put(air(0.45, 2000, 600, 0.08), 6.80)
    tt = 7.05
    while tt < 9.0:
        put(click(0.045 + 0.025 * np.random.rand()), tt)
        tt += 0.085 + np.random.rand() * 0.045
    for i, f in enumerate((D5, Fs5, A5)):
        put(pop(0.26, f, 0.10), 9.00 + i * 0.17)
    put(click(0.12), 10.55)

    # AI convert: whoosh in, processing ticks, a warm double ding
    put(air(0.45, 1900, 650, 0.08), 11.40)
    tt = 12.30
    while tt < 14.00:
        put(click(0.03), tt)
        tt += 0.16 + np.random.rand() * 0.1
    put(ding((D5, A5), 1.9, 0.13), 14.22)

    # play: taps on the choices, page turn, victory flourish
    put(air(0.45, 2000, 650, 0.08), 15.40)
    put(pop(0.3, 660.0, 0.09), 15.72)
    put(click(0.14), 17.80)
    put(air(0.4, 800, 2400, 0.075), 18.48)
    put(click(0.13), 19.60)
    put(thud(62.0, 1.2, 0.13), 20.10)
    put(flourish(D5, step=0.085, dur=2.0, amp=0.15), 20.15)
    put(harp(D6, 2.2, 0.09, bright=0.75), 20.60)

    # library: publish click + ding, share sheet, copy chime
    put(air(0.45, 1900, 600, 0.08), 21.80)
    put(click(0.13), 22.42)
    put(ding((A5, D6), 1.8, 0.13), 22.96)
    put(air(0.45, 500, 1500, 0.085), 23.82)
    put(click(0.12), 25.02)
    put(harp(D6, 1.4, 0.09, bright=0.8), 25.18)

    # end card: warm boom, CTA pop, URL chime, sparkle, resolve
    put(thud(56.0, 2.2, 0.22), 25.82)
    put(harp(D4, 2.4, 0.11, bright=0.5), 25.86)
    put(pop(0.34, 523.25, 0.11), 27.48)
    put(ding((D5, Fs5, A5), 2.4, 0.11), 27.94)
    put(harp(A5, 1.6, 0.06, bright=0.7), 28.42)
    put(harp(D6, 2.6, 0.07, bright=0.7), 29.10)
    return sfx


# ---------------------------------------------------------------------------
# mix
# ---------------------------------------------------------------------------
def _hold_peaks(x, ceiling=0.89, attack=0.004, release=0.16):
    """Envelope-follower peak holding — transparent, unlike soft clipping."""
    env = np.abs(x)
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    out = np.empty_like(env)
    cur = 0.0
    for i in range(len(env)):
        target = env[i]
        cur = target + (cur - target) * (a if target > cur else r)
        out[i] = cur
    gain = np.ones_like(x)
    hot = out > ceiling
    gain[hot] = ceiling / out[hot]
    # smooth the gain curve so gain changes are inaudible
    g = _fft_lowpass(gain, 120.0, 1.5)
    return x * g


def build(duration=TOTAL):
    n = _n(duration)
    np.random.seed(20260922)
    mix = music(n) * 1.0 + cues(n) * 1.0
    mix = _fft_highshelf_cut(mix, 6500.0, -2.5)      # take the edge off
    mix = _fft_lowpass(mix, 14000.0, 1.2)            # and the fizzy top
    mix = _fft_lowshelf(mix, 230.0, 3.0)             # body back in the low end
    mix = _hold_peaks(mix, 0.85)
    fi, fo = _n(0.45), _n(1.0)
    mix[:fi] *= np.linspace(0, 1, fi) ** 1.2
    mix[-fo:] *= np.linspace(1, 0, fo) ** 1.25
    # stereo: slight width on the upper material, bass kept centred
    mono = _fft_lowpass(mix, 240.0, 1.6)
    top = mix - mono
    d = _n(0.012)
    wide = np.concatenate([np.zeros(d), top[:-d]]) * 0.5
    left = mono + top - wide * 0.16
    right = mono + top + wide * 0.16
    stereo = np.stack([left, right], axis=1)
    # normalise the finished mix to a broadcast-ish level: loud enough for a
    # feed, with headroom left for the AAC encode
    peak = float(np.max(np.abs(stereo))) or 1.0
    stereo *= min(0.90 / peak, 3.2)
    rms = float(np.sqrt((stereo ** 2).mean()))
    if rms > 0:
        stereo *= min(1.0, 0.145 / rms)
    peak = float(np.max(np.abs(stereo))) or 1.0
    if peak > 0.89:
        stereo *= 0.89 / peak
    return stereo


def write_wav(path, stereo):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = np.clip(stereo, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "film", "audio",
        "promo-soundtrack.wav")
    print(write_wav(out, build()), "written")
