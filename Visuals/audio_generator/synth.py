"""Tiny chiptune synth shared by sfx.py and music.py: square / triangle / saw / sine / noise voices
with pitch sweeps, vibrato, envelopes and a simple low-pass, written out as 16-bit mono WAVs."""
import os
import wave
import numpy as np

RATE = 44100
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(PROJ, "Assets", "Resources", "Audio")

_rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(RATE * dur)) / RATE


def sweep(f0, f1, dur, curve="exp"):
    """Per-sample frequency going from f0 to f1."""
    n = int(RATE * dur)
    k = np.linspace(0, 1, n, endpoint=False)
    if curve == "exp" and f0 > 0 and f1 > 0:
        return f0 * (f1 / f0) ** k
    return f0 + (f1 - f0) * k


def osc(freq, wave_="square", duty=0.5, vibrato=(0, 0)):
    """freq: array of per-sample frequencies. vibrato: (rate Hz, depth as a fraction)."""
    freq = np.asarray(freq, dtype=float)
    if vibrato[1]:
        t = np.arange(len(freq)) / RATE
        freq = freq * (1 + vibrato[1] * np.sin(2 * np.pi * vibrato[0] * t))
    phase = np.cumsum(freq / RATE) % 1.0
    if wave_ == "square":
        return np.where(phase < duty, 1.0, -1.0)
    if wave_ == "tri":
        return 4 * np.abs(phase - 0.5) - 1
    if wave_ == "saw":
        return 2 * phase - 1
    if wave_ == "sine":
        return np.sin(2 * np.pi * phase)
    raise ValueError(wave_)


def noise(dur, pitch=1.0):
    """NES-style noise: random steps held for 1/pitch samples (lower pitch = rumblier)."""
    n = int(RATE * dur)
    hold = max(1, int(round(1 / max(pitch, 1e-3))))
    steps = _rng.uniform(-1, 1, n // hold + 2)
    return np.repeat(steps, hold)[:n]


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff in Hz (scalar or per-sample array)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def env(n, attack=0.005, decay=0.1, sustain=0.0, release=0.05, total=None):
    """ADSR-ish envelope over n samples (times in seconds; sustain level 0..1 held until release)."""
    a, d, r = int(attack * RATE), int(decay * RATE), int(release * RATE)
    e = np.full(n, sustain, dtype=float)
    a = min(a, n)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    d_end = min(n, a + d)
    if d_end > a:
        e[a:d_end] = np.linspace(1, sustain, d_end - a, endpoint=False)
    if r and n > r:
        e[n - r:] *= np.linspace(1, 0, r)
    return e


def decay_env(n, rate):
    """Exponential decay, `rate` = how many e-foldings per second."""
    return np.exp(-np.arange(n) / RATE * rate)


def tone(f0, f1, dur, wave_="square", duty=0.5, vol=1.0, curve="exp", vibrato=(0, 0), **env_kw):
    x = osc(sweep(f0, f1, dur, curve), wave_, duty, vibrato)
    kw = dict(attack=0.003, decay=dur, sustain=0.0, release=0.01)
    kw.update(env_kw)
    return x * env(len(x), **kw) * vol


def burst(dur, pitch=1.0, vol=1.0, cutoff=None, rate=None, **env_kw):
    x = noise(dur, pitch)
    if cutoff is not None:
        x = lowpass(x, cutoff) * 2.5
    if rate is not None:
        x = x * decay_env(len(x), rate)
    else:
        kw = dict(attack=0.002, decay=dur, sustain=0.0, release=0.01)
        kw.update(env_kw)
        x = x * env(len(x), **kw)
    return x * vol


def silence(dur):
    return np.zeros(int(RATE * dur))


def mix(*parts, at=None):
    """Sum parts; `at` = list of start times (seconds), default all at 0."""
    at = at or [0] * len(parts)
    n = max(int(s * RATE) + len(p) for p, s in zip(parts, at))
    out = np.zeros(n)
    for p, s in zip(parts, at):
        i = int(s * RATE)
        out[i:i + len(p)] += p
    return out


def seq(*parts, gap=0.0):
    pieces = []
    for p in parts:
        pieces.append(p)
        if gap:
            pieces.append(silence(gap))
    return np.concatenate(pieces)


def save(x, path, peak=0.85, fade=0.004):
    x = np.asarray(x, dtype=float)
    m = np.max(np.abs(x)) or 1.0
    x = x / m * peak
    f = int(fade * RATE)
    if f and len(x) > 2 * f:
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name):
    """'A4' -> 440, 'C#3' -> ..."""
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[pitch] + (octave - 4) * 12 - 9) / 12)
