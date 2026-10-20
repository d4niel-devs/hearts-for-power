"""Sound effects -> Assets/Resources/Audio/Sfx/<Name>.wav (loaded by Audio.cs as "Sfx/<Name>").
Every sound is modelled on the real thing (see sound.py): blades cut air, pots shatter into
ceramic shards, bones clatter, doors are heavy wood and iron, monsters have throats and voices -
all with a little stone-dungeon reverb. Run: python sfx.py"""
import os
import numpy as np
from sound import (RATE, n, noise, mix, pad, curve, env_ar, decay, lp, hp, bp, modal, click, thud,
                   ceramic_shard, bone_clack, wood_knock, metal_clang, stone_crunch, scatter, whoosh,
                   hiss, string_pluck, bell, heartbeat, voice, reverb, trim, t_axis, rng)
from synth import save, OUT

SFX = {}


def sfx(fn):
    SFX[fn.__name__] = fn
    return fn


def room(x, size=0.5, wet=0.18):
    return trim(reverb(x, size, wet))


# ================================================================== UI (soft wood / stone clicks)
@sfx
def UiMove():
    return wood_knock(0.06, 900) * 0.5


@sfx
def UiSelect():
    return room(mix(wood_knock(0.12, 420), bell(1320, 0.5, 6) * 0.15, at=[0, 0.01]), 0.4, 0.15)


@sfx
def UiBack():
    return room(wood_knock(0.12, 260), 0.4, 0.12)


# ================================================================== the knight
@sfx
def SwordSwing():
    # a blade cutting air: a fast band-passed whoosh that rises and falls, plus the faintest steel ring
    # fast "fwoosh": the band of air rushes up in pitch as the blade passes closest, then falls
    air = whoosh(0.24, 350, 1700, 500, q=2.0, peak_at=0.42)
    body = whoosh(0.24, 150, 450, 200, q=1.2, peak_at=0.45, gain=0.7)
    return room(mix(air, body), 0.35, 0.08)


@sfx
def SwordHit():
    # a blade slicing through: a fast rising swish into a sharp "shhk", with a little steel ring
    swish = bp(bp(noise(0.09), curve([(0, 1800), (0.09, 6500)], 0.09), 1.6), curve([(0, 1800), (0.09, 6500)], 0.09), 1.6)         * curve([(0, 0), (0.07, 1), (0.09, 0.6)], 0.09) * 5
    cut = hp(noise(0.14), 3000) * env_ar(0.14, 0.003, 3.0) * 1.4
    shing = modal([2950, 4420, 6180, 7900], [16, 22, 30, 40], [0.35, 0.3, 0.2, 0.12], 0.4, 0.01)
    flesh = bp(noise(0.05), 900, 1.2) * decay(0.05, 90) * 0.5
    return room(mix(swish, cut, shing, flesh, at=[0, 0.075, 0.075, 0.08]), 0.3, 0.08)


@sfx
def MonsterHurt():
    return mix(thud(0.12, 140, 0.7), lp(noise(0.04), 1200) * decay(0.04, 90) * 1.5)


@sfx
def PlayerHurt():
    grunt = voice(0.22, [(0, 175), (0.22, 130)], [(0, "uh"), (0.2, "u")], size=1.0, rough=0.15, breath=0.25,
                  amp=[(0, 0), (0.02, 1), (0.22, 0)])
    armor = metal_clang(0.3, 780, 18) * 0.25
    return room(mix(thud(0.2, 90, 0.9), armor, grunt * 0.9, at=[0, 0, 0.01]), 0.4, 0.15)


@sfx
def PlayerDeath():
    groan = voice(1.1, [(0, 170), (0.3, 150), (1.1, 95)], [(0, "ah"), (0.6, "uh"), (1.0, "u")], rough=0.25,
                  breath=0.3, amp=[(0, 0), (0.05, 1), (0.6, 0.7), (1.1, 0)])
    fall = mix(*[metal_clang(0.5, rng.uniform(500, 900), 14) * 0.3 for _ in range(3)], thud(0.4, 70, 1.4),
               at=[0.0, 0.07, 0.15, 0.05])
    return room(mix(groan, fall, at=[0, 0.9]), 0.8, 0.22)


@sfx
def Dash():
    return room(mix(whoosh(0.22, 250, 1400, 400, q=0.8, peak_at=0.3), whoosh(0.22, 900, 3200, 1200, q=1.5, peak_at=0.3, gain=0.4),
                    lp(noise(0.08), 900) * decay(0.08, 50) * 0.6), 0.3, 0.08)


@sfx
def HeartPickup():
    # a soft, warm heartbeat and a gentle chime
    return room(mix(heartbeat(0.5, 0.9), bell(880, 0.8, 5) * 0.18, bell(1320, 0.7, 6) * 0.1, at=[0, 0.02, 0.12]), 0.5, 0.18)


@sfx
def ContainerGain():
    chimes = mix(*[bell(f, 1.2, 3.5) * 0.18 for f in (523, 659, 784, 1047)], at=[0.0, 0.09, 0.18, 0.27])
    return room(mix(heartbeat(0.7, 1.2), chimes, at=[0, 0.05]), 0.9, 0.25)


@sfx
def Purchase():
    # paying for power: a deep heartbeat, then a shimmering magical chime
    shimmer = mix(*[bell(f, 1.0, 4) * 0.12 for f in (880, 1175, 1568)], at=[0, 0.05, 0.1])
    sparkle = hp(noise(0.6), 6000) * decay(0.6, 6) * 0.15
    return room(mix(heartbeat(0.6, 1.0), shimmer, sparkle, at=[0, 0.12, 0.12]), 0.9, 0.25)


@sfx
def Sacrifice():
    # giving up a heart container: two heavy, slow heartbeats and a low groan of the dungeon
    rumble = lp(noise(1.2), 120) * env_ar(1.2, 0.2, 2) * 3.0
    return room(mix(heartbeat(0.8, 1.3), heartbeat(0.8, 1.1), rumble * 0.5, at=[0, 0.7, 0]), 1.0, 0.25)


@sfx
def Full():
    return wood_knock(0.08, 520) * 0.5


# ================================================================== spells
@sfx
def SpellMagicBolt():
    zip_ = bp(noise(0.25), curve([(0, 1200), (0.25, 5200)], 0.25), 3.0) * env_ar(0.25, 0.02, 2) * 2.5
    shimmer = mix(*[bell(f, 0.4, 9) * 0.08 for f in (1760, 2217, 2637)])
    return room(mix(zip_, shimmer), 0.4, 0.15)


@sfx
def SpellFireball():
    # a burst of flame: a whoomp of low air plus roaring, crackling fire
    whoomp = lp(noise(0.6), curve([(0, 300), (0.15, 1800), (0.6, 500)], 0.6)) * env_ar(0.6, 0.06, 2.0) * 3.0
    crackle = stone_crunch(0.6, 40, 1500, 5000) * 0.25
    return room(mix(whoomp, crackle), 0.5, 0.15)


@sfx
def SpellIceShards():
    tinkle = scatter(lambda: modal([rng.uniform(3000, 6500)] * 1, [30], [1.0], 0.25), 7, 0.25, 0.5, 0.25)
    air = whoosh(0.3, 2000, 6000, 3000, q=1.0, gain=0.5)
    crack = hp(noise(0.03), 3000) * decay(0.03, 150) * 0.8
    return room(mix(crack, air, tinkle), 0.5, 0.2)


@sfx
def SpellLightning():
    crack = hp(noise(0.12), 800) * decay(0.12, 35) * 1.5
    sizzle = hp(noise(0.5), 4000) * decay(0.5, 6) * (rng.random(n(0.5)) > 0.75) * 1.2
    rumble = lp(noise(1.4), curve([(0, 600), (1.4, 80)], 1.4)) * env_ar(1.4, 0.05, 1.5) * 4.0
    return room(mix(crack, sizzle, rumble * 0.6), 1.0, 0.25)


@sfx
def BombPlace():
    return mix(metal_clang(0.25, 420, 20) * 0.4, thud(0.15, 120, 0.6))


@sfx
def BombFuse():
    # a lit fuse: hissing sparks with little crackles
    sputter = 0.6 + 0.4 * lp(rng.uniform(-1, 1, n(0.8)), 30) * 6
    return hiss(0.8, 3000, 9000, 1.2) * np.clip(sputter, 0, 1.5) + stone_crunch(0.8, 25, 3000, 7000) * 0.3


@sfx
def Explosion():
    boom = lp(noise(1.6), curve([(0, 4000), (0.08, 1200), (1.6, 90)], 1.6)) * env_ar(1.6, 0.005, 2.2) * 4.0
    sub = thud(0.8, 45, 2.0)
    debris = pad(stone_crunch(0.9, 70, 400, 3000) * 0.6, 0.15)
    return room(mix(boom, sub, debris), 1.2, 0.3)


@sfx
def EnemyShot():
    # something thrown: a short whistle of air
    return whoosh(0.18, 600, 1800, 800, q=1.6, peak_at=0.25, gain=0.8)


@sfx
def ProjectileHit():
    return mix(click(0.004, 2000), lp(noise(0.05), 1500) * decay(0.05, 80) * 1.2)


@sfx
def SpiritShot():
    # a ghostly skull-fire spit: breathy whoosh with a hollow moan in it
    moan = voice(0.35, [(0, 300), (0.35, 240)], "o", size=0.8, rough=0.0, breath=0.6, jitter=0.04,
                 amp=[(0, 0), (0.05, 1), (0.35, 0)])
    return room(mix(whoosh(0.35, 400, 1600, 700, q=1.0, gain=0.7), moan * 0.5), 0.6, 0.25)


@sfx
def SpiritImmune():
    # a hit that does nothing: a hollow ghostly ring
    return room(mix(click(0.004, 3000) * 0.4, modal([620, 1240, 1890], [6, 9, 12], [0.4, 0.2, 0.1], 0.6)), 0.7, 0.3)


# ================================================================== the room
@sfx
def DoorSlam():
    # a heavy iron-banded door slamming into its stone frame
    wood = mix(wood_knock(0.6, 85) * 1.2, wood_knock(0.5, 140) * 0.5)
    iron = metal_clang(0.6, 340, 9) * 0.25
    return room(mix(wood, thud(0.5, 60, 1.6), iron, lp(noise(0.08), 600) * decay(0.08, 50)), 1.0, 0.3)


@sfx
def DoorOpen():
    # old hinges creaking, then the door bumping open
    sec = 0.7
    rate = curve([(0, 28), (0.3, 55), (0.7, 22)], sec) * (1 + 0.25 * lp(rng.uniform(-1, 1, n(sec)), 15) * 8)
    phase = np.cumsum(rate / RATE)
    pulses = (np.diff(np.floor(phase), prepend=0) > 0).astype(float)        # stick-slip
    creak = bp(pulses, curve([(0, 900), (0.35, 1500), (0.7, 1100)], sec), 6) * 6
    creak *= curve([(0, 0), (0.05, 1), (0.6, 0.8), (0.7, 0)], sec)
    return room(mix(creak, wood_knock(0.3, 120) * 0.5, at=[0, 0.6]), 0.8, 0.25)


@sfx
def RoomClear():
    # the doors' bolts sliding back, and a soft chime of relief
    bolts = mix(metal_clang(0.25, 900, 25) * 0.3, metal_clang(0.25, 1100, 25) * 0.25, at=[0, 0.12])
    chime = mix(*[bell(f, 1.2, 3) * 0.12 for f in (659, 784, 988)], at=[0, 0.08, 0.16])
    return room(mix(bolts, chime, at=[0, 0.15]), 0.9, 0.25)


def crackle(sec, density, start_rate, lo=1500):
    """Brittle material fracturing: single-sample cracks (not filtered noise grains, which sound wet),
    densest at the start and thinning out."""
    out = np.zeros(n(sec))
    t = 0.0
    while t < sec:
        i = n(t)
        if i < len(out):
            out[i] += rng.uniform(0.4, 1.0) * rng.choice((-1, 1))
        t += rng.exponential(1.0 / (density * np.exp(-t * start_rate) + 1e-3))
    return hp(out, lo) * 1.5


def tink(freq=None):
    """One fragment landing: a sharp click and a short, bright, glassy ring."""
    f = freq or rng.uniform(3200, 8500)
    ring = modal([f, f * rng.uniform(1.35, 1.7)], [rng.uniform(28, 55), rng.uniform(45, 80)], [1.0, 0.5], 0.18, 0.02)
    return mix(click(0.002, 3500) * 1.2, ring * 0.6)


@sfx
def PotBreak():
    # ceramic smashing on stone (like a plate smash): a crisp crack, a burst of shattering,
    # then the pieces tinkling and settling
    crack = mix(hp(noise(0.012), 2000) * decay(0.012, 300) * 2.0,
                modal([1650, 2780, 3900, 5300], [55, 70, 90, 110], [0.5, 0.45, 0.35, 0.25], 0.12, 0.02))
    shatter = crackle(0.35, 2600, 14, 1800)
    fragments = pad(scatter(lambda: tink(), 34, 1.3, 0.85, 0.12), 0.03)
    settle = pad(scatter(lambda: tink(rng.uniform(4000, 9000)) * 0.6, 8, 0.6, 0.3, 0.08), 0.9)
    grit = hp(noise(0.5), 4500) * decay(0.5, 9) * 0.12
    knock = hp(wood_knock(0.06, 620), 400) * 0.35                     # the hard clack of the pot hitting
    return room(mix(knock, crack, shatter, fragments, settle, grit), 0.4, 0.1)


@sfx
def RockBreak():
    crack = hp(noise(0.01), 1500) * decay(0.01, 400) * 1.5
    return room(mix(crack, thud(0.4, 75, 1.4), stone_crunch(0.6, 80, 250, 2500),
                    pad(scatter(lambda: bone_clack(0.06, 1.6) * 0.5, 10, 0.4), 0.05)), 0.8, 0.22)


@sfx
def Spike():
    # iron spikes shooting up out of the floor: a scraping schwing and a clank
    scrape = bp(noise(0.12), curve([(0, 3000), (0.12, 6000)], 0.12), 2.0) * env_ar(0.12, 0.01, 1.5) * 1.5
    return room(mix(scrape, metal_clang(0.35, 1400, 16) * 0.35, at=[0, 0.05]), 0.5, 0.15)


@sfx
def Stairs():
    # footsteps going down stone stairs into the dark (more echo with each step)
    steps = [room(mix(thud(0.12, 140 - i * 8, 0.8), lp(noise(0.05), 1600) * decay(0.05, 60) * 0.6), 0.4 + i * 0.12, 0.1 + i * 0.05)
             for i in range(5)]
    return mix(*[s * (1 - i * 0.12) for i, s in enumerate(steps)], at=[i * 0.26 for i in range(5)])


@sfx
def Emerge():
    # earth crumbling as something claws up out of the ground
    rumble = lp(noise(0.6), 220) * env_ar(0.6, 0.15, 1.5) * 3
    return room(mix(rumble, stone_crunch(0.6, 70, 200, 1500) * 0.7), 0.5, 0.15)


@sfx
def MonsterDie():
    return room(mix(thud(0.25, 80, 1.0), lp(noise(0.2), 900) * decay(0.2, 18) * 1.2), 0.5, 0.15)


# ================================================================== monsters
def splat(sec=0.25, size=1.0):
    """Something wet hitting stone."""
    body = lp(noise(sec), 1200 / size) * decay(sec, 25 * size) * 2.5
    drops = scatter(lambda: bubble(rng.uniform(500, 1400) / size, 0.05), 5, sec * 0.8, 0.4, 0.1)
    return mix(body, thud(sec, 70 / size, 0.6), drops)


def bubble(freq, sec):
    """A droplet / bubble: a sine that chirps upward (what real bubbles do)."""
    t = t_axis(sec)
    f = freq * (1 + 2.5 * t / sec)
    return np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 40)


@sfx
def SlimeHop():
    # a wet squelch as the slime pushes off
    squelch = bp(noise(0.18), curve([(0, 400), (0.18, 1400)], 0.18), 3) * env_ar(0.18, 0.03, 1.5) * 2.5
    return mix(squelch, bubble(300, 0.12) * 0.4)


@sfx
def SlimeLand():
    return splat(0.2, 1.0) * 0.8


@sfx
def SlimeDie():
    return room(mix(splat(0.4, 0.9), scatter(lambda: bubble(rng.uniform(400, 1200), 0.08), 8, 0.4, 0.5, 0.1)), 0.5, 0.15)


@sfx
def GoblinCackle():
    # a nasty, nasal little "heh-heh-heh-heh"
    parts, at = [], []
    for k in range(5):
        p0 = 520 - k * 18 + rng.uniform(-20, 20)
        parts.append(voice(0.11, [(0, p0), (0.11, p0 * 0.8)], [(0, "e"), (0.08, "i")], size=0.62, rough=0.35, breath=0.35,
                           jitter=0.05, amp=[(0, 0), (0.012, 1), (0.06, 0.6), (0.11, 0)]))
        at.append(k * 0.115)
    return room(mix(*parts, at=at), 0.4, 0.15)


@sfx
def GoblinDie():
    # a shrill, squealing "eeyaagh"
    return room(voice(0.5, [(0, 600), (0.1, 760), (0.5, 330)], [(0, "i"), (0.12, "ae"), (0.45, "a")], size=0.62, rough=0.45,
                      breath=0.3, jitter=0.06, amp=[(0, 0), (0.02, 1), (0.3, 0.8), (0.5, 0)]), 0.5, 0.18)


@sfx
def ZombieGroan():
    # a slow, rotten "uuuurrrrgh" with a creaky, broken throat
    return room(voice(1.1, [(0, 92), (0.5, 100), (1.1, 80)], [(0, "uh"), (0.5, "o"), (1.0, "u")], size=1.1, rough=0.35,
                      breath=0.25, jitter=0.06, fry=0.6, amp=[(0, 0), (0.25, 1), (0.8, 0.8), (1.1, 0)]), 0.7, 0.2)


@sfx
def ZombieDie():
    gurgle = voice(0.9, [(0, 110), (0.9, 60)], [(0, "uh"), (0.9, "u")], size=1.1, rough=0.6, breath=0.3, fry=0.8,
                   amp=[(0, 0), (0.05, 1), (0.9, 0)])
    wet = scatter(lambda: bubble(rng.uniform(150, 400), 0.07), 10, 0.7, 0.3, 0.1)
    return room(mix(gurgle, wet, thud(0.3, 70, 0.8), at=[0, 0.1, 0.7]), 0.7, 0.2)


@sfx
def KoboldYip():
    # small, dog-like yips
    yip = lambda p: voice(0.09, [(0, p), (0.09, p * 1.25)], [(0, "a"), (0.09, "i")], size=0.7, rough=0.2, breath=0.2,
                          amp=[(0, 0), (0.008, 1), (0.09, 0)])
    return room(mix(yip(620), yip(700), at=[0, 0.13]), 0.4, 0.15)


@sfx
def KoboldHiss():
    # a reptilian hiss through bared teeth
    return hiss(0.45, 3500, 9000, 1.3) * env_ar(0.45, 0.06, 1.2) + bp(noise(0.45), 2500, 4) * env_ar(0.45, 0.06, 1.2) * 0.6


@sfx
def KoboldDie():
    return room(voice(0.35, [(0, 760), (0.35, 360)], [(0, "i"), (0.3, "a")], size=0.7, rough=0.3, breath=0.25,
                      amp=[(0, 0), (0.01, 1), (0.35, 0)]), 0.4, 0.15)


@sfx
def SkeletonRattle():
    # dry bones clattering together
    return scatter(lambda: bone_clack(0.06, 1.0), 9, 0.28, 0.9, 0.5)


@sfx
def BowTwang():
    # a bowstring snapping forward, and the arrow's whistle
    string = string_pluck(150, 0.4, 0.993, 0.7) * decay(0.4, 6)
    return room(mix(string, bone_clack(0.05, 1.3) * 0.4, whoosh(0.2, 1500, 3500, 2000, q=2, gain=0.35), at=[0, 0, 0.02]), 0.4, 0.12)


@sfx
def SkeletonDie():
    # the skeleton collapses into a heap of bones
    return room(scatter(lambda: bone_clack(0.08, rng.uniform(0.8, 1.4)), 16, 0.6, 1.0, 0.3), 0.6, 0.2)


@sfx
def OrcGrunt():
    # a deep, guttural "hrrnh"
    return room(voice(0.32, [(0, 105), (0.32, 88)], [(0, "uh"), (0.3, "o")], size=1.35, rough=0.5, breath=0.35, jitter=0.04,
                      fry=0.3, amp=[(0, 0), (0.03, 1), (0.32, 0)]), 0.5, 0.15)


@sfx
def OrcShout():
    # a big war cry: "RRAAAGH"
    cry = voice(0.75, [(0, 125), (0.15, 165), (0.75, 120)], [(0, "uh"), (0.12, "ah"), (0.65, "o")], size=1.3, rough=0.55,
                breath=0.3, jitter=0.03, amp=[(0, 0), (0.06, 1), (0.6, 0.9), (0.75, 0)])
    return room(cry, 0.7, 0.2)


@sfx
def OrcDie():
    return room(voice(1.0, [(0, 150), (0.3, 120), (1.0, 65)], [(0, "ah"), (0.5, "uh"), (0.95, "u")], size=1.35, rough=0.6,
                      breath=0.3, fry=0.5, amp=[(0, 0), (0.04, 1), (1.0, 0)]), 0.8, 0.22)


@sfx
def BatFlap():
    # leathery wings beating
    flap = lambda: lp(noise(0.035), 1100) * env_ar(0.035, 0.008, 2) * 2.5
    return mix(*[flap() for _ in range(4)], at=[i * 0.07 for i in range(4)])


@sfx
def BatSqueak():
    t = t_axis(0.09)
    f = curve([(0, 4200), (0.04, 5200), (0.09, 3800)], 0.09)
    return np.sin(2 * np.pi * np.cumsum(f) / RATE) * env_ar(0.09, 0.005, 1.5) * 0.6 + hp(noise(0.09), 5000) * env_ar(0.09, 0.005, 2) * 0.1


@sfx
def BatDie():
    f = curve([(0, 5000), (0.25, 2200)], 0.25)
    squeal = np.sin(2 * np.pi * np.cumsum(f) / RATE) * env_ar(0.25, 0.005, 1.2) * 0.6
    return room(mix(squeal, BatFlap() * 0.5), 0.4, 0.12)


@sfx
def GhostWoo():
    # a hollow, breathy "wooooo"
    moan = voice(1.0, [(0, 260), (0.5, 330), (1.0, 280)], "u", size=0.9, rough=0.0, breath=0.7, jitter=0.03,
                 amp=[(0, 0), (0.35, 1), (0.8, 0.8), (1.0, 0)])
    air = bp(noise(1.0), 700, 2) * curve([(0, 0), (0.4, 1), (1.0, 0)], 1.0) * 0.6
    return room(mix(moan, air), 1.2, 0.35)


@sfx
def GhostDie():
    wail = voice(1.0, [(0, 420), (1.0, 180)], [(0, "o"), (1.0, "u")], size=0.85, rough=0.0, breath=0.8,
                 amp=[(0, 0), (0.05, 1), (1.0, 0)])
    return room(mix(wail, whoosh(1.0, 2000, 800, 300, q=1.0, peak_at=0.2, gain=0.5)), 1.3, 0.4)


@sfx
def MimicChomp():
    # ceramic jaws snapping shut
    jaw = lambda: mix(modal([900, 1600, 2700], [60, 90, 120], [1.0, 0.5, 0.3], 0.1), click(0.003, 2500),
                      lp(noise(0.04), 1500) * decay(0.04, 80))
    return mix(jaw(), jaw() * 0.8, at=[0, 0.14])


@sfx
def MimicReveal():
    snarl = voice(0.5, [(0, 140), (0.5, 120)], [(0, "a"), (0.4, "uh")], size=1.1, rough=0.7, breath=0.4,
                  amp=[(0, 0), (0.05, 1), (0.5, 0)])
    return mix(PotBreak(), snarl * 0.8, MimicChomp(), at=[0, 0.08, 0.35])


@sfx
def MimicDie():
    return room(mix(scatter(lambda: ceramic_shard(0.08), 16, 0.4, 0.8, 0.2), thud(0.3, 90, 0.8),
                    stone_crunch(0.4, 50, 1500, 6000) * 0.4), 0.6, 0.18)


@sfx
def NecroChant():
    # low murmured incantation from more than one throat, with a whisper over it
    voices = [voice(0.9, [(0, p), (0.9, p * 0.97)], [(0, "o"), (0.3, "ah"), (0.6, "u")], size=1.15, rough=0.1, breath=0.4,
                    jitter=0.03, amp=[(0, 0), (0.1, 1), (0.8, 0.8), (0.9, 0)]) for p in (98, 147)]
    whisper = bp(noise(0.9), 3000, 1.5) * curve([(0, 0), (0.2, 1), (0.9, 0)], 0.9) * 0.4
    return room(mix(*voices, whisper), 1.0, 0.35)


@sfx
def NecroRaise():
    # the ground cracks and something spectral rises with a moan
    moan = voice(0.8, [(0, 200), (0.8, 300)], [(0, "u"), (0.8, "o")], size=0.9, breath=0.7, rough=0.0,
                 amp=[(0, 0), (0.3, 1), (0.8, 0)])
    return room(mix(Emerge(), moan * 0.6, at=[0, 0.15]), 0.9, 0.3)


@sfx
def NecroDie():
    scream = voice(0.9, [(0, 260), (0.2, 330), (0.9, 140)], [(0, "a"), (0.6, "o")], size=1.0, rough=0.4, breath=0.4,
                   amp=[(0, 0), (0.03, 1), (0.9, 0)])
    return room(mix(scream, SkeletonDie() * 0.6, at=[0, 0.4]), 0.9, 0.3)


# ================================================================== King Slime
@sfx
def KingSlimeRoar():
    # an enormous wet gurgling bellow
    bellow = voice(1.4, [(0, 70), (0.4, 85), (1.4, 60)], [(0, "o"), (0.5, "ah"), (1.2, "u")], size=1.8, rough=0.5,
                   breath=0.3, fry=0.4, amp=[(0, 0), (0.15, 1), (1.1, 0.8), (1.4, 0)])
    bubbles = scatter(lambda: bubble(rng.uniform(150, 500), 0.12), 18, 1.2, 0.5, 0.2)
    return room(mix(bellow, bubbles), 1.2, 0.3)


@sfx
def KingSlimeWobble():
    t = t_axis(0.6)
    wobble = lp(noise(0.6), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * env_ar(0.6, 0.1, 1.5) * 3
    return mix(wobble, bubble(120, 0.3) * 0.4)


@sfx
def KingSlimeSlam():
    return room(mix(splat(0.6, 2.2) * 1.6, thud(0.6, 40, 2.0)), 1.0, 0.28)


@sfx
def KingSlimeSplash():
    return room(scatter(lambda: mix(bubble(rng.uniform(400, 1000), 0.08), lp(noise(0.05), 2000) * decay(0.05, 70)), 12, 0.4), 0.7, 0.2)


@sfx
def KingSlimeDie():
    gurgle = voice(2.0, [(0, 90), (2.0, 40)], [(0, "o"), (2.0, "u")], size=1.8, rough=0.7, breath=0.3, fry=0.7,
                   amp=[(0, 0), (0.1, 1), (2.0, 0)])
    return room(mix(gurgle, scatter(lambda: bubble(rng.uniform(100, 600), 0.15), 30, 1.8, 0.6, 0.1), splat(0.8, 2.0)), 1.4, 0.3)


# ================================================================== Ancient Lich
@sfx
def LichRoar():
    # a ghastly scream of many voices, with whispering underneath
    screams = [voice(1.5, [(0, p), (0.3, p * 1.25), (1.5, p * 0.8)], [(0, "a"), (0.6, "o"), (1.3, "u")], size=0.95,
                     rough=0.3, breath=0.6, jitter=0.05, amp=[(0, 0), (0.15, 1), (1.2, 0.7), (1.5, 0)]) for p in (180, 270, 360)]
    whisper = bp(noise(1.5), 2800, 1.2) * curve([(0, 0), (0.2, 1), (1.5, 0)], 1.5) * 0.5
    return room(mix(*[s * 0.6 for s in screams], whisper), 1.5, 0.4)


@sfx
def LichWhisper():
    return room(bp(noise(0.8), curve([(0, 1800), (0.8, 3400)], 0.8), 1.5) * curve([(0, 0), (0.3, 1), (0.8, 0)], 0.8) * 1.5, 1.0, 0.35)


@sfx
def LichCast():
    whoosh_ = whoosh(0.6, 300, 1500, 500, q=0.9, peak_at=0.25)
    crackle = stone_crunch(0.5, 30, 2000, 6000) * 0.35
    return room(mix(whoosh_, crackle, heartbeat(0.4, 0.5)), 1.0, 0.3)


@sfx
def LichBones():
    return room(scatter(lambda: bone_clack(0.07, 1.0), 12, 0.4, 0.8, 0.3), 0.6, 0.2)


@sfx
def LichSink():
    return room(mix(lp(noise(1.0), 160) * env_ar(1.0, 0.3, 1.2) * 4, stone_crunch(0.9, 50, 150, 900) * 0.6), 1.0, 0.25)


@sfx
def LichDie():
    wail = voice(2.4, [(0, 330), (0.4, 380), (2.4, 120)], [(0, "a"), (1.2, "o"), (2.2, "u")], size=0.95, rough=0.3,
                 breath=0.7, amp=[(0, 0), (0.1, 1), (2.4, 0)])
    return room(mix(wail, SkeletonDie(), at=[0, 1.6]), 1.6, 0.4)


# ================================================================== Orc Warlord
@sfx
def OrcWarlordRoar():
    # a huge, throaty war roar
    roar = voice(1.4, [(0, 85), (0.25, 115), (1.4, 80)], [(0, "uh"), (0.2, "ah"), (1.2, "o")], size=1.6, rough=0.7,
                 breath=0.35, jitter=0.03, fry=0.3, amp=[(0, 0), (0.08, 1), (1.1, 0.9), (1.4, 0)])
    under = voice(1.4, [(0, 55), (1.4, 50)], "o", size=1.9, rough=0.6, breath=0.2, fry=0.6, amp=[(0, 0), (0.1, 1), (1.4, 0)])
    return room(mix(roar, under * 0.6), 1.3, 0.3)


@sfx
def OrcStomp():
    # a heavy armoured footstep on stone
    return room(mix(thud(0.3, 60, 1.5), metal_clang(0.2, 520, 30) * 0.1, lp(noise(0.06), 800) * decay(0.06, 50)), 0.6, 0.15)


@sfx
def OrcAxeRaise():
    # the axe hauled overhead: a strained grunt and steel scraping past armour
    grunt = voice(0.45, [(0, 100), (0.45, 120)], [(0, "uh"), (0.4, "ah")], size=1.5, rough=0.6, breath=0.4,
                  amp=[(0, 0), (0.1, 1), (0.45, 0)])
    scrape = bp(noise(0.4), curve([(0, 2000), (0.4, 4500)], 0.4), 3) * env_ar(0.4, 0.1, 1.2) * 1.0
    return room(mix(grunt, scrape * 0.6), 0.6, 0.18)


@sfx
def OrcCharge():
    return mix(OrcShout(), *[OrcStomp() * 0.7 for _ in range(3)], at=[0, 0.15, 0.45, 0.75])


@sfx
def OrcSlam():
    # the axe crashing into the stone floor: steel impact, the floor cracking, debris
    steel = metal_clang(0.8, 280, 7) * 0.5
    boom = lp(noise(1.0), curve([(0, 3000), (1.0, 120)], 1.0)) * env_ar(1.0, 0.005, 2.5) * 3.5
    return room(mix(click(0.006, 1500) * 2, steel, boom, thud(0.6, 45, 2.0), pad(stone_crunch(0.8, 90, 300, 3000), 0.05)), 1.1, 0.3)


@sfx
def OrcWarlordDie():
    bellow = voice(2.0, [(0, 120), (0.3, 100), (2.0, 50)], [(0, "ah"), (1.0, "uh"), (1.8, "u")], size=1.6, rough=0.7,
                   breath=0.35, fry=0.6, amp=[(0, 0), (0.05, 1), (2.0, 0)])
    fall = mix(metal_clang(1.0, 300, 5) * 0.4, thud(0.8, 40, 2.2), stone_crunch(0.8, 60, 200, 2000) * 0.6)
    return room(mix(bellow, fall, at=[0, 1.5]), 1.5, 0.3)


@sfx
def BossDefeated():
    # a triumphant toll of bells
    tolls = mix(*[bell(f, 2.5, 1.5) * 0.3 for f in (262, 330, 392, 523)], at=[0, 0.25, 0.5, 0.8])
    return room(mix(tolls, bell(131, 3.0, 1.0) * 0.3), 1.8, 0.35)


def main():
    folder = os.path.join(OUT, "Sfx")
    for name, fn in SFX.items():
        x = np.nan_to_num(fn())
        save(x, os.path.join(folder, f"{name}.wav"), peak=0.85, fade=0.002)
    print(f"wrote {len(SFX)} sounds to {folder}")


if __name__ == "__main__":
    main()
