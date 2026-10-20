"""Chiptune music -> Assets/Resources/Audio/Music/<Name>.wav (loaded by Audio.cs as "Music/<Name>").
Each track is a few bars of four channels (lead square, arpeggio square, triangle bass, noise
drums) rendered sample-exact so the loops are seamless.
Run: python music.py"""
import os
import numpy as np
from synth import mix, tone, burst, osc, sweep, env, noise, lowpass, decay_env, save, hz, RATE, OUT

CHORDS = {
    "Am": ["A", "C", "E"], "F": ["F", "A", "C"], "G": ["G", "B", "D"], "Em": ["E", "G", "B"],
    "Dm": ["D", "F", "A"], "E": ["E", "G#", "B"], "C": ["C", "E", "G"], "Bb": ["A#", "D", "F"],
    "Gm": ["G", "A#", "D"], "A": ["A", "C#", "E"], "D": ["D", "F#", "A"], "B": ["B", "D#", "F#"],
    "Cm": ["C", "D#", "G"], "Ab": ["G#", "C", "D#"], "Fm": ["F", "G#", "C"],
}


NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def voiced(chord, octave):
    """Chord tones stacked upward from the root in `octave`, plus the root an octave up."""
    out, last = [], None
    for n in chord:
        midi = NAMES.index(n) + 12 * (octave + 1)
        while last is not None and midi <= last:
            midi += 12
        out.append(midi)
        last = midi
    out.append(out[0] + 12)
    return [f"{NAMES[m % 12]}{m // 12 - 1}" for m in out]


class Track:
    def __init__(self, bpm, bars, steps_per_bar=16):
        self.step = 60 / bpm / 4                  # one 16th note in seconds
        self.steps = bars * steps_per_bar
        self.spb = steps_per_bar
        self.buf = np.zeros(int(round(self.steps * self.step * RATE)))

    def put(self, x, step):
        i = int(round(step * self.step * RATE)) % len(self.buf)
        end = i + len(x)
        if end <= len(self.buf):
            self.buf[i:end] += x
        else:                                     # wrap around so the loop stays seamless
            k = len(self.buf) - i
            self.buf[i:] += x[:k]
            self.buf[:end - len(self.buf)] += x[k:]

    def note(self, name, step, length, wave_="square", duty=0.5, vol=0.3, vibrato=(0, 0), sustain=0.7, slide=1.0):
        dur = length * self.step
        f = hz(name)
        x = tone(f, f * slide, dur, wave_, duty, vol, vibrato=vibrato, attack=0.004, decay=dur * 0.4,
                 sustain=sustain, release=min(0.03, dur * 0.3))
        self.put(x, step)

    def melody(self, text, wave_="square", duty=0.5, vol=0.3, vibrato=(5.5, 0.012), start=0, sustain=0.7):
        """'E5:4 G5:2 -:2 ...' -> notes (length in 16ths, '-' = rest)."""
        step = start
        for token in text.split():
            name, length = token.split(":")
            length = float(length)
            if name != "-":
                self.note(name, step, length, wave_, duty, vol, vibrato, sustain)
            step += length

    def bass(self, chords, octave=2, pattern="8", vol=0.42, bar_len=16):
        """One chord per bar; pattern '8' = root eighths, 'q' = quarters, 'r' = root-fifth eighths, 'w' = whole."""
        for bar, chord in enumerate(chords):
            root = CHORDS[chord][0]
            fifth = CHORDS[chord][2]
            base = bar * bar_len
            if pattern == "w":
                self.note(f"{root}{octave}", base, bar_len, "tri", vol=vol, sustain=0.9)
            elif pattern == "q":
                for s in range(0, bar_len, 4):
                    self.note(f"{root}{octave}", base + s, 3.5, "tri", vol=vol, sustain=0.8)
            else:
                for i, s in enumerate(range(0, bar_len, 2)):
                    n = root if pattern == "8" or i % 2 == 0 else fifth
                    octv = octave + (1 if pattern == "r" and i % 4 == 3 else 0)
                    self.note(f"{n}{octv}", base + s, 1.8, "tri", vol=vol, sustain=0.8)

    def arp(self, chords, octave=4, rate=1, vol=0.13, duty=0.25, bar_len=16, up_down=False):
        for bar, chord in enumerate(chords):
            tones = voiced(CHORDS[chord], octave)
            order = tones + tones[-2:0:-1] if up_down else tones
            for i, s in enumerate(np.arange(0, bar_len, rate)):
                self.note(order[i % len(order)], bar * bar_len + s, rate * 0.9, "square", duty, vol, sustain=0.4)

    def drums(self, pattern, bars, vol=0.3):
        """pattern: 16 chars per bar, K = kick, S = snare, h = hat, T = low tom, . = rest (repeats)."""
        for bar in range(bars):
            for s, ch in enumerate(pattern):
                step = bar * len(pattern) + s
                if ch == "K":
                    self.put(kick() * vol, step)
                elif ch == "S":
                    self.put(snare() * vol, step)
                elif ch == "h":
                    self.put(hat() * vol, step)
                elif ch == "T":
                    self.put(tom() * vol, step)

    def render(self, path):
        save(self.buf, path, peak=0.8, fade=0)


def kick():
    return mix(tone(150, 45, 0.14, "sine", vol=1.2), burst(0.02, pitch=0.5, rate=120, vol=0.3))


def snare():
    return mix(burst(0.13, pitch=1.0, rate=28, vol=0.75), tone(220, 160, 0.06, "tri", vol=0.4))


def hat():
    return burst(0.035, pitch=1.0, rate=110, vol=0.3)


def tom():
    return mix(tone(110, 70, 0.16, "tri", vol=0.9), burst(0.03, pitch=0.3, rate=60, vol=0.2))


# ------------------------------------------------------------------ tracks
def title():
    t = Track(bpm=92, bars=8)
    ch = ["Am", "F", "C", "G", "Am", "F", "G", "E"]
    t.bass(ch, pattern="w", vol=0.4)
    t.arp(ch, octave=4, rate=1, vol=0.11, up_down=True)
    t.melody("E5:6 D5:2 C5:4 B4:4  A4:6 C5:2 F5:8  E5:6 D5:2 C5:4 G4:4  B4:12 -:4 "
             "E5:6 D5:2 C5:4 E5:4  F5:6 E5:2 D5:4 C5:4  D5:6 B4:2 G4:4 B4:4  G#4:12 -:4",
             "square", duty=0.5, vol=0.26)
    t.drums("K.......S.......", 8, vol=0.18)
    return t


def dungeon():
    t = Track(bpm=112, bars=8)
    ch = ["Am", "F", "G", "Em", "Am", "F", "Dm", "E"]
    t.bass(ch, pattern="r", vol=0.42)
    t.arp(ch, octave=4, rate=1, vol=0.1)
    t.melody("A4:3 C5:3 E5:2 D5:4 C5:4  A4:3 C5:3 F5:2 E5:4 C5:4  B4:3 D5:3 G5:2 F5:4 D5:4  E5:12 -:4 "
             "A5:3 G5:3 E5:2 C5:4 E5:4  F5:3 E5:3 C5:2 A4:8  D5:3 F5:3 A5:2 G5:4 F5:4  E5:4 D5:4 B4:4 G#4:4",
             "square", duty=0.5, vol=0.24)
    t.drums("K...h.h.S...h.h.", 8, vol=0.26)
    return t


def crypt():
    t = Track(bpm=78, bars=8)
    ch = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "Gm", "A"]
    t.bass(ch, octave=2, pattern="q", vol=0.42)
    t.arp(ch, octave=4, rate=2, vol=0.09, duty=0.125)
    # bell-like triangle lead, sparse and eerie
    t.melody("D5:4 -:2 F5:2 E5:4 -:4  D5:4 -:2 A#4:2 A4:8  G4:4 -:2 A#4:2 D5:4 C#5:4  A4:12 -:4 "
             "F5:4 -:2 E5:2 D5:4 -:4  F5:4 -:2 G5:2 A5:8  A#5:4 A5:2 G5:2 F5:4 E5:4  C#5:12 -:4",
             "tri", vol=0.42, sustain=0.3)
    t.melody("-:64 D6:2 -:14 -:16 A5:2 -:14 -:16", "square", duty=0.125, vol=0.06)
    t.drums("T.......h.......", 8, vol=0.2)
    return t


def caves():
    t = Track(bpm=132, bars=8)
    ch = ["Em", "C", "D", "B", "Em", "C", "Am", "B"]
    t.bass(ch, pattern="8", vol=0.45)
    t.arp(ch, octave=4, rate=1, vol=0.09, duty=0.25)
    t.melody("E5:2 E5:2 G5:2 E5:2 B5:4 A5:4  G5:2 G5:2 E5:2 G5:2 C6:8  A5:2 A5:2 F#5:2 A5:2 D6:4 C6:4  B5:12 -:4 "
             "E5:2 G5:2 B5:2 E6:2 D6:4 B5:4  C6:2 B5:2 G5:2 E5:2 G5:8  A5:2 C6:2 E6:2 C6:2 A5:4 F#5:4  D#5:12 -:4",
             "square", duty=0.25, vol=0.22)
    t.drums("K.hhS.hhK.KhS.hT", 8, vol=0.28)
    return t


def boss():
    t = Track(bpm=152, bars=8)
    ch = ["Cm", "Ab", "Bb", "G", "Cm", "Ab", "Fm", "G"]
    t.bass(ch, octave=2, pattern="r", vol=0.46)
    t.arp(ch, octave=4, rate=0.5, vol=0.08, duty=0.25)
    t.melody("C5:2 D#5:2 G5:4 F5:2 D#5:2 D5:4  C5:2 D#5:2 G#5:4 G5:2 F5:2 D#5:4  D5:2 F5:2 A#5:4 G#5:2 G5:2 F5:4  G5:8 B4:8 "
             "C6:4 A#5:2 G#5:2 G5:4 D#5:4  G#5:4 G5:2 F5:2 D#5:4 C5:4  F5:4 G#5:4 C6:4 G#5:4  B5:8 D5:4 G5:4",
             "square", duty=0.5, vol=0.23, vibrato=(7, 0.015))
    t.drums("K.hKS.hhK.hKS.SS", 8, vol=0.3)
    return t


def game_over():
    t = Track(bpm=70, bars=2)
    t.melody("E5:4 D5:4 C5:4 B4:4  A4:4 G#4:4 A4:8", "square", duty=0.5, vol=0.28, sustain=0.8)
    t.bass(["Am", "E"], octave=2, pattern="w", vol=0.4)
    buf = np.concatenate([t.buf, np.zeros(int(RATE * 0.8))])
    return buf


def floor_clear():
    t = Track(bpm=140, bars=1)
    t.melody("C5:2 E5:2 G5:2 C6:10", "square", duty=0.5, vol=0.3)
    t.melody("G4:2 C5:2 E5:2 G5:10", "square", duty=0.25, vol=0.15)
    t.bass(["C"], octave=3, pattern="w", vol=0.4)
    return np.concatenate([t.buf, np.zeros(int(RATE * 0.4))])


def main():
    folder = os.path.join(OUT, "Music")
    for name, make in (("Title", title), ("Dungeon", dungeon), ("Crypt", crypt), ("Caves", caves), ("Boss", boss)):
        make().render(os.path.join(folder, f"{name}.wav"))
    save(game_over(), os.path.join(folder, "GameOver.wav"))
    save(floor_clear(), os.path.join(folder, "FloorClear.wav"))
    print("wrote music to", folder)


if __name__ == "__main__":
    main()
