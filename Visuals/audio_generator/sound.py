"""Realistic sound-effect synthesis (no chiptune beeps): filtered noise for air and debris, modal
synthesis (banks of decaying resonances) for ceramic / bone / wood / metal / stone impacts,
Karplus-Strong for strings, a formant voice model for creature voices, and a small room reverb.
Used by sfx.py."""
import math
import numpy as np

RATE = 44100
rng = np.random.default_rng(11)


def n(sec):
    return int(round(RATE * sec))


def t_axis(sec):
    return np.arange(n(sec)) / RATE


def noise(sec):
    return rng.uniform(-1.0, 1.0, n(sec))


def pad(x, sec):
    """Silence before x."""
    return np.concatenate([np.zeros(n(sec)), x])


def mix(*parts, at=None):
    at = at or [0.0] * len(parts)
    total = max(n(s) + len(p) for p, s in zip(parts, at))
    out = np.zeros(total)
    for p, s in zip(parts, at):
        i = n(s)
        out[i:i + len(p)] += p
    return out


def curve(points, sec):
    """Piecewise-linear control curve: points = [(time, value), ...] -> per-sample array."""
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    return np.interp(t_axis(sec), ts, vs)


def env_ar(sec, attack, release_shape=4.0, hold=0.0):
    """Fast rise then exponential-ish fall over the rest."""
    t = t_axis(sec)
    e = np.where(t < attack, t / max(attack, 1e-4), 1.0)
    fall = np.clip((t - attack - hold) / max(sec - attack - hold, 1e-4), 0, 1)
    return e * (1 - fall) ** release_shape


def decay(sec, rate):
    return np.exp(-t_axis(sec) * rate)


# ---------------------------------------------------------------- filters (RBJ biquads, per-sample params allowed)
def _biquad(x, b0, b1, b2, a1, a2):
    xs = np.asarray(x, dtype=float).tolist()          # plain lists: much faster to index in a loop
    y = [0.0] * len(xs)
    x1 = x2 = y1 = y2 = 0.0
    if np.isscalar(b0):
        for i, xi in enumerate(xs):
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, xi, y1, yi
            y[i] = yi
    else:
        B0, B1, B2, A1, A2 = (np.asarray(v, dtype=float).tolist() for v in (b0, b1, b2, a1, a2))
        for i, xi in enumerate(xs):
            yi = B0[i] * xi + B1[i] * x1 + B2[i] * x2 - A1[i] * y1 - A2[i] * y2
            x2, x1, y2, y1 = x1, xi, y1, yi
            y[i] = yi
    return np.array(y)


def _coeffs(kind, f, q):
    f = np.clip(np.asarray(f, dtype=float), 20, RATE * 0.45)
    w = 2 * np.pi * f / RATE
    alpha = np.sin(w) / (2 * q)
    cw = np.cos(w)
    if kind == "lp":
        b0, b1, b2 = (1 - cw) / 2, 1 - cw, (1 - cw) / 2
    elif kind == "hp":
        b0, b1, b2 = (1 + cw) / 2, -(1 + cw), (1 + cw) / 2
    else:  # band-pass, 0 dB peak
        b0, b1, b2 = alpha, 0 * cw, -alpha
    a0 = 1 + alpha
    return b0 / a0, b1 / a0, b2 / a0, (-2 * cw) / a0, (1 - alpha) / a0


def filt(x, kind, f, q=0.707):
    """kind: lp / hp / bp. f may be a number or a per-sample array (a sweep)."""
    if np.ndim(f) == 0:
        b0, b1, b2, a1, a2 = (float(v) for v in _coeffs(kind, f, q))
        return _biquad(x, b0, b1, b2, a1, a2)
    f = np.asarray(f)[:len(x)]
    if len(f) < len(x):
        f = np.concatenate([f, np.full(len(x) - len(f), f[-1])])
    return _biquad(x, *_coeffs(kind, f, q))


def lp(x, f, q=0.707):
    return filt(x, "lp", f, q)


def hp(x, f, q=0.707):
    return filt(x, "hp", f, q)


def bp(x, f, q=1.0):
    return filt(x, "bp", f, q)


# ---------------------------------------------------------------- impacts
def modal(freqs, decays, amps, sec, jitter=0.0):
    """A struck object: a bank of exponentially decaying sine resonances."""
    t = t_axis(sec)
    out = np.zeros_like(t)
    for f, d, a in zip(freqs, decays, amps):
        f = f * (1 + rng.uniform(-jitter, jitter))
        out += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t * d)
    return out


def click(sec=0.004, hi=3000):
    """The sharp contact transient at the start of a hit."""
    return hp(noise(sec), hi) * decay(sec, 900)


def thud(sec=0.25, f=90, weight=1.0):
    """Something heavy landing: a low pitch-drop body + muffled noise."""
    t = t_axis(sec)
    pitch = f * (1 + 0.6 * np.exp(-t * 30))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / RATE) * np.exp(-t * 18)
    muffle = lp(noise(sec), 400) * np.exp(-t * 30) * 2.5
    return (body + muffle) * weight


def ceramic_shard(sec=0.08):
    """One piece of pottery skittering on stone: a short, gritty tick with just a hint of ring."""
    base = rng.uniform(1800, 4500)
    tick = bp(noise(sec), base, 5.0) * decay(sec, rng.uniform(110, 170)) * 2.5
    ring = modal([base, base * 1.59], [rng.uniform(120, 180), 220], [0.35, 0.15], sec, 0.05)
    return mix(tick, ring, click(0.003, 3000) * 0.7)


def bone_clack(sec=0.08, size=1.0):
    """Dry bone on bone / stone: hollow, woody, short."""
    base = rng.uniform(900, 1500) / size
    return mix(modal([base, base * 2.27, base * 3.9], [90, 140, 200], [1.0, 0.5, 0.25], sec, 0.05), click(0.003, 2500) * 0.8)


def wood_knock(sec=0.2, base=180):
    return mix(modal([base, base * 2.61, base * 4.4, base * 6.3], [22, 35, 55, 80], [1.0, 0.5, 0.3, 0.15], sec, 0.02),
               click(0.004, 1500) * 0.5)


def metal_clang(sec=0.6, base=620, ring=6.0):
    ratios = [1.0, 2.76, 5.40, 8.93, 13.34]
    return mix(modal([base * r for r in ratios], [ring * (1 + i * 0.7) for i in range(5)], [1.0, 0.7, 0.5, 0.3, 0.2], sec, 0.01),
               click(0.004, 4000))


def stone_crunch(sec=0.35, grains=60, low=300, high=2200):
    """Rock breaking / gravel: many tiny cracks shaped into a decaying cloud."""
    out = np.zeros(n(sec))
    for _ in range(grains):
        i = int(rng.beta(1.2, 3.5) * len(out))
        g = bp(noise(0.012), rng.uniform(low, high), 2.0) * decay(0.012, 300) * rng.uniform(0.3, 1.0)
        out[i:i + len(g)] += g[:len(out) - i]
    return out * 2.5


def scatter(make, count, span, start_amp=1.0, end_amp=0.25):
    """Many small events (shards, bones, droplets) spread over `span` seconds, fading."""
    parts, at = [], []
    for k in range(count):
        when = span * (k / count) ** 1.6 + rng.uniform(0, span / count)
        amp = start_amp + (end_amp - start_amp) * k / max(1, count - 1)
        parts.append(make() * amp * rng.uniform(0.6, 1.0))
        at.append(when)
    return mix(*parts, at=at)


# ---------------------------------------------------------------- air
def whoosh(sec, f0, f_peak, f1, q=1.4, peak_at=0.4, gain=1.0):
    """Air displaced by something swinging past: band-passed noise swelling and fading."""
    f = curve([(0, f0), (sec * peak_at, f_peak), (sec, f1)], sec)
    amp = curve([(0, 0.0), (sec * peak_at, 1.0), (sec, 0.0)], sec) ** 1.5
    air = bp(bp(noise(sec), f, q), f, q)               # two passes: a focused rush of air, not hiss
    return lp(air, 4500) * amp * 6.0 * gain


def hiss(sec, low=3000, high=9000, gain=1.0):
    return bp(hp(noise(sec), low), (low + high) / 2, 0.7) * gain


def string_pluck(freq, sec, damping=0.996, bright=0.5):
    """Karplus-Strong plucked string (bow strings, sinew)."""
    period = int(RATE / freq)
    buf = rng.uniform(-1, 1, period) * bright + (1 - bright) * lp(rng.uniform(-1, 1, period), 2000)
    buf = buf.tolist()
    out = [0.0] * n(sec)
    for i in range(len(out)):
        k = i % period
        v = buf[k]
        out[i] = v
        buf[k] = damping * 0.5 * (v + buf[(k + 1) % period])
    return np.array(out)


def bell(freq, sec, decay_rate=3.0):
    """A small bell / chime (inharmonic partials, no square waves)."""
    ratios = [1.0, 2.0, 2.4, 3.0, 4.5, 5.33]
    return modal([freq * r for r in ratios], [decay_rate * (1 + i * 0.5) for i in range(6)],
                 [1.0, 0.6, 0.4, 0.25, 0.15, 0.1], sec)


def heartbeat(sec=0.7, strength=1.0):
    """Lub-dub."""
    lub = thud(0.18, 55, 1.0)
    dub = thud(0.16, 70, 0.7)
    return mix(lub, dub, at=[0, 0.16])[:n(sec)] * strength


# ---------------------------------------------------------------- creature voices
VOWELS = {   # formant frequencies (Hz) and relative gains
    "a": ([750, 1150, 2500], [1.0, 0.5, 0.25]),
    "ah": ([700, 1220, 2600], [1.0, 0.55, 0.25]),
    "e": ([550, 1800, 2550], [1.0, 0.4, 0.3]),
    "i": ([320, 2300, 3000], [1.0, 0.3, 0.25]),
    "o": ([480, 850, 2500], [1.0, 0.45, 0.15]),
    "u": ([330, 750, 2400], [1.0, 0.35, 0.1]),
    "uh": ([600, 1050, 2400], [1.0, 0.45, 0.2]),
    "ae": ([660, 1700, 2400], [1.0, 0.5, 0.3]),
}


def voice(sec, pitch, vowels, size=1.0, rough=0.2, breath=0.1, jitter=0.02, fry=0.0, amp=None):
    """A creature's voice: a buzzing glottal source shaped by mouth resonances.
    pitch: Hz or [(t, Hz), ...]. vowels: vowel name or [(t, vowel), ...] (glides between them).
    size > 1 lowers the formants (bigger throat: orcs); < 1 raises them (goblins, kobolds).
    rough: growl (fast random amplitude flutter). fry: creaky irregular pulses (zombies).
    amp: envelope points [(t, a), ...]."""
    total = n(sec)
    t = t_axis(sec)
    p = curve(pitch, sec) if isinstance(pitch, list) else np.full(total, float(pitch))
    walk = np.cumsum(rng.normal(0, 1, total)) / math.sqrt(RATE * 0.05)
    walk = lp(walk - np.mean(walk), 8)
    p = p * (1 + jitter * walk / (np.std(walk) + 1e-9))
    if fry > 0:   # creak: slow, irregular period jumps
        p = p * (1 - fry * 0.5 * (lp(rng.uniform(-1, 1, total), 25) > 0.05))
    phase = np.cumsum(p / RATE) % 1.0
    src = (2 * phase - 1)
    src = lp(src, 3500) * (1 - 0.3 * phase)                          # softer glottal pulse
    if rough > 0:
        flutter = lp(rng.uniform(-1, 1, total), 70)
        src *= 1 + rough * 6 * flutter
    src += lp(noise(sec), 6000) * breath

    # vowel glide -> per-sample formant tracks
    if isinstance(vowels, str):
        vowels = [(0, vowels)]
    times = [v[0] for v in vowels] + [sec]
    fs = [np.zeros(total) for _ in range(3)]
    gs = [0.0, 0.0, 0.0]
    for k in range(3):
        pts_f = [(vt, VOWELS[v][0][k] / size) for vt, v in vowels] + [(sec, VOWELS[vowels[-1][1]][0][k] / size)]
        fs[k] = curve(pts_f, sec)
        gs[k] = VOWELS[vowels[0][1]][1][k]
    out = sum(bp(src, fs[k], q=[4.0, 6.0, 8.0][k]) * gs[k] for k in range(3))
    if amp:
        out = out * curve(amp, sec)
    else:
        out = out * env_ar(sec, 0.02, 1.2)
    return out * 3.0


# ---------------------------------------------------------------- space
def reverb(x, size=0.6, wet=0.22, damp=3000):
    """Stone room ambience: convolve with a decaying, darkened noise tail."""
    ir_len = n(size)
    ir = rng.normal(0, 1, ir_len) * np.exp(-np.arange(ir_len) / RATE * (6.5 / size))
    ir = lp(ir, damp)
    ir[:n(0.012)] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    m = len(x) + ir_len
    size_fft = 1 << (m - 1).bit_length()
    tail = np.fft.irfft(np.fft.rfft(x, size_fft) * np.fft.rfft(ir, size_fft), size_fft)[:m]
    dry = np.concatenate([x, np.zeros(ir_len)])
    return dry + tail * wet * 2.0


def trim(x, threshold=0.002):
    """Cut trailing near-silence."""
    m = np.max(np.abs(x)) or 1.0
    idx = np.where(np.abs(x) > threshold * m)[0]
    return x[:idx[-1] + 1] if len(idx) else x
