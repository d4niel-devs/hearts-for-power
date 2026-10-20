"""Hand-authored 32x32 pixel-art monsters in the same style as the knight.
Every monster has three views - Down (front), Up (back), Side (facing right; flip in-game for left) -
each with an idle (4 frames) and a walk (4 frames).
Run this for a preview, then unity_export.py to push everything into Unity."""
from PIL import Image

OUTLINE = (24, 18, 26)
VIEWS = ("Down", "Up", "Side")


# ---------------------------------------------------------------- helpers
def mirror(half):
    assert len(half) == 16, (len(half), half)
    return half + half[::-1]


def M(rows):
    return [mirror(r) for r in rows]


def flip_rows(rows):
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.')[::-1] for r in rows]


def remap(rows, mapping):
    return [''.join(mapping.get(c, c) for c in r) for r in rows]


def stamp(g, rows, x, y):
    for j, r in enumerate(rows):
        assert len(r) <= 32, (len(r), r)
        for i, c in enumerate(r):
            if c != '.' and 0 <= y + j < 32 and 0 <= x + i < 32:
                g[y + j][x + i] = c
    return g


def build(parts):
    """parts: list of (rows, x, y), stamped back to front"""
    g = [['.'] * 32 for _ in range(32)]
    for rows, x, y in parts:
        stamp(g, rows, x, y)
    return g


def lift(rows, side):
    """Raise one half of a symmetric leg block by 1px (a lifted foot). side: 'L' or 'R' (viewer's)."""
    rows = [r.ljust(32, '.') for r in rows]
    out = [list(r) for r in rows]
    cols = range(0, 16) if side == 'L' else range(16, 32)
    for y in range(len(rows)):
        for x in cols:
            out[y][x] = rows[y + 1][x] if y + 1 < len(rows) else '.'
    return [''.join(r) for r in out]


def to_img(g, pal):
    if isinstance(g, Image.Image):      # already drawn (new_monsters.py)
        return g
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            if c == '.':
                continue
            col = OUTLINE if c == 'K' else pal[c]
            im.putpixel((x, y), col if len(col) == 4 else col + (255,))
    return im


def front_cycle(head, head_y, body, body_y, legs, legs_y, hands=None, behind=None, front=None):
    """Down/Up view: idle = breathing head dip, walk = alternating lifted feet + arm swing + bob.
    hands: (rows, left_x, right_x, y) - rows are for the viewer-left hand, mirrored for the right."""
    def f(legs_rows, dy=0, hdy=0, hl=0, hr=0):
        parts = []
        if behind:
            parts.append((behind[0], behind[1], behind[2] + dy))
        parts += [(legs_rows, 0, legs_y), (body, 0, body_y + dy), (head, 0, head_y + dy + hdy)]
        if front:
            parts.append((front[0], front[1], front[2] + dy))
        if hands:
            rows, lx, rx, hy = hands
            parts += [(rows, lx, hy + dy + hl), (flip_rows(rows), rx, hy + dy + hr)]
        return build(parts)
    idle = [f(legs), f(legs), f(legs, hdy=1), f(legs, hdy=1)]
    walk = [f(lift(legs, 'R'), hl=-1, hr=1), f(legs, dy=-1), f(lift(legs, 'L'), hl=1, hr=-1), f(legs, dy=-1)]
    return idle, walk


def side_cycle(head, head_xy, body, body_xy, arm_fwd, arm_back, legs_stand, legs_stride, legs_xy, behind=None):
    hx, hy = head_xy
    bx, by = body_xy
    lx, ly = legs_xy

    def f(b, legs, dy=0, hdy=0):
        parts = []
        if behind:
            rows, x, y = behind
            parts.append((rows, x, y + dy))
        parts += [(legs, lx, ly), (b, bx, by + dy), (head, hx, hy + dy + hdy)]
        return build(parts)
    idle = [f(body, legs_stand), f(body, legs_stand), f(body, legs_stand, hdy=1), f(body, legs_stand, hdy=1)]
    walk = [f(arm_back, legs_stride), f(body, legs_stand, dy=-1), f(arm_fwd, legs_stride), f(body, legs_stand, dy=-1)]
    return idle, walk


MONSTERS = {}

# =====================================================================
# Knight body templates (shared by the human-shaped monsters)
# =====================================================================
KN_FRONT_BODY = M([
"........KKKKKKKK",
".......KGGWWWWWW",
"......KGGKGWWWWW",
"......KGgKGWWWWW",
"......KggKgGGGGG",
"......KKKKbbbbbY",
])
KN_BACK_BODY = M([
"........KKKKKKKK",
".......KGGWWGGGG",
"......KGGKGWGGGg",
"......KGgKgGGGGg",
"......KggKggGGGg",
"......KKKKbbbbbb",
])
KN_FRONT_LEGS = M([
".........KgGGGGG",
".........KgGGgKK",
".........KgggK..",
".........KKKKK..",
])
KN_HAND = ["KSK", "KsK", ".K."]
KN_SIDE_BODY = [
"..........KKKKKKKKKKKK",
"..........KgGGGWWWWWGK",
".........KgGGGKKWWWWGK",
".........KgGGKSSKWWWGK",
".........KgGGKSSKGGGgK",
"..........KbbbKKbbbbYK",
]
KN_SIDE_ARM_BACK = KN_SIDE_BODY[:2] + [
".........KgGGKKWWWWWGK",
"........KSSKgGWWWWWGK",
"........KSSKgGGGGGGgK",
] + KN_SIDE_BODY[5:]
KN_SIDE_ARM_FWD = KN_SIDE_BODY[:2] + [
".........KgGGGGWWWWKK",
".........KgGGGWWWWKSSK",
".........KgGGGGGGgKSSK",
] + KN_SIDE_BODY[5:]
KN_SIDE_LEGS = [
"...........KgGGGGGgK",
"...........KgGgKgGGK",
"...........KggKKggGK",
"...........KKKKKKKKK",
]
KN_SIDE_LEGS_STRIDE = [
"...........KgGGGGGgK",
"..........KgGKKKKgGGK",
".........KggK....KggGK",
".........KKKK....KKKKK",
]

# =====================================================================
# SLIME - blue blob; walk = hop (crouch, launch, airborne, land)
# =====================================================================
SLIME_PAL = {'1': (206, 236, 255), '2': (96, 166, 246), '3': (56, 110, 210), '4': (36, 68, 150),
             'w': (255, 255, 255), 'e': (16, 22, 48), 'z': (20, 16, 24, 110)}
SLIME_SIDE = [
"..........KKKKKKKKK",
"........KK112222222KK",
".......K1112222222222K",
"......K111222222222222K",
".....K11222222222222222K",
".....K122222222Kw2Kw222K",
"....K1222222222KeKKe2222K",
"....K2222222222KKKKK2222K",
"....K3222222222222222222K",
"....K33222222222222222233K",
".....K332222222222222223K",
"......KK3333333333333333K",
"........KKKKKKKKKKKKKKKK",
]
SLIME_SIDE_SQUASH = [
".........KKKKKKKKKK",
".......KK1122222222KK",
".....KK1112222222222222KK",
"....K11122222222Kw2Kw22222K",
"...K1222222222222KeKKe222222K",
"...K22222222222222KKKKK222222K",
"...K322222222222222222222222K",
"....K3322222222222222222223K",
".....KK33333333333333333333K",
".......KKKKKKKKKKKKKKKKKKKK",
]
SLIME_SIDE_STRETCH = [
"...........KKKKKKK",
".........KK1122222KK",
"........K11122222222K",
".......K1112222222222K",
"......K112222222222222K",
"......K12222222Kw2Kw22K",
"......K22222222KeKKe22K",
"......K22222222KKKKK22K",
"......K3222222222222222K",
"......K3222222222222223K",
"......K3322222222222233K",
".......K33222222222233K",
"........KK3333333333K",
"..........KKKKKKKKKK",
]
SLIME_FRONT_HALF = [
"..........KKKKKK",
"........KK111222",
"......KK11122222",
".....K1112222222",
"....K11222222222",
"....K1222222Kw22",
"...K12222222KK22",
"...K222222222222",
"...K322222222222",
"...K332222222222",
"....K33322222222",
".....KK333333333",
".......KKKKKKKKK",
]
SLIME_BACK_HALF = [r.replace('Kw', '22').replace('KK22', '2222') if i in (5, 6) else r
                   for i, r in enumerate(SLIME_FRONT_HALF)]


def widen(half_rows, n):
    """Squash: push the left half outwards by n (the mirror does the right)."""
    return [r[n:] + r[-1] * n for r in half_rows]


def narrow(half_rows, n):
    return ['.' * n + r[:-n] for r in half_rows]


def shadow_rows(width, center=16):
    """A soft ground shadow (2 rows), drawn under the slime; narrower the higher it jumps."""
    rows = []
    for w in (width, max(2, width - 4)):
        left = int(center - w / 2)
        rows.append('.' * left + 'z' * w)
    return rows


def slime_set(normal, squash, stretch, soft, x_normal=3, x_squash=1, x_stretch=3):
    """Idle: gentle squish. Walk (hop, 6 frames): crouch, launch, rise, apex, fall, splat.
    The shadow stays on the floor (row 29) while the body leaves the ground."""
    def frame(body, x, y, shadow_width):
        return build([(shadow_rows(shadow_width), 0, 29), (body, x, y)])

    def top_for(rows, bottom):
        return bottom - len(rows) + 1

    ground = 29
    idle = [frame(normal, x_normal, top_for(normal, ground), 22), frame(normal, x_normal, top_for(normal, ground), 22),
            frame(soft, x_normal, top_for(soft, ground), 22), frame(soft, x_normal, top_for(soft, ground), 22)]
    walk = [frame(squash, x_squash, top_for(squash, ground), 26),        # crouch
            frame(stretch, x_stretch, top_for(stretch, ground), 18),     # launch (still touching the floor)
            frame(normal, x_normal, top_for(normal, ground - 6), 14),    # rising
            frame(soft, x_normal, top_for(soft, ground - 9), 12),        # apex
            frame(stretch, x_stretch, top_for(stretch, ground - 3), 16), # falling
            frame(squash, x_squash, top_for(squash, ground), 26)]        # splat
    return idle, walk


def slime_frames():
    def sym(half):
        n = M(half)
        squash = M(widen(half[:3] + half[5:], 2))
        stretch = M(narrow(half[:7] + half[6:8] + half[7:], 1))
        soft = M(half[:3] + half[4:])
        return slime_set(n, squash, stretch, soft, 0, 0, 0)
    side_soft = SLIME_SIDE[:3] + SLIME_SIDE[4:]
    return {
        "Down": sym(SLIME_FRONT_HALF),
        "Up": sym(SLIME_BACK_HALF),
        "Side": slime_set(SLIME_SIDE, SLIME_SIDE_SQUASH, SLIME_SIDE_STRETCH, side_soft),
    }


MONSTERS['Slime'] = (SLIME_PAL, slime_frames)

# =====================================================================
# GOBLIN - green, long ears, big nose, rag tunic, small
# =====================================================================
GOB_PAL = {'1': (176, 222, 104), '2': (124, 182, 70), '3': (82, 132, 54), '4': (52, 88, 42),
           'e': (255, 226, 80), 't': (244, 240, 224), 'm': (110, 30, 40),
           'A': (176, 128, 84), 'B': (136, 94, 60), 'C': (96, 64, 44)}
GOB_SIDE_HEAD = [
"..........KKKKKKK",
"........KK1111122KK",
".......K111122222222K",
"KK....K11122222222222K",
"K1KK..K112222222222222K",
".K11KK112222222222KK222K",
".K2222K2222222222KeeK22K",
"..K3222K222222222KeKK222K",
"...KK33K222222222KKK22222K",
".....KK3222222222222222222K",
"......K332222222222KKKKKKK",
".......K3322222222KttmK",
"........KK33322222KKKK",
"..........KKKKKKKKK",
]
GOB_SIDE_BODY = [
".KKKKKKKKK",
"KBAAAAABBK",
"KBBKK2KBCK",
"KBBK22KCCK",
"KCCKKKKCCK",
]
GOB_SIDE_FWD = [
".KKKKKKKKK",
"KBAAAAABBKK",
"KBBBBBBBK22K",
"KBBBBBBCK22K",
"KCCCCCCCKKK",
]
GOB_SIDE_BACK = [
"..KKKKKKKKK",
".KKBAAAAABBK",
"K22KBBBBBBBK",
"K22KBBBBBBCK",
".KKKCCCCCCCK",
]
GOB_SIDE_LEGS = ["..K3K.K3K", "..K3K.K3K", ".KKKK.KKKK"]
GOB_SIDE_STRIDE = [".K3K...K3K", "K33K...K33K", "KKKK...KKKK"]
GOB_FRONT_HEAD = M([
"..........KKKKKK",
"........KK111112",
".......K11112222",
"......K111222222",
"KKK...K112222222",
"K11KK.K122222222",
".K1222K222222222",
"..K322K2KKKK2222",
"...KK3K2KeeK2222",
".....KK2KeKK2K22",
".....K3222222K11",
".....K3322222KKK",
"......K3322Ktmmm",
".......KK3322KKK",
".........KKKKKKK",
])
GOB_BACK_HEAD = M([
"..........KKKKKK",
"........KK111112",
".......K11112222",
"......K111222222",
"KKK...K112222222",
"K11KK.K122222222",
".K1222K222222222",
"..K322K222222222",
"...KK3K222222222",
".....KK222222222",
".....K3222222222",
".....K3322222222",
"......K332222222",
".......KK3333333",
".........KKKKKKK",
])
GOB_FRONT_BODY = M([
"..........KAAAAA",
".........KBAAAAA",
".........KCBBBBB",
"..........KKKKKK",
])
GOB_FRONT_LEGS = M([
"..........K3K...",
"..........K3K...",
".........KKKK...",
])
GOB_HAND = ["K2K", "K3K", ".K."]


def goblin_frames():
    return {
        "Down": front_cycle(GOB_FRONT_HEAD, 9, GOB_FRONT_BODY, 23, GOB_FRONT_LEGS, 27, hands=(GOB_HAND, 8, 21, 23)),
        "Up": front_cycle(GOB_BACK_HEAD, 9, GOB_FRONT_BODY, 23, GOB_FRONT_LEGS, 27, hands=(GOB_HAND, 8, 21, 23)),
        "Side": side_cycle(GOB_SIDE_HEAD, (4, 9), GOB_SIDE_BODY, (10, 22), GOB_SIDE_FWD, GOB_SIDE_BACK,
                           GOB_SIDE_LEGS, GOB_SIDE_STRIDE, (9, 27)),
    }


MONSTERS['Goblin'] = (GOB_PAL, goblin_frames)

# =====================================================================
# KOBOLD - upright little reptile: orange scales, short snout, horns,
# leather vest, tail. Uses the knight's body proportions.
# =====================================================================
KOB_PAL = {'1': (244, 156, 100), '2': (214, 104, 64), '3': (156, 66, 48), '4': (100, 40, 40),
           'S': (214, 104, 64), 's': (156, 66, 48),
           'e': (255, 236, 120), 'h': (236, 222, 190), 'H': (176, 160, 132), 'u': (250, 206, 150),
           'W': (176, 136, 96), 'G': (136, 100, 70), 'g': (96, 70, 52), 'b': (70, 50, 40), 'Y': (220, 180, 90),
           'n': (60, 24, 24)}
SCALE_LEGS = {'g': 's', 'G': 'S'}
KOB_SIDE_HEAD = [
"...........KK..KK",
"..........KhK.KhK",
".........KKHKKKHKK",
"........K11111222K",
".......K1112222222K",
"......K112222222222K",
"......K12222222KK222K",
"......K2222222KeK2222KKK",
"......K2222222KKK22222222K",
"......K322222222222222222nK",
"......K3222222222uuuuuuuKK",
"......K33222222222KKKKKKK",
".......K332222222K",
"........KK33222KK",
"..........KKKKK",
]
KOB_FRONT_HEAD = M([
"................",
"................",
"................",
"................",
"................",
"......KK........",
"......KhK.......",
".......KHKKKKKKK",
"........K1111122",
".......K11122222",
"......K112222222",
"......K122222222",
"......K22KKK2222",
"......K2KeKK2222",
"......K32KKK222u",
"......K322222uuu",
"......K32222uKuu",
".......K322uuuuu",
"........KK3KKKKK",
"..........KKKKKK",
])
KOB_BACK_HEAD = M([
"................",
"................",
"................",
"................",
"................",
"......KK........",
"......KhK.......",
".......KHKKKKKKK",
"........K1111113",
".......K11122223",
"......K112222223",
"......K122222223",
"......K222222223",
"......K222222223",
"......K322222223",
"......K322222223",
"......K332222223",
".......K33222223",
"........KK333333",
"..........KKKKKK",
])
KOB_TAIL_SIDE = ["KK", "KsKK", ".KSsSK", "..KKKK"]
KOB_TAIL_BACK = ["KKKK", "KSsK", "KSsK", ".KK."]


def kobold_frames():
    legs = remap(KN_FRONT_LEGS, SCALE_LEGS)
    return {
        "Down": front_cycle(KOB_FRONT_HEAD, 0, KN_FRONT_BODY, 20, legs, 26, hands=(KN_HAND, 6, 23, 24)),
        "Up": front_cycle(KOB_BACK_HEAD, 0, KN_BACK_BODY, 20, legs, 26, hands=(KN_HAND, 6, 23, 24),
                          front=(KOB_TAIL_BACK, 14, 25)),
        "Side": side_cycle(KOB_SIDE_HEAD, (0, 5), KN_SIDE_BODY, (0, 20), KN_SIDE_ARM_FWD, KN_SIDE_ARM_BACK,
                           remap(KN_SIDE_LEGS, SCALE_LEGS), remap(KN_SIDE_LEGS_STRIDE, SCALE_LEGS), (0, 26),
                           behind=(KOB_TAIL_SIDE, 6, 22)),
    }


MONSTERS['Kobold'] = (KOB_PAL, kobold_frames)

# =====================================================================
# SKELETON - bone white, dark sockets with a red glint
# =====================================================================
SKEL_PAL = {'1': (252, 250, 240), '2': (222, 218, 200), '3': (170, 164, 148), '4': (110, 104, 100),
            'r': (240, 60, 60)}
SKEL_SIDE_HEAD = [
"..........KKKKKKK",
"........KK1111122KK",
".......K11111222222K",
"......K1112222222222K",
".....K112222222222222K",
".....K122222222222222K",
".....K2222222222KKK22K",
".....K322222222KKrKK2K",
".....K3222KK222KKKKK2K",
".....K322K44K2222222K2K",
".....K3222KK2222222KK2K",
"......K33222222222222K",
".......KK322KKKKKKKKK",
".........KK3K2K2K2K2K",
"..........KKKKKKKKKK",
"...........K32222K",
"............KKKKK",
]
SKEL_SIDE_BODY = [
"....KKK",
"..KKK2KKKK",
".K11K1K111K",
".KKKK3KKKKK",
".K22K2K222K",
"..KKK3KKKK",
"...K2222K",
]
SKEL_ARM = ["KKK", "K1K", "K2K", "K2K", "K3K", "K2K", "KKK"]
SKEL_SIDE_LEGS = ["...K2K.K2K", "...K3K.K3K", "..KKKK.KKKK"]
SKEL_SIDE_STRIDE = ["..K2K...K2K", ".K23K...K23K", ".KKKK...KKKK"]
SKEL_FRONT_HEAD = M([
"..........KKKKKK",
"........KK111112",
".......K11111222",
"......K111222222",
".....K1122222222",
".....K1222222222",
".....K2222222222",
".....K22KKKK2222",
".....K2KKKrK2222",
".....K2KKKKK2222",
".....K32KKK2222K",
".....K3322222KKK",
"......K332222222",
".......KKKKKKKKK",
"........K1K1K1K1",
"........KKKKKKKK",
".........K322222",
"..........KKKKKK",
])
SKEL_BACK_HEAD = M([
"..........KKKKKK",
"........KK111112",
".......K11111222",
"......K111222222",
".....K1122222222",
".....K1222222222",
".....K2222222222",
".....K2222222222",
".....K3222222222",
".....K3222222222",
".....K3322222222",
".....K3332222222",
"......K333222222",
".......KKKKKKKKK",
"........KK333333",
".........KKKKKKK",
"................",
"................",
])
SKEL_FRONT_BODY = M([
"..............K2",
"..........KKKKK2",
".........K1111K2",
".........KKKKKK3",
".........K2222K2",
"..........KKKKK3",
"...........K2222",
])
SKEL_FRONT_LEGS = M([
"...........K2K..",
"...........K3K..",
"..........KKKK..",
])


def skeleton_frames():
    def side(arm_dx, legs, dy=0, hdy=0):
        return build([(legs, 8, 27), (SKEL_SIDE_BODY, 8, 20 + dy), (SKEL_ARM, 12 + arm_dx, 21 + dy),
                      (SKEL_SIDE_HEAD, 4, 4 + dy + hdy)])
    side_idle = [side(0, SKEL_SIDE_LEGS), side(0, SKEL_SIDE_LEGS),
                 side(0, SKEL_SIDE_LEGS, hdy=1), side(0, SKEL_SIDE_LEGS, hdy=1)]
    side_walk = [side(-2, SKEL_SIDE_STRIDE), side(0, SKEL_SIDE_LEGS, -1),
                 side(2, SKEL_SIDE_STRIDE), side(0, SKEL_SIDE_LEGS, -1)]
    arm = SKEL_ARM[:6]
    return {
        "Down": front_cycle(SKEL_FRONT_HEAD, 3, SKEL_FRONT_BODY, 20, SKEL_FRONT_LEGS, 27, hands=(arm, 7, 22, 21)),
        "Up": front_cycle(SKEL_BACK_HEAD, 3, SKEL_FRONT_BODY, 20, SKEL_FRONT_LEGS, 27, hands=(arm, 7, 22, 21)),
        "Side": (side_idle, side_walk),
    }


MONSTERS['Skeleton'] = (SKEL_PAL, skeleton_frames)

# =====================================================================
# ZOMBIE - the knight's shape, undead: green skin, pale eyes, messy hair,
# torn shirt, arms reaching forward
# =====================================================================
ZOM_PAL = {'H': (98, 84, 70), 'h': (72, 60, 52), 'd': (52, 42, 38), 'L': (128, 110, 92),
           'S': (150, 180, 128), 's': (106, 136, 96), 'm': (120, 44, 56), 'e': (236, 236, 190),
           'W': (156, 156, 136), 'G': (112, 120, 140), 'g': (74, 80, 100), 'b': (70, 50, 40), 'Y': (130, 112, 76)}
ZOM_FRONT_HEAD = M([
"................",
"................",
"................",
"..........KKKKKK",
"........KKHHHHHH",
".......KHHLHHHhH",
"......KHhLHHHHHh",
".....KHHHhHHHHHh",
".....KHHHHHHHHhK",
"....KhHHhHHHHhKS",
"....KhHHHHHhKKSS",
"....KhHHHhKKSSSS",
"....KhHHhKSSSSSS",
"....KhhhKSSSSSSS",
"....KKhKSSSeeSSS",
"...KsKKSSSSeeSSS",
"...KsSKSmSSKKSSS",
"....KsKmmSSSSSSS",
".....KKSsSSSSKmm",
"......KKssSSSSKK",
])
ZOM_BACK_HEAD = M([
"................",
"................",
"................",
"..........KKKKKK",
"........KKHHHHHH",
".......KHHLHHHhH",
"......KHhLHHHHHH",
".....KHHHhHHHHHH",
".....KHHHHHHHHHH",
"....KhHHhHHHHhHH",
"....KhHHHHHHHHHH",
"....KhHHHHHHHHHh",
"....KhhHHHHhHHHh",
"....KhhHHHHHHHhH",
"....KKhhHHHHHhHH",
"...KsKhhHHHHhHHH",
"...KsKhhhHHHHHHH",
"....KKhhhhHhhHHh",
".....KKhhhhhhhhh",
"......KKdddddddd",
])
ZOM_SIDE_HEAD = [
"",
"",
"",
"..........KKKKKKKKKK",
"........KKHHHHHHHHHHKK",
".......KHHHHhHHHHLLHHHK",
"......KHHHHHHHHhHHLLHHHK",
".....KHHHhHHHHHHHHHHLHHHK",
".....KHHHHHHHHHHHHHhHHHHHK",
"....KhHHHHHHHHHHHHHHHHHhhK",
"....KhHHHHHHHHHHHHHHHhhhdK",
"....KhHHHHHHHHHHHhhddSSSSK",
"....KhHHHHHHHHHHhdSSSSSSSK",
"....KhhHHHHHHHHhdSSmSSSSSK",
"....KhhHHHhKKhdSSSmSSeeSSK",
"....KhhhHKssSKSSSSSSSeeSSSK",
"....KKhhhKsSSKSSSSSSSSSSSSK",
".....KhhhhKKSSSSSSSSSSSKmmK",
"......KKhhhhKsSSSSSSSSSKKK",
".......KKddddKssSSSSSssK",
]
ZOM_SIDE_BODY = [
"..........KKKKKKKKKKKK",
"..........KgGGGWWWWWGKKKKK",
".........KgGGGWWWWWWKSSSSSK",
".........KgGGGWWWWWGKKKKKsK",
".........KgGGGGGGGGgK....KK",
"..........KbbbKKbbbbYK",
]
ZOM_SIDE_BODY_ALT = [
"..........KKKKKKKKKKKK",
"..........KgGGGWWWWWGK",
".........KgGGGWWWWWWKKKKKKK",
".........KgGGGWWWWWGKSSSSSK",
".........KgGGGGGGGGgKKKKKsK",
"..........KbbbKKbbbbYK...KK",
]
ZOM_REACH_HAND = ["KKK", "KSK", "KsK", "KKK"]


def zombie_frames():
    return {
        "Down": front_cycle(ZOM_FRONT_HEAD, 0, KN_FRONT_BODY, 20, KN_FRONT_LEGS, 26, hands=(ZOM_REACH_HAND, 8, 21, 21)),
        "Up": front_cycle(ZOM_BACK_HEAD, 0, KN_BACK_BODY, 20, KN_FRONT_LEGS, 26, hands=(KN_HAND, 6, 23, 22)),
        "Side": side_cycle(ZOM_SIDE_HEAD, (0, 0), ZOM_SIDE_BODY, (0, 20), ZOM_SIDE_BODY_ALT, ZOM_SIDE_BODY_ALT,
                           KN_SIDE_LEGS, KN_SIDE_LEGS_STRIDE, (0, 26)),
    }


MONSTERS['Zombie'] = (ZOM_PAL, zombie_frames)

# =====================================================================
# ORC - big, green, tusks, dark topknot, leather and iron armor
# =====================================================================
ORC_PAL = {'1': (150, 184, 110), '2': (108, 146, 82), '3': (76, 108, 62), '4': (50, 72, 46),
           'e': (250, 80, 60), 't': (246, 240, 220), 'h': (54, 44, 48), 'H': (84, 70, 74),
           'A': (150, 110, 80), 'B': (112, 80, 56), 'C': (78, 54, 40), 'M': (180, 184, 196),
           'N': (120, 124, 140), 'Y': (214, 170, 80), 'm': (90, 30, 36)}
ORC_SIDE_HEAD = [
"..........KKKK",
".........KHhhK",
"......KKKKhhKKKKK",
"....KK1111222222KK",
"...K111122222222222K",
"..K11222222222222222K",
"..K122222222222222222K",
"..K2222222222222KK2222K",
"..K222222222222KeeK2222K",
"..K2222KK222222KKKK22222K",
"..K322K44K222222222222222K",
"..K3222KK222222222222KKKK",
"..K33222222222222KtK2tK",
"...K33322222222222KK2K",
"....KK333322222222222K",
"......KKKKKKKKKKKKKKK",
]
ORC_SIDE_BODY = [
"..KKKKKKKKKKKKK",
".KMMNAAAAAAAMMK",
"KMNKKBBYBBBBNNK",
"K22K2KBBBBBBBCK",
"K22K2KCCCCCCCCK",
".KKKKKKKKKKKKK",
]
ORC_SIDE_FWD = [
"..KKKKKKKKKKKKK",
".KMMNAAAAAAAMMKK",
"KMNNABBYBBBBNK2K",
"KBBBBBBBBBBBCK22K",
"KCCCCCCCCCCCCK22K",
".KKKKKKKKKKKKKKK",
]
ORC_SIDE_BACK = [
"..KKKKKKKKKKKKK",
"KKMMNAAAAAAAMMK",
"K2KNABBYBBBBNNK",
"K22KBBBBBBBBBCK",
"K22KCCCCCCCCCCK",
".KKKKKKKKKKKKK",
]
ORC_SIDE_LEGS = ["...KCCK..KCCK", "...KCCK..KCCK", "..KKKKK..KKKKK"]
ORC_SIDE_STRIDE = ["..KCCK....KCCK", ".KCCCK....KCCCK", ".KKKKK....KKKKK"]
ORC_FRONT_HEAD = M([
"..............KK",
".............KHh",
".........KKKKKhh",
"......KK11111222",
".....K1111222222",
"....K11222222222",
"KK..K12222222222",
"K2KKK22KKKK22222",
".K22K22KeeK22222",
"..KKK322KKK222K2",
"....K32222222K22",
"....K332K222222K",
"....K332KtK22KKK",
"....K3332KtKmmmm",
".....KK333KKKKKK",
".......KKKKKKKKK",
])
ORC_BACK_HEAD = M([
"..............KK",
".............KHh",
".........KKKKKhh",
"......KK11111222",
".....K1111222222",
"....K11222222222",
"KK..K12222222222",
"K2KKK22222222222",
".K22K22222222222",
"..KKK32222222222",
"....K32222222222",
"....K33222222222",
"....K33322222222",
"....K33332222222",
".....KK333333333",
".......KKKKKKKKK",
])
ORC_FRONT_BODY = M([
"........KKKKKKKK",
"......KKMMNAAAAA",
".....KMMNNKBBBBB",
".....KNNKKKBBBBB",
"......KKKCCCCCCY",
".........KKKKKKK",
])
ORC_BACK_BODY = M([
"........KKKKKKKK",
"......KKMMNAAAAA",
".....KMMNNKBBBBB",
".....KNNKKKBBBBB",
"......KKKCCCCCCC",
".........KKKKKKK",
])
ORC_FRONT_LEGS = M([
"........KCCCK...",
"........KCCCK...",
".......KKKKKK...",
])
ORC_HAND = ["K22K", "K23K", ".KK."]


def orc_frames():
    return {
        "Down": front_cycle(ORC_FRONT_HEAD, 6, ORC_FRONT_BODY, 21, ORC_FRONT_LEGS, 27, hands=(ORC_HAND, 3, 25, 24)),
        "Up": front_cycle(ORC_BACK_HEAD, 6, ORC_BACK_BODY, 21, ORC_FRONT_LEGS, 27, hands=(ORC_HAND, 3, 25, 24)),
        "Side": side_cycle(ORC_SIDE_HEAD, (3, 6), ORC_SIDE_BODY, (6, 21), ORC_SIDE_FWD, ORC_SIDE_BACK,
                           ORC_SIDE_LEGS, ORC_SIDE_STRIDE, (6, 27)),
    }


MONSTERS['Orc'] = (ORC_PAL, orc_frames)

# =====================================================================
# Bat, Ghost, Mimic, Necromancer: drawn from shaded shapes in new_monsters.py
import new_monsters
for _name, _fn in new_monsters.NEW.items():
    MONSTERS[_name] = (None, _fn)

ORDER = ['Slime', 'Goblin', 'Kobold', 'Skeleton', 'Zombie', 'Orc', 'Bat', 'Ghost', 'Mimic', 'Necromancer', 'Spirit']

if __name__ == "__main__":
    # preview: one row per monster per view, idle (4) | walk (4)
    rows = [(n, v) for n in ORDER for v in VIEWS]
    preview = Image.new("RGBA", (8 * 34 + 8, len(rows) * 34), (40, 40, 48, 255))
    for r, (name, view) in enumerate(rows):
        pal, fn = MONSTERS[name]
        idle, walk = fn()[view]
        for c, g in enumerate(idle + walk):
            preview.alpha_composite(to_img(g, pal), (c * 34 + (8 if c >= 4 else 0), r * 34))
    preview.resize((preview.width * 3, preview.height * 3), Image.NEAREST).save("monsters_preview.png")
