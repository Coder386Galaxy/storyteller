"""Soundtrack for the Storyteller CYOP promo film.

A warm storybook music bed (harp/bell arpeggios, soft pads, low roots) plus
UI sound design cued to the film's timeline: typing ticks while the story is
written, taps on the choices, a flourish on the victory, a ding on publish.

Everything is synthesised from scratch with numpy — no sample libraries — so the
audio is reproducible alongside the video, and the cue list reads against the
same SCENES timeline that drives the picture.
"""
from __future__ import annotations

import os
import struct
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


def bell(freq, dur=1.4, amp=0.2, bright=1.0, detune=0.0):
    """Struck bell/harp tone: a few inharmonic partials under an exp decay."""
    t = _t(dur)
    out = np.zeros_like(t)
    partials = ((1.0, 1.00), (2.01, 0.42 * bright), (2.99, 0.20 * bright),
                (4.21, 0.10 * bright), (5.43, 0.05 * bright))
    for mult, g in partials:
        f = freq * mult * (1 + detune)
        out += g * np.sin(2 * np.pi * f * t + np.random.rand() * 0.4)
    env = np.exp(-t * (2.6 + 1.6 / max(dur, 0.2))) * (1 - np.exp(-t * 320))
    tail = min(len(t), _n(0.035))
    env[:tail] *= np.linspace(0, 1, tail)
    return out * env * amp


def pluck(freq, dur=1.1, amp=0.16):
    """Softer, rounder version of bell() for the arpeggio bed."""
    return bell(freq, dur, amp, bright=0.55)


def pad(freqs, dur, amp=0.07, attack=0.6, release=0.8):
    """Breathy sustained chord: detuned saws through a one-pole low-pass."""
    t = _t(dur)
    out = np.zeros_like(t)
    for f in freqs:
        for d in (-0.0035, 0.0, 0.0042):
            partial = np.zeros_like(t)
            for h in (1, 2, 3, 4):
                # naive saw via harmonics, rolled off so the pad stays soft
                partial += np.sin(2 * np.pi * f * h * (1 + d) * t) / (h ** 1.9)
            out += partial
    out /= max(1, len(freqs) * 3)
    # one-pole low-pass, then remove the DC the filter introduces
    a = 0.055
    y = np.empty_like(out)
    acc = 0.0
    for i in range(len(out)):
        acc += a * (out[i] - acc)
        y[i] = acc
    y = y - y.mean()
    env = np.ones_like(t)
    ai, ri = _n(attack), _n(release)
    ai, ri = min(ai, len(t) // 2), min(ri, len(t) // 2)
    env[:ai] = np.linspace(0, 1, ai) ** 1.6
    env[-ri:] *= np.linspace(1, 0, ri) ** 1.3
    return y * env * amp


def noise_sweep(dur, f0, f1, amp=0.12, q=1.6):
    """Band-passed noise swept from f0 to f1 — whooshes and page turns."""
    t = _t(dur)
    src = np.random.randn(len(t))
    out = np.zeros_like(src)
    # sweeping two-pole resonator implemented as a time-varying biquad
    y1 = y2 = 0.0
    freqs = np.geomspace(max(60.0, f0), max(60.0, f1), len(t))
    for i, f in enumerate(freqs):
        w = 2 * np.pi * f / SR
        r = max(0.90, 1 - (w / (2 * q)))
        b0 = (1 - r) * np.sqrt(1 - r * r)
        y = b0 * src[i] + 2 * r * np.cos(w) * y1 - r * r * y2
        y2, y1 = y1, y
        out[i] = y
    env = np.sin(np.linspace(0, np.pi, len(t))) ** 1.4
    return out * env * amp * 6


def click(amp=0.16, f=2100.0):
    """UI tap: a tiny filtered noise tick plus a soft body."""
    t = _t(0.05)
    tick = np.random.randn(len(t)) * np.exp(-t * 260) * 0.5
    body = np.sin(2 * np.pi * f * t) * np.exp(-t * 90)
    return (tick + body * 0.5) * amp


def pop(dur=0.22, f=660.0, amp=0.14):
    """Row/item appearing."""
    t = _t(dur)
    env = np.exp(-t * 22) * (1 - np.exp(-t * 500))
    return np.sin(2 * np.pi * f * t) * env * amp


def ding(freqs=(1046.5, 1568.0), dur=1.6, amp=0.16):
    out = np.zeros(_n(dur))
    for i, f in enumerate(freqs):
        take(out, bell(f, dur, amp * (1.0 if i == 0 else 0.7)), 0)
    return out


def flourish(base=587.33, notes=(0, 4, 7, 12, 16), step=0.085, dur=1.9, amp=0.17):
    """Victory: a rising arpeggio with a ringing top note."""
    total = step * len(notes) + dur
    out = np.zeros(_n(total))
    for i, semi in enumerate(notes):
        f = base * (2 ** (semi / 12))
        v = bell(f, dur, amp * (0.75 + 0.05 * i), bright=0.9)
        take(out, v, _n(i * step))
    return out


def thud(f=68.0, dur=1.5, amp=0.30):
    """Low soft boom for the end card."""
    t = _t(dur)
    env = np.exp(-t * 3.4) * (1 - np.exp(-t * 90))
    body = np.sin(2 * np.pi * f * t) * env
    sub = np.sin(2 * np.pi * f * 0.5 * t) * env * 0.6
    return (body + sub) * amp


# ---------------------------------------------------------------------------
# musical bed
# ---------------------------------------------------------------------------
D3, E3, Fs3, G3, A3, B3 = 146.83, 164.81, 185.00, 196.00, 220.00, 246.94
D4, E4, Fs4, G4, A4, B4 = 293.66, 329.63, 369.99, 392.00, 440.00, 493.88
Cs5, D5, E5, Fs5, A5, B5, D6, E6, Fs6, A6 = (554.37, 587.33, 659.26, 739.99, 880.00,
                                            987.77, 1174.66, 1318.51, 1479.98, 1760.00)

BAR = 3.8
# D  A/C#  Bm  G  |  D  A  Bm  G -> A (lift, resolve home on the end card)
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
ENERGY = [(0.0, 0.0, 0.55), (0.6, 3.2, 0.72), (3.2, 6.8, 0.80), (6.8, 11.4, 0.68),
          (11.4, 15.4, 0.74), (15.4, 21.8, 0.95), (21.8, 25.8, 0.80), (25.8, 30.4, 1.0)]


def take(buf, sig, at):
    """Add sig into buf at sample offset at, clipped to the buffer length."""
    if at >= len(buf) or at < 0:
        return
    m = min(len(sig), len(buf) - at)
    if m > 0:
        buf[at:at + m] += sig[:m]


def energy_env(n):
    env = np.zeros(n)
    level = 0.0
    for a, b, lvl in ENERGY:
        i0, i1 = _n(a), min(n, _n(b))
        if i1 <= i0:
            continue
        env[i0:i1] = lvl
        ramp = min(_n(0.6), (i1 - i0) // 2)
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
        # pad
        p = pad(chord, BAR * 1.06, amp=0.085)
        take(bed, p, start)
        # bass root
        b = bell(chord[0] / 2, dur=1.9, amp=0.16, bright=0.25)
        take(bed, b, start)
        # harp arpeggio, 8th notes with a little humanisation
        step = BAR / 8
        for i in range(8):
            s = _n(bar * BAR + i * step + (np.random.rand() - 0.5) * 0.012)
            if s >= n:
                break
            f = arp[i % len(arp)]
            v = 0.135 if i % 2 == 0 else 0.10
            note = pluck(f, dur=1.35, amp=v * (0.9 + 0.2 * np.random.rand()))
            take(bed, note, s)
    return bed * energy_env(n)


# ---------------------------------------------------------------------------
# sound design cues (times read against the film's SCENES timeline)
# ---------------------------------------------------------------------------
def cues(n):
    sfx = np.zeros(n)

    def put(sig, at, gain=1.0):
        if at >= n / SR or at < 0:
            return
        s = _n(at)
        m = min(len(sig), n - s)
        if m > 0:
            sfx[s:s + m] += sig[:m] * gain

    # hook: paper whoosh + a sparkle per word, flourish under the gold rule
    put(noise_sweep(0.55, 1900, 300, 0.10), 0.16)
    put(bell(D5, 1.5, 0.11), 0.52)
    put(bell(Fs5, 1.5, 0.11), 1.22)
    put(bell(A5, 1.9, 0.13), 1.90)
    put(noise_sweep(0.45, 700, 2600, 0.06), 2.55)

    # hero: button highlight, tap, then the AI button nudge
    put(noise_sweep(0.5, 2600, 700, 0.09), 3.20)
    put(pop(0.3, 784.0, 0.12), 4.52)
    put(click(0.15), 4.95)
    put(pop(0.3, 880.0, 0.11), 6.18)

    # build: whoosh in, typing ticks, the three choice rows landing
    put(noise_sweep(0.5, 2400, 600, 0.09), 6.80)
    tt = 7.05
    while tt < 9.0:
        put(click(0.05 + 0.03 * np.random.rand(), 1500 + 500 * np.random.rand()), tt)
        tt += 0.085 + np.random.rand() * 0.045
    for i, f in enumerate((D5, Fs5, A5)):
        put(pop(0.26, f, 0.11), 9.00 + i * 0.17)
    put(click(0.14), 10.55)

    # AI convert: whoosh in, processing ticks, success ding
    put(noise_sweep(0.5, 2200, 700, 0.09), 11.40)
    tt = 12.30
    while tt < 14.00:
        put(click(0.035, 1200 + 900 * np.random.rand()), tt)
        tt += 0.16 + np.random.rand() * 0.1
    put(ding((D5, A5), 1.8, 0.15), 14.22)

    # play: taps on the choices, page turn, victory flourish
    put(noise_sweep(0.5, 2400, 700, 0.09), 15.40)
    put(pop(0.3, 660.0, 0.10), 15.72)
    put(click(0.17), 17.80)
    put(noise_sweep(0.42, 900, 3000, 0.09), 18.48)
    put(click(0.15), 19.60)
    put(thud(74.0, 1.2, 0.14), 20.10)
    put(flourish(D5, step=0.085, dur=2.0, amp=0.16), 20.15)
    put(bell(D6, 2.2, 0.10), 20.60)

    # library: publish click + ding, share sheet, copy toast
    put(noise_sweep(0.5, 2300, 650, 0.09), 21.80)
    put(click(0.15), 22.42)
    put(ding((A5, D6), 1.7, 0.15), 22.96)
    put(noise_sweep(0.5, 500, 1800, 0.10), 23.82)
    put(click(0.14), 25.02)
    put(bell(D6, 1.4, 0.10), 25.18)

    # end card: warm boom, CTA pop, URL chime, sparkle, resolve
    put(thud(62.0, 2.2, 0.26), 25.82)
    put(bell(D4, 2.4, 0.12), 25.86)
    put(pop(0.34, 523.25, 0.13), 27.48)
    put(ding((D5, Fs5, A5), 2.4, 0.13), 27.94)
    put(bell(A5, 1.6, 0.07), 28.42)
    put(bell(D6, 2.6, 0.08), 29.10)
    return sfx


# ---------------------------------------------------------------------------
# mix
# ---------------------------------------------------------------------------
def build(duration=TOTAL):
    n = _n(duration)
    np.random.seed(20260922)
    bed = music(n)
    fx = cues(n)
    mix = bed * 1.0 + fx * 1.15
    # gentle glue: soft-knee limiter, then trims
    mix = np.tanh(mix * 1.15) * 0.86
    # fades
    fi, fo = _n(0.45), _n(0.9)
    mix[:fi] *= np.linspace(0, 1, fi) ** 1.2
    mix[-fo:] *= np.linspace(1, 0, fo) ** 1.25
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.89
    # stereo: widen the bell/pluck content slightly, keep lows centred
    left = mix.copy()
    right = mix.copy()
    delay = _n(0.011)
    right[delay:] = right[:-delay] * 0.985
    right[:delay] = 0
    side = (right - left) * 0.16
    left = mix - side
    right = mix + side
    stereo = np.stack([left, right], axis=1)
    # safety limiter after widening (the side signal can push the true peak back up)
    stereo = np.tanh(stereo * 1.05) / np.tanh(1.05) * 0.9
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
