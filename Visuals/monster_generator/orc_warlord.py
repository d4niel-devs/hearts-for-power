"""The Orc Warlord boss, 64x64 per frame (same pixel size as the knight).
Built from layers (cape, legs, armour, arms, head, helmet, horns, axe, hands), each shaded with
5-step colour ramps and given its own dark outline, then stacked. The battle axe is hand-drawn
pixel art. Used by bosses.py."""
import math
from PIL import Image

SIZE = 64
K = (24, 18, 26)

# 5-step ramps: highlight, light, mid, dark, deep
SKIN = [(184, 222, 128), (146, 188, 98), (108, 150, 76), (78, 112, 58), (52, 78, 44)]
IRON = [(232, 234, 242), (182, 186, 200), (134, 138, 156), (94, 98, 118), (62, 64, 82)]
LEATHER = [(160, 112, 74), (126, 86, 56), (96, 64, 42), (70, 46, 32), (48, 32, 24)]
CAPE = [(204, 62, 58), (164, 40, 44), (124, 28, 36), (90, 20, 30), (62, 14, 24)]
FUR = [(176, 156, 130), (140, 122, 100), (108, 92, 76), (80, 66, 56), (56, 46, 40)]
BONE = [(250, 244, 222), (222, 212, 184), (184, 172, 144), (140, 130, 108), (100, 92, 78)]
EYE = (255, 74, 40)
EYE_GLOW = (255, 196, 120)

AXE_PAL = {
    'L': (236, 238, 246), 'S': (116, 120, 138), 'E': (246, 250, 255), 'M': (158, 162, 180), 'D': (96, 100, 118),
    'W': (148, 102, 62), 'w': (104, 70, 42), 'B': (74, 48, 32), 'b': (118, 82, 56), 'R': (200, 50, 46),
}
_AXE_HEAD_HALF = [
    "..........K",
    ".........KL",
    ".........KL",
    "..KKKK...KS",
    ".KEEEMK..KS",
    "KEEMMMMK.KS",
    "KEMMMMMMKKS",
    "KEMMMMDMDDS",
    "KEMMMDMMDDS",
    "KEMMMMMMDDS",
    "KEMMMDMMDDS",
    "KEMMMMDMDDS",
    "KEMMMMMMKKS",
    "KEEMMMMK.KS",
    ".KEEEMK..KS",
    "..KKKK...KS",
    ".........KS",
]
_AXE_HAFT = [
    ".........KWwK.........",
    ".........KWwK.........",
    ".........KWwK.........",
    ".........KbBK.........",
    ".........KBbK.........",
    ".........KbBK.........",
    ".........KWwK.........",
    ".........KWwK.........",
    ".........KRRK.........",
    ".........KRRK.........",
    ".........KWwK.........",
    ".........KWwK.........",
    ".........KbBK.........",
    ".........KBbK.........",
    ".........KbBK.........",
    ".........KBbK.........",
    ".........KWwK.........",
    ".........KWwK.........",
    ".........KWwK.........",
    "........KSSSSK........",
    ".........KSSK.........",
    "..........KK..........",
]


def _axe_image():
    rows = [h + h[::-1] for h in _AXE_HEAD_HALF] + _AXE_HAFT
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            c = K if ch == 'K' else AXE_PAL[ch]
            im.putpixel((x, y), c + (255,))
    return im


AXE = _axe_image()                               # head at the top, 22 x 39
AXE_GRIP = 27                                    # haft row the hand usually holds
AXE_HALF = AXE.width // 2
AXE_OVERHEAD = AXE.rotate(90, expand=True)       # horizontal, head on the left
AXE_DOWN = AXE.transpose(Image.FLIP_TOP_BOTTOM)  # head at the bottom (slam)


class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.im.putpixel((x, y), tuple(c[:3]) + ((c[3],) if len(c) == 4 else (255,)))

    def get(self, x, y):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            return self.im.getpixel((x, y))
        return (0, 0, 0, 0)

    def blob(self, cx, cy, rx, ry_top, ry_bottom, ramp, light=(-0.55, -0.85), only=None):
        for y in range(SIZE):
            for x in range(SIZE):
                ry = ry_top if y < cy else ry_bottom
                if rx <= 0 or ry <= 0:
                    continue
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = nx * nx + ny * ny
                if d > 1 or (only and not only(x, y)):
                    continue
                t = nx * light[0] + ny * light[1]
                if d > 0.82:
                    t -= 0.35            # darker rim reads as roundness
                self.px(x, y, ramp_pick(ramp, t))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def poly(self, points, c_or_fn):
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if point_in_poly(x + 0.5, y + 0.5, points):
                    self.px(x, y, c_or_fn(x, y) if callable(c_or_fn) else c_or_fn)

    def thick_line(self, x0, y0, x1, y1, width, ramp):
        """A limb: a capsule from (x0,y0) to (x1,y1), shaded across its width."""
        dx, dy = x1 - x0, y1 - y0
        length = max(0.001, (dx * dx + dy * dy) ** 0.5)
        nx, ny = -dy / length, dx / length
        r = width / 2
        for y in range(SIZE):
            for x in range(SIZE):
                px_, py_ = x + 0.5 - x0, y + 0.5 - y0
                t = max(0.0, min(1.0, (px_ * dx + py_ * dy) / (length * length)))
                cx_, cy_ = x0 + dx * t, y0 + dy * t
                ox, oy = x + 0.5 - cx_, y + 0.5 - cy_
                if ox * ox + oy * oy > r * r:
                    continue
                side = (ox * nx + oy * ny) / r          # -1..1 across the limb
                light_side = -side if nx > 0 else side
                self.px(x, y, ramp_pick(ramp, light_side * 0.8 - 0.05))

    def paste(self, im, x, y):
        self.im.alpha_composite(im, (int(x), int(y)))


def ramp_pick(ramp, t):
    if t > 0.55:
        return ramp[0]
    if t > 0.18:
        return ramp[1]
    if t > -0.22:
        return ramp[2]
    if t > -0.6:
        return ramp[3]
    return ramp[4]


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def outlined(layer):
    out = layer.im.copy()
    for y in range(SIZE):
        for x in range(SIZE):
            if layer.get(x, y)[3] == 255:
                continue
            if any(layer.get(x + dx, y + dy)[3] == 255 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), K + (255,))
    return out


def stack(layers, shadow=True):
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    if shadow:
        for y in range(SIZE):
            for x in range(SIZE):
                if ((x + 0.5 - 32) / 19) ** 2 + ((y + 0.5 - 61) / 3) ** 2 <= 1:
                    im.putpixel((x, y), (20, 16, 24, 110))
    for layer in layers:
        if layer is None:
            continue
        im.alpha_composite(outlined(layer) if isinstance(layer, Layer) else layer)
    return im


# ---------------------------------------------------------------- body parts

def horn(layer, base, tip, ctrl, r0=3.2, r1=0.8):
    """Curved horn along a quadratic curve, thick at the base, with ring ridges."""
    steps = 22
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * base[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0]
        y = (1 - t) ** 2 * base[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]
        r = r0 + (r1 - r0) * t
        ring = (i % 4 == 2) and t < 0.8
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                d = ((xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2) ** 0.5
                if d > r:
                    continue
                shade = -((xx + 0.5 - x) * 0.6 + (yy + 0.5 - y) * 0.8) / max(r, 0.5)
                c = ramp_pick(BONE, shade)
                if ring:
                    c = BONE[3]
                layer.px(xx, yy, c)


def head_front(layer, cx, cy, back=False):
    layer.blob(cx, cy + 1, 11, 9, 9, SKIN)                     # broad head and jaw
    layer.blob(cx - 7, cy + 5, 3, 3, 3, SKIN)                  # cheeks / jaw corners
    layer.blob(cx + 7, cy + 5, 3, 3, 3, SKIN)
    if back:
        return
    # angry brow: a dark V over the eyes
    for i in range(6):
        layer.px(cx - 8 + i, cy - 2 + i // 2, SKIN[4])
        layer.px(cx + 7 - i, cy - 2 + i // 2, SKIN[4])
        layer.px(cx - 8 + i, cy - 1 + i // 2, SKIN[3])
        layer.px(cx + 7 - i, cy - 1 + i // 2, SKIN[3])
    for ex in (cx - 5, cx + 3):                                # glowing red eyes
        layer.rect(ex, cy + 1, ex + 2, cy + 2, EYE)
        layer.px(ex + (0 if ex < cx else 2), cy + 1, EYE_GLOW)
    layer.rect(cx - 1, cy + 2, cx, cy + 5, SKIN[1])            # nose ridge
    layer.px(cx - 2, cy + 5, SKIN[4])
    layer.px(cx + 1, cy + 5, SKIN[4])
    layer.rect(cx - 5, cy + 8, cx + 4, cy + 8, (60, 26, 34))   # grim mouth
    layer.rect(cx - 4, cy + 9, cx + 3, cy + 9, SKIN[3])
    for tx in (cx - 5, cx + 3):                                # big lower tusks
        layer.rect(tx, cy + 5, tx + 1, cy + 8, BONE[1])
        layer.px(tx, cy + 5, BONE[0])
        layer.px(tx + 1, cy + 8, BONE[3])
    for i in range(4):                                         # scar across the left cheek
        layer.px(cx - 8 + i, cy + 2 + i, SKIN[4])


def helmet_front(layer, cx, cy, back=False):
    layer.blob(cx, cy - 4, 11, 6, 3, IRON, only=lambda x, y: y <= cy - 3)
    layer.rect(cx - 11, cy - 4, cx + 10, cy - 3, IRON[3])      # rim
    for rx in (cx - 9, cx - 4, cx + 3, cx + 8):
        layer.px(rx, cy - 4, IRON[0])                          # rivets
    if not back:
        layer.rect(cx - 1, cy - 4, cx, cy + 3, IRON[1])        # nose guard
        layer.px(cx, cy + 3, IRON[3])
    else:
        layer.blob(cx, cy, 11, 9, 9, IRON)                     # from behind the helmet hides the whole head
        for y in range(cy - 8, cy + 8):                        # back ridge
            if layer.get(cx, y)[3]:
                layer.px(cx, y, IRON[0] if y < cy else IRON[1])
                layer.px(cx + 1, y, IRON[3])
        layer.rect(cx - 10, cy + 5, cx + 9, cy + 6, IRON[3])   # lower rim


def pauldron(layer, cx, cy, mirror):
    layer.blob(cx, cy, 8, 6, 5, IRON)
    layer.blob(cx + (1 if mirror else -1), cy + 5, 7, 3, 3, IRON)              # lower plate
    for i, dx in enumerate((-4, 0, 4)):
        sx = cx + dx * (-1 if mirror else 1)
        top = cy - 6 + (1 if i != 1 else 0)
        h = 7 if i == 1 else 5
        lean = 2 if not mirror else -2
        layer.poly([(sx - 2, top + 2), (sx + 2, top + 2), (sx + lean, top - h)],
                   lambda x, y: BONE[1] if x < sx else BONE[2])
    for rx in (-5, -1, 3):
        layer.px(cx + rx, cy + 4, IRON[0])


def fur_collar(layer, cx, cy, width=15):
    layer.blob(cx, cy, width, 4, 5, FUR)
    for x in range(cx - width + 1, cx + width):
        if x % 3 == 0:
            layer.px(x, cy + 4 + (x % 2), FUR[3])               # ragged tufts
        if x % 4 == 1:
            layer.px(x, cy - 2, FUR[0])


def fist(layer, x, y):
    layer.blob(x, y, 4, 4, 4, SKIN)
    layer.px(x - 1, y - 1, SKIN[0])
    for i in (-2, 0, 2):
        layer.px(x + i, y + 2, SKIN[3])                         # knuckles


def arm(layer, shoulder, hand, bracer=True):
    sx, sy = shoulder
    hx, hy = hand
    layer.thick_line(sx, sy, hx, hy, 7, SKIN)
    if bracer:
        bx, by = sx + (hx - sx) * 0.55, sy + (hy - sy) * 0.55
        layer.thick_line(bx, by, hx - (hx - sx) * 0.12, hy - (hy - sy) * 0.12, 8, IRON)


def cape_front(layer, sway, top=22, bottom=58, half_top=17, half_bottom=23, cx=32):
    points = [(cx - half_top, top), (cx + half_top, top)]
    # torn bottom edge
    for i in range(9, -1, -1):
        x = cx - half_bottom + i * (2 * half_bottom) / 9 + sway
        y = bottom - (3 if i % 2 else 0)
        points.append((x, y))
    layer.poly(points, lambda x, y: CAPE[2] if (x + y // 7) % 6 else CAPE[3])
    for x in range(cx - half_top + 2, cx + half_top - 1, 6):   # fold highlights
        for y in range(top + 3, bottom - 4):
            if layer.get(x, y)[3]:
                layer.px(x, y, CAPE[1])


def legs_front(layer, lift_l, lift_r, bob):
    for lx, lift in ((23, lift_l), (35, lift_r)):
        top = 46 + bob
        foot = 60 - lift
        layer.rect(lx, top, lx + 6, foot - 8, LEATHER[3])                       # trousers
        layer.rect(lx, foot - 9, lx + 6, foot - 4, IRON[2])                     # greave
        layer.rect(lx + 1, foot - 9, lx + 1, foot - 4, IRON[1])
        layer.rect(lx - 1, foot - 10, lx + 7, foot - 9, IRON[3])                # knee guard
        layer.px(lx + 3, foot - 10, IRON[0])
        layer.rect(lx - 1, foot - 3, lx + 7, foot, LEATHER[3])                  # boot
        layer.rect(lx - 1, foot - 3, lx + 7, foot - 3, LEATHER[2])
        layer.rect(lx - 1, foot, lx + 7, foot, LEATHER[4])


def skirt(layer, cx, bob, half=12):
    for i, x in enumerate(range(cx - half, cx + half, 4)):
        length = 9 if 1 <= i <= len(range(cx - half, cx + half, 4)) - 2 else 7
        ramp_i = 1 if i % 2 else 2
        layer.rect(x, 43 + bob, x + 3, 43 + bob + length, LEATHER[ramp_i])
        layer.rect(x, 43 + bob + length, x + 3, 43 + bob + length, LEATHER[4])
        layer.rect(x + 3, 43 + bob, x + 3, 43 + bob + length, LEATHER[4])


def torso_front(layer, cx, bob, back=False):
    layer.blob(cx, 32 + bob, 12, 11, 10, IRON)                                  # chest plate
    if not back:
        for y in range(23 + bob, 41 + bob):                                     # centre ridge
            layer.px(cx, y, IRON[0] if y < 32 + bob else IRON[1])
            layer.px(cx + 1, y, IRON[3])
        for x in range(cx - 10, cx + 11):                                        # plate seams
            if layer.get(x, 31 + bob)[3]:
                layer.px(x, 31 + bob + (abs(x - cx) // 6), IRON[3])
            if layer.get(x, 36 + bob)[3]:
                layer.px(x, 36 + bob, IRON[3])
        for rx, ry in ((-8, 27), (8, 27), (-9, 34), (9, 34)):
            layer.px(cx + rx, ry + bob, IRON[0])
    # belt with a skull buckle
    layer.rect(cx - 14, 40 + bob, cx + 13, 43 + bob, LEATHER[3])
    layer.rect(cx - 14, 40 + bob, cx + 13, 40 + bob, LEATHER[1])
    if not back:
        layer.blob(cx, 41 + bob, 4, 3, 3, BONE)
        layer.px(cx - 2, 41 + bob, K)
        layer.px(cx + 1, 41 + bob, K)
        layer.px(cx - 1, 43 + bob, K)
        layer.px(cx + 1, 43 + bob, K)


# ---------------------------------------------------------------- poses

WALK_LIFT_L = [4, 2, 0, 0, 0, 0]
WALK_LIFT_R = [0, 0, 0, 4, 2, 0]
WALK_BOB = [0, -1, 1, 0, -1, 1]       # dips when each foot slams down
WALK_SWAY = [-1, 0, 1, 1, 0, -1]


def front(pose, frame, back=False):
    """Front (Down) view; the back (Up) view is drawn from the same parts and mirrored."""
    cape, legs, body, arms, shoulders, head, horns, hands = (Layer() for _ in range(8))
    cx = 32
    bob, lift_l, lift_r, sway = 0, 0, 0, 0
    if pose == "idle":
        bob = [0, 0, 1, 1][frame]
        sway = [0, 1, 1, 0][frame]
    elif pose == "walk":
        bob, lift_l, lift_r, sway = WALK_BOB[frame], WALK_LIFT_L[frame], WALK_LIFT_R[frame], WALK_SWAY[frame]
    elif pose == "windup":
        bob = [0, -1, -1, -1][frame]
    elif pose == "slam":
        bob = [-2, 0, 2, 3, 2][frame]
    elif pose == "charge":
        c = CHARGE_STEPS[frame]
        bob, lift_l, lift_r = WALK_BOB[c] - 1, WALK_LIFT_L[c], WALK_LIFT_R[c]
        sway = [-2, -1, -2, -1][frame]

    shake = 1 if pose == "windup" and frame == 3 else 0
    cx += shake

    if back:
        cape_front(cape, sway, top=21 + bob, bottom=59, half_top=18, half_bottom=24, cx=cx)
    else:
        cape_front(cape, sway, top=22 + bob, cx=cx)
    legs_front(legs, lift_l, lift_r, bob)
    skirt(legs, cx, bob)
    torso_front(body, cx, bob, back)

    # hands and the axe
    axe_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    down_grip = AXE_DOWN.height - 1 - AXE_GRIP          # grip row once the axe is flipped head-down
    after = None                                        # extra effect drawn on top: ("dust", amount) / ("streaks", top)
    if pose == "windup":
        # lift from the side, across the chest, to overhead (then hold, trembling)
        right_hand, left_hand = [((cx - 17, 36 + bob), (cx + 17, 40 + bob)), ((cx - 13, 24 + bob), (cx + 8, 30 + bob)),
                                 ((cx - 9, 13 + bob), (cx + 9, 13 + bob)), ((cx - 9, 13 + bob), (cx + 9, 13 + bob))][frame]
        if frame < 2:
            paste_rotated(axe_img, AXE, (AXE_HALF, AXE_GRIP), [105, 140][frame], right_hand)
        else:
            _paste_clipped(axe_img, AXE_OVERHEAD, cx - 33, 13 + bob - AXE_HALF)
    elif pose == "charge":
        # held high overhead in both hands, trembling with every heavy step
        tremble = frame % 2
        right_hand, left_hand = (cx - 9 + tremble, 13 + bob), (cx + 9 + tremble, 13 + bob)
        _paste_clipped(axe_img, AXE_OVERHEAD, cx - 33 + tremble, 13 + bob - AXE_HALF)
        after = ("kick", frame)
    elif pose == "slam":
        # high overhead -> coming down -> impact -> dust -> recover
        grips = [((cx - 3, 5 + bob), (cx + 3, 8 + bob)), ((cx - 2, 20 + bob), (cx + 2, 24 + bob)),
                 ((cx - 1, 33), (cx + 1, 37)), ((cx - 1, 33), (cx + 1, 37)), ((cx - 2, 31), (cx + 2, 35))]
        right_hand, left_hand = grips[frame]
        if frame == 0:
            _paste_clipped(axe_img, AXE, right_hand[0] - AXE_HALF, right_hand[1] - AXE_GRIP)
        elif frame == 1:
            _paste_clipped(axe_img, AXE_DOWN, cx - AXE_HALF, right_hand[1] - down_grip)
            after = ("streaks", right_hand[1] - down_grip + 22)
        else:
            _paste_clipped(axe_img, AXE_DOWN, cx - AXE_HALF, 61 - AXE_DOWN.height)
            after = ("dust", [0.0, 0.0, 0.6, 1.0, 0.5][frame])
    else:
        swing = 0 if pose == "idle" else [-2, -1, 0, 2, 1, 0][frame]
        right_hand, left_hand = (cx - 19, 44 + bob + swing), (cx + 19, 44 + bob - swing)
        _paste_clipped(axe_img, AXE, right_hand[0] - AXE_HALF, right_hand[1] - AXE_GRIP)

    arm(arms, (cx - 13, 28 + bob), right_hand)
    arm(arms, (cx + 13, 28 + bob), left_hand)
    pauldron(shoulders, cx - 14, 24 + bob, mirror=False)
    pauldron(shoulders, cx + 14, 24 + bob, mirror=True)
    fur_collar(shoulders, cx, 21 + bob, width=13)

    head_front(head, cx, 13 + bob, back)
    helmet_front(head, cx, 13 + bob, back)
    horn(horns, (cx - 9, 8 + bob), (cx - 21, 0), (cx - 20, 9 + bob))
    horn(horns, (cx + 9, 8 + bob), (cx + 21, 0), (cx + 20, 9 + bob))

    fist(hands, *right_hand)
    fist(hands, *left_hand)

    if back:
        order = [legs, body, arms, axe_img, hands, cape, shoulders, head, horns]
    elif pose == "slam":
        order = [cape, legs, body, arms, shoulders, head, horns, axe_img, hands]
    elif pose == "windup":
        order = [cape, legs, body, arms, shoulders, head, horns, axe_img, hands]
    else:
        order = [cape, legs, body, arms, shoulders, head, horns, axe_img, hands]
    im = stack(order)

    if after and after[0] == "dust" and after[1] > 0:
        _dust(im, cx, after[1])
    elif after and after[0] == "kick":
        _kick_dust(im, cx + (-7 if after[1] in (0, 1) else 6), after[1])
    elif after and after[0] == "streaks":
        streaks(im, (cx - 7, cx - 3, cx + 3, cx + 7), after[1] - 14, after[1])
    if back:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)     # from behind, the axe hand is on the other side
    return im


def paste_rotated(dst, src, pivot, direction_deg, at):
    """Draws `src` (drawn pointing up) turned to point along direction_deg (0 = right, 90 = up),
    with its pivot pixel landing on `at`. Nearest-pixel sampling keeps it crisp."""
    theta = math.radians(direction_deg - 90)
    c, s_ = math.cos(theta), math.sin(theta)
    reach = int(max(src.width, src.height) * 1.2)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            # inverse of a counter-clockwise turn on screen (y points down)
            sx = dx * c - dy * s_ + pivot[0]
            sy = dx * s_ + dy * c + pivot[1]
            ix, iy = int(round(sx)), int(round(sy))
            if not (0 <= ix < src.width and 0 <= iy < src.height):
                continue
            p = src.getpixel((ix, iy))
            x, y = int(at[0]) + dx, int(at[1]) + dy
            if p[3] and 0 <= x < SIZE and 0 <= y < SIZE:
                dst.putpixel((x, y), p)


def smear(im, center, radius, from_deg, to_deg, width=3):
    """Pale motion arc where the axe head just passed."""
    steps = 18
    for i in range(steps + 1):
        a = math.radians(from_deg + (to_deg - from_deg) * i / steps)
        fade = i / steps
        for w in range(width):
            r = radius - w
            x = int(round(center[0] + math.cos(a) * r))
            y = int(round(center[1] - math.sin(a) * r))
            if 0 <= x < SIZE and 0 <= y < SIZE and im.getpixel((x, y))[3] == 0:
                im.putpixel((x, y), (236, 236, 244, int(60 + 150 * fade)))


def streaks(im, xs, y_top, y_bottom):
    """Vertical speed lines above a downward swing (front view)."""
    for x in xs:
        for y in range(max(0, y_top), min(SIZE, y_bottom)):
            if im.getpixel((x, y))[3] == 0:
                im.putpixel((x, y), (236, 236, 244, int(70 + 140 * (y - y_top) / max(1, y_bottom - y_top))))


def _paste_clipped(dst, src, x, y):
    for sy in range(src.height):
        for sx in range(src.width):
            p = src.getpixel((sx, sy))
            if p[3] and 0 <= x + sx < SIZE and 0 <= y + sy < SIZE:
                dst.putpixel((x + sx, y + sy), p)


def _dust(im, cx, amount=1.0):
    puffs = ((-14, 0), (-11, -2), (-9, 1), (10, 0), (12, -2), (15, 1), (-6, -1), (7, -1), (-17, -1), (18, -1), (-4, -3), (5, -3))
    for dx, dy in puffs[:int(len(puffs) * amount)]:
        x, y = cx + dx, 60 + dy
        for ox, oy in ((0, 0), (1, 0), (0, -1)):
            if 0 <= x + ox < SIZE and 0 <= y + oy < SIZE:
                im.putpixel((x + ox, y + oy), (196, 184, 160, 255))
    for i in range(6):                                  # ground cracks
        for x0, d in ((cx - 4, -1), (cx + 4, 1)):
            x, y = x0 + d * i, 61 - (i % 2)
            if 0 <= x < SIZE:
                im.putpixel((x, y), K + (255,))


CHARGE_STEPS = [0, 2, 3, 5]      # walk-cycle frames reused (faster) for the charge


def _kick_dust(im, x, frame, behind=False):
    """Small dust clouds kicked up by the heavy running steps."""
    puffs = [(0, 0), (-2, -1), (2, -1), (-1, -2)] if not behind else [(0, 0), (-3, -1), (-6, -2), (-2, -3), (-8, -1)]
    for i, (dx, dy) in enumerate(puffs[:3 + frame % 2 * 2]):
        px_, py_ = x + dx, 60 + dy
        for ox, oy in ((0, 0), (1, 0), (0, -1)):
            if 0 <= px_ + ox < SIZE and 0 <= py_ + oy < SIZE and im.getpixel((px_ + ox, py_ + oy))[3] < 255:
                im.putpixel((px_ + ox, py_ + oy), (196, 184, 160, 220 - i * 30))


def speed_lines(im, x_right, frame):
    """Horizontal speed lines streaming behind him while he charges (side view)."""
    for i, y in enumerate((20, 30, 39, 48)):
        length = 6 + ((i + frame) % 3) * 3
        y += frame % 2
        for x in range(x_right - length, x_right):
            if 0 <= x < SIZE and im.getpixel((x, y))[3] == 0:
                im.putpixel((x, y), (236, 236, 244, int(60 + 140 * (x - x_right + length) / length)))


def side(pose, frame):
    """Side view, facing right (mirrored in-game for left)."""
    cape, far, legs, body, arms, shoulders, head, horns, hands = (Layer() for _ in range(9))
    bob, stride, sway = 0, 0, 0
    if pose == "idle":
        bob = [0, 0, 1, 1][frame]
        sway = [0, 1, 1, 0][frame]
    elif pose == "walk":
        bob = WALK_BOB[frame]
        stride = [5, 2, 0, -5, -2, 0][frame]
        sway = [-2, -1, 0, -2, -1, 0][frame]
    elif pose == "windup":
        bob = [0, -1, -1, -1][frame]
    elif pose == "slam":
        bob = [-2, 0, 1, 3, 2][frame]
    elif pose == "charge":
        bob = WALK_BOB[CHARGE_STEPS[frame]] - 1
        stride = [6, 2, -6, -2][frame]
        sway = [-4, -3, -4, -3][frame]
    shake = 1 if pose == "windup" and frame == 3 else 0
    cx = 30 + shake

    # cape trailing behind (to the left)
    pts = [(cx - 2, 22 + bob), (cx + 4, 22 + bob), (cx - 2, 57), (cx - 6 + sway, 59), (cx - 10 + sway, 56), (cx - 14 + sway, 59), (cx - 15 + sway, 54)]
    cape.poly(pts, lambda x, y: CAPE[2] if (x + y // 6) % 5 else CAPE[3])

    # legs: far one darker
    for layer, offset, darker in ((far, -stride, True), (legs, stride, False)):
        lx = cx - 2 + offset
        ramp = LEATHER[4] if darker else LEATHER[3]
        greave = IRON[3] if darker else IRON[2]
        layer.rect(lx, 46 + bob, lx + 6, 52, ramp)
        layer.rect(lx, 51, lx + 6, 56, greave)
        layer.rect(lx - 1, 50, lx + 7, 51, IRON[3] if not darker else IRON[4])
        layer.rect(lx - 1, 56, lx + 9, 60, LEATHER[3] if not darker else LEATHER[4])
        layer.rect(lx + 7, 58, lx + 9, 60, IRON[2] if not darker else IRON[3])   # toe cap

    skirt(legs, cx + 1, bob, half=8)
    body.blob(cx + 1, 32 + bob, 10, 11, 10, IRON)
    body.rect(cx - 8, 40 + bob, cx + 10, 43 + bob, LEATHER[3])
    body.rect(cx - 8, 40 + bob, cx + 10, 40 + bob, LEATHER[1])
    for y in (30, 36):
        for x in range(cx - 7, cx + 10):
            if body.get(x, y + bob)[3]:
                body.px(x, y + bob, IRON[3])
    body.px(cx + 6, 27 + bob, IRON[0])
    body.px(cx + 7, 34 + bob, IRON[0])

    shoulder = (cx + 1, 28 + bob)
    swing_from = None
    if pose in ("windup", "slam", "charge"):
        # (hand angle around the shoulder, axe direction) for each frame; 0 = forward, 90 = up
        keys = {"windup": [(-50, 80), (20, 110), (95, 150), (110, 160)],
                "slam": [(115, 150), (60, 75), (0, 5), (-45, -65), (-40, -60)],
                "charge": [(108, 158), (111, 161), (108, 158), (111, 161)]}[pose]
        arm_angle, axe_dir = keys[frame]
        rad = math.radians(arm_angle)
        hand = (int(round(shoulder[0] + math.cos(rad) * 13)), int(round(shoulder[1] - math.sin(rad) * 13)))
        if pose == "slam" and frame in (1, 2):
            swing_from = keys[frame - 1][1]
    else:
        swing = 0 if pose == "idle" else [-2, -1, 0, 2, 1, 0][frame]
        hand = (cx + 13 + swing, 43 + bob)
        axe_dir = 90
    arm(arms, shoulder, hand)
    pauldron(shoulders, cx + 1, 24 + bob, mirror=True)
    fur_collar(shoulders, cx + 1, 21 + bob, width=10)

    # head in profile, facing right
    hx, hy = cx + 3, 12 + bob
    head.blob(hx, hy + 1, 8, 8, 9, SKIN)
    head.blob(hx + 6, hy + 5, 4, 3, 3, SKIN)                       # jutting jaw
    for i in range(5):
        head.px(hx + 2 + i, hy - 1 + i // 2, SKIN[4])                # brow
    head.rect(hx + 4, hy + 1, hx + 6, hy + 2, EYE)
    head.px(hx + 6, hy + 1, EYE_GLOW)
    head.rect(hx + 5, hy + 8, hx + 10, hy + 8, (60, 26, 34))
    head.rect(hx + 8, hy + 4, hx + 9, hy + 7, BONE[1])              # tusk
    head.px(hx + 8, hy + 4, BONE[0])
    head.blob(hx - 1, hy - 3, 10, 7, 3, IRON, only=lambda x, y: y <= hy - 1)
    head.rect(hx - 10, hy - 2, hx + 8, hy - 1, IRON[3])
    for rx in (hx - 7, hx - 2, hx + 4):
        head.px(rx, hy - 2, IRON[0])
    horn(horns, (hx - 6, hy - 4), (hx - 20, hy - 11), (hx - 16, hy - 2))

    fist(hands, *hand)
    axe_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    paste_rotated(axe_img, AXE, (AXE_HALF, AXE_GRIP), axe_dir, hand)

    order = [cape, far, legs, body, shoulders, head, horns, arms, axe_img, hands]
    im = stack(order)
    if swing_from is not None:
        smear(im, hand, AXE_GRIP - 6, swing_from, axe_dir)
    if pose == "charge":
        speed_lines(im, cx - 13, frame)
        _kick_dust(im, cx - 10 - stride // 2, frame, behind=True)
    if pose == "slam" and frame >= 3:
        rad = math.radians(axe_dir)
        head_x = int(hand[0] + math.cos(rad) * (AXE_GRIP - 8))
        _dust(im, min(SIZE - 18, head_x), 1.0 if frame == 3 else 0.5)
    return im


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
        "Slam": [make("slam", f) for f in range(5)],
        "Charge": [make("charge", f) for f in range(4)],
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
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save("orc_preview.png")
    print("preview written")
