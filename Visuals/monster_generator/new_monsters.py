"""Bat, Ghost, Mimic and Necromancer: 32x32 like the other monsters (same outline colour and
4-tone shading), drawn from shaded shapes instead of hand-typed grids. Each returns finished
PIL images per view: {"Down": (idle, walk), "Up": ..., "Side": ...}; monsters.py registers them.
Run for a preview: python new_monsters.py"""
import math
from PIL import Image

S = 32
K = (24, 18, 26)


class L:
    """A 32x32 drawing layer; outlined automatically when stacked."""
    def __init__(self):
        self.im = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S:
            self.im.putpixel((x, y), tuple(c[:3]) + ((c[3],) if len(c) == 4 else (255,)))

    def get(self, x, y):
        return self.im.getpixel((x, y)) if 0 <= x < S and 0 <= y < S else (0, 0, 0, 0)

    def blob(self, cx, cy, rx, ry_top, ry_bottom, ramp, light=(-0.55, -0.85), only=None):
        for y in range(S):
            for x in range(S):
                ry = ry_top if y + 0.5 < cy else ry_bottom
                if rx <= 0 or ry <= 0:
                    continue
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = nx * nx + ny * ny
                if d > 1 or (only and not only(x, y)):
                    continue
                t = nx * light[0] + ny * light[1] - (0.35 if d > 0.8 else 0)
                self.px(x, y, pick(ramp, t))

    def poly(self, pts, c):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if inside(x + 0.5, y + 0.5, pts):
                    self.px(x, y, c(x, y) if callable(c) else c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)


def pick(ramp, t):
    if t > 0.55:
        return ramp[0]
    if t > 0.18:
        return ramp[1]
    if t > -0.22:
        return ramp[2]
    if t > -0.6:
        return ramp[3]
    return ramp[4]


def inside(x, y, pts):
    res, j = False, len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            res = not res
        j = i
    return res


def outlined(layer):
    out = layer.im.copy()
    for y in range(S):
        for x in range(S):
            if layer.get(x, y)[3] >= 200:
                continue
            if any(layer.get(x + dx, y + dy)[3] >= 200 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), K + (255,))
    return out


def stack(layers, shadow=None, alpha=255):
    """shadow: (center x, half width) of a soft floor shadow on rows 29-30."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    if shadow:
        cx, hw = shadow
        for y, w in ((29, hw), (30, max(1, hw - 2))):
            for x in range(int(cx - w), int(cx + w)):
                if 0 <= x < S:
                    im.putpixel((x, y), (20, 16, 24, 90))
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for layer in layers:
        body.alpha_composite(outlined(layer) if isinstance(layer, L) else layer)
    if alpha < 255:
        r, g, b, a = body.split()
        a = a.point(lambda v: v * alpha // 255)
        body = Image.merge("RGBA", (r, g, b, a))
    im.alpha_composite(body)
    return im


def mirror_x(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


# =====================================================================
# BAT - purple, big ears, leathery wings, red eyes; always flapping, hovers over its shadow
# =====================================================================
BAT = [(168, 128, 206), (134, 94, 176), (100, 66, 140), (70, 44, 104), (46, 28, 72)]
WING = [(120, 84, 150), (96, 62, 124), (74, 46, 100), (54, 32, 76), (38, 22, 56)]
EYE_RED = (255, 70, 70)

# wing tip height relative to the shoulder for each flap pose: up, mid, down, mid
FLAP = [-7, -2, 4, -2]


def bat_wing(layer, sx, sy, tip_dy, side):
    """One wing from the shoulder outwards (side = -1 left, +1 right) with scalloped edge."""
    tip = (sx + side * 12, sy + tip_dy)
    mid = (sx + side * 7, sy + tip_dy * 0.6 - 2)
    pts = [(sx, sy - 1), mid, tip, (sx + side * 10, sy + tip_dy + 3), (sx + side * 7, sy + tip_dy * 0.5 + 3),
           (sx + side * 4, sy + 4), (sx, sy + 3)]
    layer.poly(pts, lambda x, y: pick(WING, -0.1 - abs(x - sx) / 16))
    layer.line(sx, sy - 1, tip[0], tip[1], BAT[3])               # wing bone
    layer.line(mid[0], mid[1], sx + side * 7, sy + tip_dy * 0.5 + 3, BAT[3])


def bat_front(frame, back=False, flying_y=0):
    wings, body = L(), L()
    tip = FLAP[frame % 4]
    cy = 14 + flying_y + (1 if tip > 0 else 0)
    for side in (-1, 1):
        bat_wing(wings, 16 + side * 3, cy - 1, tip, side)
    body.blob(16, cy, 5, 5, 5, BAT)
    for side in (-1, 1):                                          # ears
        body.poly([(16 + side * 2, cy - 4), (16 + side * 5, cy - 10), (16 + side * 5.5, cy - 3)], lambda x, y: BAT[2])
        if not back:
            body.px(16 + side * 4, cy - 6, (220, 140, 170))
    if not back:
        body.px(14, cy - 1, EYE_RED)
        body.px(18, cy - 1, EYE_RED)
        body.px(14, cy - 2, (255, 200, 200))
        body.px(18, cy - 2, (255, 200, 200))
        body.px(15, cy + 2, (250, 250, 240))                      # fangs
        body.px(17, cy + 2, (250, 250, 240))
    body.px(15, cy + 5, BAT[3])                                   # little feet
    body.px(17, cy + 5, BAT[3])
    order = [wings, body] if not back else [body, wings]
    shadow_w = 6 - abs(tip) // 4
    return stack(order, shadow=(16, shadow_w))


def bat_side(frame, flying_y=0):
    far, body, near = L(), L(), L()
    tip = FLAP[frame % 4]
    cy = 14 + flying_y + (1 if tip > 0 else 0)
    # far wing peeks out above/behind, near wing sweeps over the body
    far.poly([(15, cy - 2), (10, cy - 2 + tip * 0.8 - 3), (6, cy + tip), (11, cy + 2)], lambda x, y: WING[3])
    body.blob(16, cy, 5, 4, 5, BAT, light=(0.3, -0.8))
    body.poly([(17, cy - 3), (18, cy - 10), (20, cy - 2)], lambda x, y: BAT[2])     # ear
    body.blob(20, cy, 2, 2, 2, BAT)                                                  # snout
    body.px(19, cy - 1, EYE_RED)
    body.px(21, cy + 2, (250, 250, 240))
    near.poly([(16, cy - 1), (11, cy - 1 + tip * 0.6 - 2), (3, cy + tip), (7, cy + tip + 3), (10, cy + 3), (15, cy + 3)],
              lambda x, y: pick(WING, -0.1 - abs(x - 16) / 14))
    near.line(16, cy - 1, 3, cy + tip, BAT[3])
    return stack([far, body, near], shadow=(16, 5 - abs(tip) // 4))


def bat_frames():
    bob = [0, -1, 0, 1]
    views = {}
    for view in ("Down", "Up"):
        idle = [bat_front(f, view == "Up", bob[f]) for f in range(4)]
        walk = [bat_front(f, view == "Up", bob[(f + 1) % 4] - 1) for f in range(4)]
        views[view] = (idle, walk)
    views["Side"] = ([bat_side(f, bob[f]) for f in range(4)], [bat_side(f, bob[(f + 1) % 4] - 1) for f in range(4)])
    return views


# =====================================================================
# GHOST - pale floating sheet with hollow eyes and an "O" mouth, wispy waving tail
# =====================================================================
GHOST = [(240, 246, 255), (206, 220, 244), (162, 182, 222), (118, 136, 186), (80, 92, 140)]
HOLLOW = (34, 30, 56)


def ghost_body(layer, cx, top, wave, tail_lean=0):
    layer.blob(cx, top + 8, 8, 8, 6, GHOST)                     # round head / shoulders
    bottom = top + 22
    pts = [(cx - 8, top + 8), (cx + 8, top + 8)]
    for i in range(6, -1, -1):                                  # wavy tail
        x = cx - 8 + i * 16 / 6 + tail_lean * (bottom - top - 8) / 14
        dip = 2 if (i + wave) % 2 == 0 else -1
        pts.append((x, bottom + dip))
    layer.poly(pts, lambda x, y: pick(GHOST, 0.3 - (x - cx + 4) / 12 - (y - top - 10) / 18))


def ghost_front(frame, back=False, walk=False):
    body, face, arms = L(), L(), L()
    bob = [0, -1, -1, 0][frame]
    top = 4 + bob
    lean = [-1, 0, 1, 0][frame] if walk else 0
    ghost_body(body, 16, top, frame, lean)
    for side in (-1, 1):                                         # stubby arms reaching out
        ax = 16 + side * 9
        arms.blob(ax, top + 13 + (frame % 2 if walk else 0), 2.5, 2, 2, GHOST)
    if not back:
        for ex in (13, 19):
            face.blob(ex, top + 9, 1.8, 2.5, 2.5, [HOLLOW] * 5)
        face.blob(16, top + 14, 1.5, 1.8, 1.8, [HOLLOW] * 5)
    return stack([arms, body, face], shadow=(16, 5), alpha=225)


def ghost_side(frame, walk=False):
    body, face, arm = L(), L(), L()
    bob = [0, -1, -1, 0][frame]
    top = 4 + bob
    body.blob(17, top + 8, 7, 8, 6, GHOST, light=(0.3, -0.85))
    bottom = top + 22
    trail = 3 + (frame % 2 if walk else 0)
    pts = [(10, top + 9), (24, top + 9), (22, bottom - 2), (18, bottom + (frame % 2)), (14, bottom - 1), (10 - trail, bottom + 1 - (frame % 2)),
           (9 - trail, bottom - 4)]
    body.poly(pts, lambda x, y: pick(GHOST, 0.3 - (24 - x) / 14 - (y - top - 10) / 18))
    face.blob(21, top + 9, 1.5, 2.5, 2.5, [HOLLOW] * 5)
    face.blob(23, top + 14, 1, 1.5, 1.5, [HOLLOW] * 5)
    arm.blob(22, top + 14 + (frame % 2 if walk else 0), 2.5, 2, 2, GHOST)
    return stack([body, arm, face], shadow=(16, 5), alpha=225)


def ghost_frames():
    return {
        "Down": ([ghost_front(f) for f in range(4)], [ghost_front(f, walk=True) for f in range(4)]),
        "Up": ([ghost_front(f, back=True) for f in range(4)], [ghost_front(f, back=True, walk=True) for f in range(4)]),
        "Side": ([ghost_side(f) for f in range(4)], [ghost_side(f, walk=True) for f in range(4)]),
    }


# =====================================================================
# MIMIC - a clay pot with a toothy grin across its belly, little eyes on the rim, a lolling
# tongue and stubby feet. Hops like a slime (6-frame hop) and snaps its jaws.
# =====================================================================
CLAY = [(226, 158, 104), (196, 122, 76), (152, 88, 56), (108, 60, 42), (72, 40, 32)]
MOUTH = (70, 16, 26)
TONGUE = (226, 92, 120)
TOOTH = (250, 246, 230)


def mimic_pot(layer, face, cx, base, squash=0.0, open_=0.5, back=False, side=False):
    """base: y of its feet. squash > 0 = wider + lower, < 0 = stretched tall. open_: 0 shut .. 1 wide."""
    h = 17 * (1 - squash * 0.25)
    w = 8 * (1 + squash * 0.25)
    cy = base - h * 0.48
    layer.blob(cx, cy, w, h * 0.55, h * 0.45, CLAY, light=(0.3, -0.8) if side else (-0.55, -0.85))
    rim_y = base - h + 1
    layer.rect(cx - w * 0.55, rim_y - 1, cx + w * 0.55, rim_y + 1, CLAY[1])     # neck + rim
    layer.rect(cx - w * 0.65, rim_y - 2, cx + w * 0.65, rim_y - 2, CLAY[0])
    for fx in ((-4, 3) if not side else (-2, 3)):                               # stubby feet
        layer.rect(cx + fx - 1, base - 1, cx + fx + 1, base, CLAY[3])
    if back:
        for y in range(int(cy - 3), int(cy + 4)):                               # a crack down the back
            layer.px(cx + (1 if y % 3 else 0), y, CLAY[4])
        return
    mx = cx + (3 if side else 0)
    mw = w * (0.55 if side else 0.85)
    gap = 1 + int(round(open_ * 4))
    my = cy + 1
    face.rect(mx - mw, my - gap // 2, mx + mw, my + (gap - gap // 2), MOUTH)    # mouth
    for x in range(int(mx - mw), int(mx + mw) + 1, 2):                          # teeth top and bottom
        face.px(x, my - gap // 2, TOOTH)
        face.px(x + 1, my + (gap - gap // 2), TOOTH)
    if open_ > 0.4:                                                              # lolling tongue
        face.rect(mx - 1, my + 1, mx + 1, my + gap // 2 + 2, TONGUE)
    for ex in ((cx - 3, cx + 3) if not side else (cx + 4,)):                    # beady eyes on the rim
        face.px(ex, rim_y + 2, (255, 230, 90))
        face.px(ex, rim_y + 3, K)


def mimic_frames():
    # hop: crouch, launch, rise, apex, fall, splat (+ jaws snap open as it leaps, shut on landing)
    hop = [(0.35, 0, 0.2), (-0.3, 0, 0.6), (-0.1, 5, 1.0), (0.0, 8, 0.9), (-0.2, 3, 0.4), (0.35, 0, 0.0)]
    idle = [(0.0, 0, 0.1), (0.05, 0, 0.3), (0.0, 0, 0.1), (-0.05, 0, 0.0)]

    def frame(sq, lift, op, back=False, side=False):
        body, face = L(), L()
        mimic_pot(body, face, 16, 28 - lift, sq, op, back, side)
        return stack([body, face], shadow=(16, 7 - lift // 2))

    views = {}
    for view in VIEWS:
        back, side = view == "Up", view == "Side"
        views[view] = ([frame(*p, back, side) for p in idle], [frame(*p, back, side) for p in hop])
    return views


# =====================================================================
# NECROMANCER - a smaller, green-robed cousin of the Ancient Lich: hood, bony face with green
# eyes, bone staff topped with a little skull in green fire
# =====================================================================
NROBE = [(88, 128, 92), (64, 100, 70), (46, 76, 54), (32, 54, 40), (22, 36, 28)]
NBONE = [(236, 232, 210), (204, 198, 172), (160, 154, 132), (116, 110, 96), (78, 74, 66)]
NGLOW = (120, 255, 140)
WOOD = [(150, 112, 80), (120, 86, 62), (92, 64, 46), (66, 46, 34), (44, 30, 24)]


def necro_staff(layer, x, top, bottom, flame):
    layer.rect(x, top + 4, x, bottom, WOOD[2])
    layer.blob(x, top + 2, 2.2, 2, 2, NBONE)                    # little skull
    layer.px(x - 1, top + 2, K)
    layer.px(x + 1, top + 2, K)
    for i, (dx, dy) in enumerate(((0, -1), (-1, -2), (1, -2), (0, -3), (0, -4))[:2 + flame]):
        layer.px(x + dx, top + dy, NGLOW if i % 2 else (210, 255, 210))


def necro_front(frame, back=False, walk=False):
    robe, staff, head, hands = L(), L(), L(), L()
    bob = ([0, 0, 1, 1] if not walk else [0, -1, 0, -1])[frame]
    sway = [0, 1, 0, -1][frame] if walk else 0
    # robe (wider at the hem, feet peeking out when walking)
    pts = [(12, 13 + bob), (20, 13 + bob), (23 + sway, 28), (9 + sway, 28)]
    robe.poly(pts, lambda x, y: pick(NROBE, -0.1 - abs(x - 16) / 10 - (0.3 if (x + y) % 5 == 0 else 0)))
    if walk:
        lift = frame % 2
        robe.rect(12, 28 - (lift if frame < 2 else 0), 14, 29 - (lift if frame < 2 else 0), NBONE[3])
        robe.rect(18, 28 - (lift if frame >= 2 else 0), 20, 29 - (lift if frame >= 2 else 0), NBONE[3])
    if not back:
        robe.rect(15, 15 + bob, 16, 27, NROBE[4])                # robe opening
        robe.px(15, 19 + bob, NGLOW)                             # glowing rune
        robe.px(16, 23 + bob, NGLOW)
    # hood with a bony face
    head.blob(16, 9 + bob, 6, 6, 5, NROBE)
    if not back:
        head.blob(16, 10 + bob, 3.5, 3.5, 3.5, [(16, 12, 20)] * 5)
        head.blob(16, 10.5 + bob, 2.5, 2.5, 2.5, NBONE, light=(-0.2, 0.9))
        head.px(15, 10 + bob, NGLOW)
        head.px(17, 10 + bob, NGLOW)
    else:
        head.poly([(14, 4 + bob), (16, 1 + bob), (18, 4 + bob)], lambda x, y: NROBE[2])
    # staff in its right hand (viewer's left), other hand raised a little
    sx = 9 if not back else 23
    staff_top = 6 + bob + (frame % 2 if walk else 0)
    necro_staff(staff, sx, staff_top, 27, frame % 3)
    hands.blob(sx, 17 + bob, 1.6, 1.5, 1.5, NBONE)
    hx = 23 if not back else 9
    hands.blob(hx, 18 + bob - (1 if frame in (1, 2) else 0), 1.6, 1.5, 1.5, NBONE)
    order = [robe, head, staff, hands] if not back else [staff, robe, head, hands]
    return stack(order, shadow=(16, 6))


def necro_side(frame, walk=False):
    robe, staff, head, hand = L(), L(), L(), L()
    bob = ([0, 0, 1, 1] if not walk else [0, -1, 0, -1])[frame]
    trail = [0, -1, -2, -1][frame] if walk else 0
    pts = [(13, 13 + bob), (19, 13 + bob), (21, 28), (17, 28), (14, 27), (10 + trail, 28), (11 + trail, 22)]
    robe.poly(pts, lambda x, y: pick(NROBE, 0.1 - (21 - x) / 12 - (0.3 if (x + y) % 5 == 0 else 0)))
    if walk:
        step = [2, 0, -2, 0][frame]
        robe.rect(16 + step, 28, 18 + step, 29, NBONE[3])
    head.blob(16, 9 + bob, 5.5, 6, 5, NROBE, light=(0.3, -0.85))
    head.poly([(12, 5 + bob), (9, 9 + bob), (12, 11 + bob)], lambda x, y: NROBE[3])      # hood point
    head.blob(19, 10 + bob, 2.5, 3.5, 3.5, [(16, 12, 20)] * 5)
    head.blob(19.5, 10.5 + bob, 1.8, 2.5, 2.5, NBONE, light=(0.6, 0.6))
    head.px(20, 10 + bob, NGLOW)
    sx = 22
    staff_top = 6 + bob + (frame % 2 if walk else 0)
    necro_staff(staff, sx, staff_top, 27, frame % 3)
    hand.blob(sx, 17 + bob, 1.6, 1.5, 1.5, NBONE)
    return stack([robe, head, staff, hand], shadow=(16, 6))


def necro_frames():
    return {
        "Down": ([necro_front(f) for f in range(4)], [necro_front(f, walk=True) for f in range(4)]),
        "Up": ([necro_front(f, back=True) for f in range(4)], [necro_front(f, back=True, walk=True) for f in range(4)]),
        "Side": ([necro_side(f) for f in range(4)], [necro_side(f, walk=True) for f in range(4)]),
    }


# =====================================================================
# SPIRIT - what necromancers summon: a floating skull wreathed in green soul-fire, trailing wisps.
# Can't be killed; it fades when its necromancer dies.
# =====================================================================
SOUL = [(214, 255, 210), (140, 246, 150), (80, 210, 110), (40, 150, 80), (24, 96, 56)]
SKULL = [(236, 234, 220), (206, 202, 186), (164, 160, 146), (118, 114, 104), (80, 76, 70)]


def soul_flames(layer, cx, top, frame, back=False):
    """Licking green flames rising off the skull (the shape changes every frame)."""
    for i, dx in enumerate((-5, -3, -1, 1, 3, 5)):
        h = 8 + ((i * 3 + frame * 2) % 5) + (3 if dx in (-1, 1) else 0)
        sway = ((frame + i) % 3) - 1
        layer.poly([(cx + dx - 1.6, top + 6), (cx + dx + sway, top + 6 - h), (cx + dx + 1.6, top + 6)],
                   lambda x, y, h=h: pick(SOUL, 0.7 - (top + 6 - y) / h * 1.6))


def wisp_tail(layer, cx, top, frame, lean=0):
    pts = [(cx - 5, top + 12), (cx + 5, top + 12)]
    for k in range(5):
        pts.append((cx + 4 - k * 2 + lean + ((frame + k) % 2), top + 20 + k * 1.5 - (k % 2) * 2))
    pts.append((cx - 5, top + 15))
    layer.poly(pts, lambda x, y: pick(SOUL, 0.2 - (y - top - 12) / 8))


def spirit_front(frame, back=False):
    fire, tail, skull, glow = L(), L(), L(), L()
    bob = [0, -1, -2, -1][frame]
    top = 6 + bob
    wisp_tail(tail, 16, top, frame)
    soul_flames(fire, 16, top - 1, frame)
    skull.blob(16, top + 8, 6, 6, 5, SKULL)
    if not back:
        skull.blob(16, top + 14, 3.5, 2, 2, SKULL)                   # jaw
        for ex in (13, 19):                                           # burning eye sockets
            skull.blob(ex, top + 9, 1.8, 1.8, 1.8, [(18, 30, 22)] * 5)
            skull.px(ex, top + 9, SOUL[0])
            skull.px(ex, top + 8, SOUL[1])
        skull.px(16, top + 12, (18, 30, 22))
        for tx in (14, 16, 18):
            skull.px(tx, top + 14, (18, 30, 22))
    else:
        skull.px(15, top + 6, SKULL[3])                               # cracks on the back of the skull
        skull.px(16, top + 7, SKULL[3])
        skull.px(16, top + 8, SKULL[3])
    return stack([tail, fire, skull, glow], shadow=(16, 4), alpha=240)


def spirit_side(frame):
    fire, tail, skull = L(), L(), L()
    bob = [0, -1, -2, -1][frame]
    top = 6 + bob
    wisp_tail(tail, 14, top, frame, lean=-4)
    soul_flames(fire, 15, top - 1, frame)
    skull.blob(16, top + 8, 6, 6, 5, SKULL, light=(0.3, -0.85))
    skull.blob(19, top + 13, 3, 2, 2, SKULL)
    skull.blob(19, top + 9, 1.8, 1.8, 1.8, [(18, 30, 22)] * 5)
    skull.px(19, top + 9, SOUL[0])
    skull.px(21, top + 12, (18, 30, 22))
    return stack([tail, fire, skull], shadow=(16, 4), alpha=240)


def spirit_frames():
    return {
        "Down": ([spirit_front(f) for f in range(4)], [spirit_front(f) for f in range(4)]),
        "Up": ([spirit_front(f, True) for f in range(4)], [spirit_front(f, True) for f in range(4)]),
        "Side": ([spirit_side(f) for f in range(4)], [spirit_side(f) for f in range(4)]),
    }


VIEWS = ("Down", "Up", "Side")
NEW = {"Bat": bat_frames, "Ghost": ghost_frames, "Mimic": mimic_frames, "Necromancer": necro_frames, "Spirit": spirit_frames}

if __name__ == "__main__":
    rows = [(n, v) for n in NEW for v in VIEWS]
    preview = Image.new("RGBA", (10 * 34 + 8, len(rows) * 34), (88, 86, 98, 255))
    for r, (name, view) in enumerate(rows):
        idle, walk = NEW[name]()[view]
        for c, im in enumerate(idle + walk):
            preview.alpha_composite(im, (c * 34 + (8 if c >= 4 else 0), r * 34))
    preview.resize((preview.width * 3, preview.height * 3), Image.NEAREST).save("new_monsters_preview.png")
    print("preview written")
