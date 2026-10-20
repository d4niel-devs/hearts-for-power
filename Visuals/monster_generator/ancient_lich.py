"""The Ancient Lich boss (floor 2): a hooded, floating undead sorcerer. A skull glares out of a deep
cowl with burning green eyes under a corroded crown; tattered robes trail off into ghostly wisps
instead of feet, a phylactery glows on its chest and soul motes drift around it. It carries a
gnarled staff topped with a horned skull in green flame. 64x64 per frame, shaded layers like the
Orc Warlord. Animations: Idle (4, hovering), Walk (6, gliding), Attack = raising the staff while
the flame and eyes flare (4), Slam = the cast, the staff thrusts and the flame bursts (4).
Used by bosses.py."""
import math
from PIL import Image
from orc_warlord import (Layer, stack, ramp_pick, paste_rotated, _paste_clipped, SIZE, K, BONE)

ROBE = [(96, 88, 124), (70, 62, 98), (50, 44, 74), (36, 31, 56), (24, 20, 40)]
INNER = [(76, 104, 86), (56, 80, 66), (40, 60, 50), (28, 44, 38), (20, 30, 28)]
CROWN = [(198, 176, 118), (152, 128, 80), (112, 92, 58), (80, 64, 44), (54, 42, 32)]
SKULL = [(214, 220, 196), (182, 188, 162), (140, 146, 124), (100, 106, 92), (66, 70, 62)]
VOID = (10, 8, 16)
GLOW = (110, 255, 140)
GLOW_HOT = (226, 255, 214)
GLOW_DIM = (54, 176, 96)

# ---------------------------------------------------------------- the staff
STAFF_ROWS = [
    ".....g.....",
    "..g..Gg....",
    "..Gg.GWg.g.",
    "..gGgWWGgG.",
    "h..GWWWWG.h",
    "hh.KKKKK.hh",
    ".hKBBBBBKh.",
    ".KBBBBBBbK.",
    ".KBEEBEEbK.",
    ".KBBBnBBbK.",
    "..KBbbbbK..",
    "..KTKTKTK..",
    "...KKdKK...",
    "....KdDK...",
    "....KdDK...",
    "...KdDK....",
    "...KdDK....",
    "...KxxK....",
    "....KdDK...",
    "....KdDK...",
    "....KdDK...",
    "....KPPK...",
    "....KPPK...",
    "....KdDK...",
    "...KdDK....",
    "...KdDK....",
    "...KxxK....",
    "....KdDK...",
    "....KdDK...",
    "....KdDK...",
    "....KdDK...",
    "...KdDK....",
    "...KdDK....",
    "....KK.....",
]
STAFF_GRIP = 22     # row the hand holds
STAFF_ORB = (5, 3)  # flame centre in the staff image
STAFF_HALF = 5


def staff_image(bright=False):
    pal = {'B': SKULL[1], 'b': SKULL[2], 'n': VOID, 'T': SKULL[0], 'h': CROWN[2],
           'd': (74, 58, 50), 'D': (52, 40, 36), 'x': (96, 78, 66), 'P': ROBE[1],
           'E': GLOW_HOT if bright else GLOW,
           'g': GLOW if bright else GLOW_DIM, 'G': GLOW_HOT if bright else GLOW,
           'W': (255, 255, 240) if bright else GLOW_HOT}
    im = Image.new("RGBA", (len(STAFF_ROWS[0]), len(STAFF_ROWS)), (0, 0, 0, 0))
    for y, row in enumerate(STAFF_ROWS):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            im.putpixel((x, y), (K if ch == 'K' else pal[ch]) + (255,))
    return im


STAFF = staff_image(False)
STAFF_LIT = staff_image(True)


# ---------------------------------------------------------------- effects

def glow_ring(im, center, radius, strength):
    """Soft green halo (only over empty or see-through pixels)."""
    cx, cy = center
    for y in range(int(cy - radius - 1), int(cy + radius + 2)):
        for x in range(int(cx - radius - 1), int(cx + radius + 2)):
            if not (0 <= x < SIZE and 0 <= y < SIZE):
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if radius - 1.2 <= d <= radius and im.getpixel((x, y))[3] < 255:
                im.putpixel((x, y), GLOW + (int(190 * strength),))


def motes(im, center, frame, count, radius, spin=0.0, pull=0.0):
    """Soul motes drifting around the lich; `pull` (0..1) draws them in toward `center`."""
    for i in range(count):
        a = i * 2.39996 + frame * 0.55 + spin
        r = radius * (0.65 + 0.35 * ((i * 37) % 10) / 10) * (1 - 0.7 * pull)
        x = int(center[0] + math.cos(a) * r)
        y = int(center[1] + math.sin(a) * r * 0.8 - (frame + i) % 3)
        for dx, dy, alpha in ((0, 0, 230), (0, 1, 110)):
            if 0 <= x + dx < SIZE and 0 <= y + dy < SIZE and im.getpixel((x + dx, y + dy))[3] < 200:
                im.putpixel((x + dx, y + dy), (GLOW_HOT if i % 3 == 0 else GLOW) + (alpha,))


def fade_wisps(im, keep, top=46, bottom=62):
    """The robe dissolves into ghostly wisps toward the floor (the staff and claws stay solid)."""
    for y in range(top, SIZE):
        k = max(0.12, 1 - (y - top) / (bottom - top) * 0.9)
        for x in range(SIZE):
            p = im.getpixel((x, y))
            if p[3] and not keep.getpixel((x, y))[3]:
                im.putpixel((x, y), p[:3] + (int(p[3] * k),))


def with_shadow(im, hover):
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rx = 15 - hover * 1.5
    for y in range(SIZE):
        for x in range(SIZE):
            if ((x + 0.5 - 32) / rx) ** 2 + ((y + 0.5 - 61) / 2.6) ** 2 <= 1:
                base.putpixel((x, y), (20, 16, 24, 100))
    base.alpha_composite(im)
    return base


# ---------------------------------------------------------------- body parts

def crown(layer, cx, top, back=False):
    layer.rect(cx - 8, top + 3, cx + 7, top + 5, CROWN[2])
    layer.rect(cx - 8, top + 3, cx + 7, top + 3, CROWN[1])
    layer.rect(cx - 8, top + 5, cx + 7, top + 5, CROWN[4])
    for i, (dx, h) in enumerate(((-8, 4), (-4, 2), (-1, 5), (3, 2), (6, 4))):
        layer.poly([(cx + dx - 0.5, top + 3.5), (cx + dx + 1, top + 3.5 - h), (cx + dx + 2.5, top + 3.5)],
                   lambda x, y, dx=dx: CROWN[1] if x < cx + dx + 1 else CROWN[3])
    if not back:
        for gx in (cx - 5, cx + 4):
            layer.px(gx, top + 4, GLOW_DIM)
        layer.px(cx - 1, top + 4, GLOW)
        layer.px(cx, top + 4, GLOW)


def hood_front(layer, face, cx, cy, glow, back=False):
    """Deep cowl; `face` gets the skull peering out of the dark."""
    layer.blob(cx, cy, 11, 11, 9, ROBE)
    layer.poly([(cx - 11, cy + 2), (cx - 14, cy + 11), (cx - 6, cy + 8)], lambda x, y: ROBE[3])   # drape
    layer.poly([(cx + 10, cy + 2), (cx + 13, cy + 11), (cx + 5, cy + 8)], lambda x, y: ROBE[3])
    if back:
        for y in range(cy - 8, cy + 8):
            layer.px(cx + (1 if y % 4 < 2 else 0), y, ROBE[3])    # seam down the back
        return
    layer.blob(cx, cy + 3, 7, 7, 6, [VOID] * 5)                   # the dark inside the hood
    # gaunt skull, top in the hood's shadow
    face.blob(cx, cy + 3, 5, 5, 4, SKULL, light=(-0.2, 0.9))
    face.blob(cx, cy + 8, 3, 2, 2, SKULL)
    for y in range(cy - 2, cy + 1):
        for x in range(cx - 5, cx + 6):
            if face.get(x, y)[3]:
                face.px(x, y, SKULL[4] if y < cy else SKULL[3])
    for ex in (cx - 3, cx + 2):                                   # burning eyes
        face.rect(ex, cy + 3, ex + 1, cy + 4, VOID)
        face.px(ex, cy + 3, GLOW_HOT if glow > 0.75 else GLOW)
        face.px(ex + 1, cy + 3, GLOW)
        face.px(ex, cy + 4, GLOW_DIM)
    face.px(cx, cy + 6, VOID)
    face.px(cx - 1, cy + 6, VOID)
    face.rect(cx - 2, cy + 8, cx + 2, cy + 8, VOID)               # teeth
    for tx in (cx - 2, cx, cx + 2):
        face.px(tx, cy + 8, SKULL[0])


def eye_flames(im, cx, cy, glow):
    """Green fire licking up out of the eye sockets when it powers up."""
    if glow < 0.85:
        return
    for ex in (cx - 3, cx + 2):
        for i, alpha in enumerate((200, 140, 70)):
            x, y = ex + (i % 2), cy + 2 - i
            if 0 <= y < SIZE and im.getpixel((x, y))[3] < 255:
                im.putpixel((x, y), GLOW + (alpha,))


def robe_front(layer, cx, b, sway, back=False):
    top = 22 + b
    pts = [(cx - 12, top), (cx + 12, top)]
    hem = 54 + b
    for i in range(12, -1, -1):                                   # tattered, tendril hem
        x = cx - 19 + i * 38 / 12
        long = i % 2 == 0
        pts.append((x + sway * (1.4 if long else 0.6), hem + (6 if long else 0) + (i % 3 == 1)))
    layer.poly(pts, lambda x, y: ramp_pick(ROBE, -0.15 - 0.7 * ((x - cx) / 20) ** 2 - (0.3 if (x + y // 4) % 8 == 0 else 0)))
    if back:
        return
    # inner robe panel with glowing runes
    layer.poly([(cx - 5, top + 2), (cx + 5, top + 2), (cx + 7, hem), (cx - 7, hem)],
               lambda x, y: ramp_pick(INNER, -0.1 - abs(x - cx) / 10))
    for y in range(top + 9, hem - 2, 5):
        for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, 2)):
            layer.px(cx + dx, y + dy, GLOW_DIM)
    for y in range(top + 2, hem):                                 # panel edges
        t = (y - top) / max(1, hem - top)
        layer.px(int(cx - 5 - 2 * t), y, CROWN[3])
        layer.px(int(cx + 5 + 2 * t), y, CROWN[3])


def phylactery(layer, cx, y, glow):
    for dx in range(-5, 6):                                       # chain
        layer.px(cx + dx, y - 4 + abs(dx) // 2 - 2, CROWN[2] if dx % 2 else CROWN[3])
    layer.blob(cx, y, 3, 3, 3, CROWN)
    layer.rect(cx - 1, y - 1, cx + 1, y + 1, GLOW if glow < 0.85 else GLOW_HOT)
    layer.px(cx - 1, y - 1, GLOW_HOT)


def mantle(layer, cx, b):
    layer.blob(cx, 23 + b, 15, 4, 4, ROBE)
    for sx, d in ((cx - 13, -1), (cx + 13, 1)):                   # bone spikes on the shoulders
        layer.blob(sx, 22 + b, 4, 3, 3, BONE)
        for i, (ox, h) in enumerate(((-1, 5), (2, 3))):
            bx = sx + ox * d
            layer.poly([(bx - 1, 21 + b), (bx + d * 2, 21 + b - h), (bx + 1.5, 21 + b)], lambda x, y: BONE[1] if y < 19 + b else BONE[2])


def sleeve_arm(layer, shoulder, hand):
    sx, sy = shoulder
    hx, hy = hand
    ex, ey = (sx + hx) / 2 + (2 if hx < sx else -2), (sy + hy) / 2 + 2
    layer.thick_line(sx, sy, ex, ey, 6, ROBE)
    layer.thick_line(ex, ey, hx, hy - 1, 5, ROBE)
    layer.blob(hx, hy - 2, 4, 2, 3, ROBE)                         # sleeve cuff


def claw(layer, x, y, open_=False):
    layer.blob(x, y, 2, 2, 2, SKULL)
    for dx in (-2, 0, 2):
        reach = 4 if open_ else 3
        for i in range(1, reach + 1):
            fx = x + dx + (dx // 2) * (i // 2 if open_ else 0)
            layer.px(fx, y + 1 + i, SKULL[1] if i < reach else SKULL[3])


HOVER_IDLE = [0, 1, 2, 1]
HOVER_WALK = [0, 1, 2, 2, 1, 0]
SWAY_IDLE = [0, 1, 0, -1]
SWAY_WALK = [-2, -3, -2, -1, -2, -3]       # robe trails behind while gliding


def pose_params(pose, frame):
    hover, sway, glow = 1, 0, 0.6
    if pose == "idle":
        hover, sway, glow = HOVER_IDLE[frame], SWAY_IDLE[frame], [0.5, 0.65, 0.8, 0.65][frame]
    elif pose == "walk":
        hover, sway = HOVER_WALK[frame], SWAY_WALK[frame]
    elif pose == "windup":
        hover, glow = [1, 2, 3, 3][frame], [0.7, 0.85, 1.0, 1.0][frame]
        sway = [0, 1, 1, 2][frame]
    elif pose == "cast":
        hover, glow, sway = [3, 1, 1, 2][frame], 1.0, [2, -2, -2, 0][frame]
    return hover, sway, glow


def front(pose, frame, back=False):
    robe, body, arms, shoulders, hood, face, staff_l, hands = (Layer() for _ in range(8))
    cx = 32
    hover, sway, glow = pose_params(pose, frame)
    b = 3 - hover

    robe_front(robe, cx, b, sway, back)
    if not back:
        phylactery(body, cx, 29 + b, glow)
    mantle(shoulders, cx, b)
    hood_front(hood, face, cx, 13 + b, glow, back)
    crown(hood, cx, 0 + b, back)

    left_open = False
    if pose == "windup":
        right = [(cx - 16, 37 + b), (cx - 15, 31 + b), (cx - 13, 26 + b), (cx - 13, 25 + b)][frame]
        left = [(cx + 15, 38 + b), (cx + 16, 33 + b), (cx + 17, 28 + b), (cx + 17, 27 + b)][frame]
        left_open = frame >= 1
    elif pose == "cast":
        right = [(cx - 13, 24 + b), (cx - 7, 29 + b), (cx - 6, 31 + b), (cx - 11, 35 + b)][frame]
        left = [(cx + 17, 27 + b), (cx + 11, 31 + b), (cx + 11, 31 + b), (cx + 14, 35 + b)][frame]
        left_open = frame < 3
    else:
        drift = 0 if pose == "idle" else [-1, 0, 1, 1, 0, -1][frame]
        right, left = (cx - 17, 39 + b + drift), (cx + 16, 40 + b - drift)
    staff = STAFF_LIT if glow >= 0.9 else STAFF
    _paste_clipped(staff_l.im, staff, right[0] - STAFF_HALF, right[1] - STAFF_GRIP)
    orb = (right[0] - STAFF_HALF + STAFF_ORB[0] + 0.5, right[1] - STAFF_GRIP + STAFF_ORB[1] + 0.5)

    sleeve_arm(arms, (cx - 12, 24 + b), right)
    sleeve_arm(arms, (cx + 12, 24 + b), left)
    claw(hands, *right)
    claw(hands, *left, open_=left_open)

    if back:
        order = [staff_l.im, hands, arms, robe, shoulders, hood]
    else:
        order = [robe, body, arms, shoulders, hood, face, staff_l.im, hands]
    im = stack(order, shadow=False)
    keep = stack([staff_l.im, hands], shadow=False)
    fade_wisps(im, keep)

    if not back:
        eye_flames(im, cx, 16 + b, glow)
        if glow >= 0.85:                                            # green light from the left hand too
            glow_ring(im, (left[0] + 0.5, left[1] + 3.5), 3, glow)
    if glow > 0.6:
        glow_ring(im, orb, 4 + (2 if glow >= 0.9 else 0), glow)
    if pose == "cast" and frame in (1, 2):
        glow_ring(im, orb, [0, 9, 13][frame], 1.0 - 0.3 * (frame - 1))
    pull = [0, 0.3, 0.6, 0.8][frame] if pose == "windup" else 0
    center = orb if pose == "windup" else (cx, 34 + b)
    motes(im, center, frame, 7, 22 if pose != "windup" else 16, pull=pull)
    if back:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return with_shadow(im, hover)


def side(pose, frame):
    robe, arms, hood, face, staff_l, hands = (Layer() for _ in range(6))
    cx = 31
    hover, sway, glow = pose_params(pose, frame)
    b = 3 - hover
    trail = sway - (2 if pose == "walk" else 0)

    # robe in profile, trailing back into wisps
    top = 22 + b
    pts = [(cx - 6, top), (cx + 7, top), (cx + 9, 54 + b), (cx + 6, 58 + b), (cx + 3, 54 + b),
           (cx, 60 + b + trail // 2), (cx - 3, 55 + b), (cx - 7 + trail, 60 + b), (cx - 10 + trail, 54 + b),
           (cx - 14 + trail * 1.5, 58 + b), (cx - 12 + trail, 48 + b)]
    robe.poly(pts, lambda x, y: ramp_pick(ROBE, 0.1 - (cx + 9 - x) / 22 - (0.3 if (x + y // 4) % 7 == 0 else 0)))
    for y in range(top + 2, 54 + b):
        robe.px(cx + 7 + (y - top) * 2 // 34, y, CROWN[3])
    robe.blob(cx + 1, 23 + b, 9, 4, 4, ROBE)                       # mantle
    robe.blob(cx + 1, 22 + b, 3, 3, 3, BONE)
    robe.poly([(cx, 21 + b), (cx - 2, 15 + b), (cx + 2, 21 + b)], lambda x, y: BONE[1])   # shoulder spike

    # hood in profile, facing right, with the skull in its opening
    hx, hy = cx + 1, 13 + b
    hood.blob(hx, hy, 10, 11, 9, ROBE)
    hood.poly([(hx - 8, hy - 4), (hx - 14, hy + 4), (hx - 7, hy + 6)], lambda x, y: ROBE[3])   # cowl point
    hood.blob(hx + 6, hy + 3, 4, 6, 5, [VOID] * 5)
    face.blob(hx + 6, hy + 3, 3, 4, 4, SKULL, light=(0.6, 0.6))
    face.blob(hx + 7, hy + 7, 2, 2, 2, SKULL)
    for x in range(hx + 3, hx + 10):
        if face.get(x, hy):
            face.px(x, hy, SKULL[4])
    face.rect(hx + 6, hy + 2, hx + 7, hy + 3, VOID)
    face.px(hx + 7, hy + 2, GLOW_HOT if glow > 0.75 else GLOW)
    face.px(hx + 6, hy + 2, GLOW)
    face.rect(hx + 6, hy + 7, hx + 9, hy + 7, VOID)
    face.px(hx + 7, hy + 7, SKULL[0])
    crown(hood, hx, 0 + b)

    shoulder = (cx + 1, 24 + b)
    if pose in ("windup", "cast"):
        keys = {"windup": [(-40, 90), (-5, 95), (15, 102), (18, 104)],
                "cast": [(18, 104), (5, 55), (-5, 30), (-25, 70)]}[pose]
        arm_angle, direction = keys[frame]
        rad = math.radians(arm_angle)
        hand = (int(round(shoulder[0] + math.cos(rad) * 11)), int(round(shoulder[1] - math.sin(rad) * 11)))
    else:
        drift = 0 if pose == "idle" else [-1, 0, 1, 1, 0, -1][frame]
        hand, direction = (cx + 11 + drift, 40 + b), 90
    staff = STAFF_LIT if glow >= 0.9 else STAFF
    paste_rotated(staff_l.im, staff, (STAFF_HALF, STAFF_GRIP), direction, hand)
    reach = STAFF_GRIP - STAFF_ORB[1]
    orb = (hand[0] + math.cos(math.radians(direction)) * reach + 0.5, hand[1] - math.sin(math.radians(direction)) * reach + 0.5)
    sleeve_arm(arms, shoulder, hand)
    claw(hands, *hand)

    im = stack([robe, hood, face, arms, staff_l.im, hands], shadow=False)
    keep = stack([staff_l.im, hands], shadow=False)
    fade_wisps(im, keep)
    if glow >= 0.85:
        for i, alpha in enumerate((200, 130, 60)):
            x, y = hx + 7 + i // 2, hy + 1 - i
            if 0 <= y < SIZE and im.getpixel((x, y))[3] < 255:
                im.putpixel((x, y), GLOW + (alpha,))
    if glow > 0.6:
        glow_ring(im, orb, 4 + (2 if glow >= 0.9 else 0), glow)
    if pose == "cast" and frame in (1, 2):
        glow_ring(im, orb, [0, 9, 13][frame], 1.0 - 0.3 * (frame - 1))
    pull = [0, 0.3, 0.6, 0.8][frame] if pose == "windup" else 0
    motes(im, orb if pose == "windup" else (cx, 34 + b), frame, 7, 16 if pose == "windup" else 22, pull=pull)
    return with_shadow(im, hover)


def frames(view):
    if view == "Side":
        make = side
    else:
        back = view == "Up"
        make = lambda pose, f: front(pose, f, back)
    return {
        "Idle": [make("idle", f) for f in range(4)],
        "Walk": [make("walk", f) for f in range(6)],
        "Attack": [make("windup", f) for f in range(4)],
        "Slam": [make("cast", f) for f in range(4)],
    }


if __name__ == "__main__":
    rows = []
    for view in ("Down", "Up", "Side"):
        fr = frames(view)
        for anim in ("Idle", "Walk", "Attack", "Slam"):
            rows.append(fr[anim])
    sheet = Image.new("RGBA", (6 * 66, len(rows) * 66), (88, 86, 98, 255))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.alpha_composite(im, (c * 66, r * 66))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save("lich_preview.png")
    print("preview written")
