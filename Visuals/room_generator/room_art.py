"""Room tilesets + props, drawn procedurally in the knight's pixel style, in three floor themes:
  Dungeon  mossy stone (Assets/Resources/Sprites/Room)
  Crypt    pale violet stone, cobwebs, skulls in the walls, bone piles, urns, candles, green-lit pits
           (Assets/Resources/Sprites/Room/Crypt)
  Caves    dark basalt with glowing cracks, magma rocks, braziers, lava pits (.../Room/Caves)
Also the pedestal, cost hearts and map icons.
Tiles are 32x32 at 16 pixels per unit = 2x2 world units (same pixel size as the knight).
Run: python room_art.py"""
import hashlib
import os
import random
import sys
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fx_generator"))
from fx import meta, folder_meta   # same importer settings as the other generated sprites

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Resources", "Sprites"))
K = (24, 18, 26)
OUT = {}   # (group, name) -> (Image, ppu)


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, amount):
    return tuple(clamp(x + amount) for x in c[:3])


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), tuple(c[:3]) + ((c[3],) if len(c) == 4 else (255,)))


def get(im, x, y):
    if 0 <= x < im.width and 0 <= y < im.height:
        return im.getpixel((x, y))
    return (0, 0, 0, 0)


def outline(im, color=K):
    """Dark 1px outline around every opaque area (pixel-art style)."""
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if get(im, x, y)[3] > 0:
                continue
            if any(get(im, x + dx, y + dy)[3] > 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                put(out, x, y, color)
    return out


def ellipse_mask(cx, cy, rx, ry):
    return lambda x, y: ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


# ---------------------------------------------------------------- palette
FLOOR = (94, 92, 102)
MORTAR = (54, 52, 62)
WALL = (82, 80, 92)
WALL_HI = (110, 108, 120)
WALL_MORTAR = (42, 40, 50)
CAP = (70, 68, 80)
MOSS = (86, 124, 60)
MOSS_L = (118, 160, 78)
MOSS_D = (58, 86, 46)
WOOD = (122, 80, 48)
WOOD_D = (92, 58, 34)
WOOD_L = (150, 104, 64)
IRON = (70, 70, 82)
IRON_L = (120, 120, 134)
VOID = (14, 10, 18)

THEME = "Dungeon"
THEMES = {
    "Dungeon": dict(FLOOR=(94, 92, 102), MORTAR=(54, 52, 62), WALL=(82, 80, 92), WALL_HI=(110, 108, 120),
                    WALL_MORTAR=(42, 40, 50), CAP=(70, 68, 80), MOSS=(86, 124, 60), MOSS_L=(118, 160, 78), MOSS_D=(58, 86, 46)),
    # pale grey-violet stone; "moss" becomes dusty cobweb grey
    "Crypt": dict(FLOOR=(112, 106, 124), MORTAR=(64, 58, 76), WALL=(104, 98, 118), WALL_HI=(140, 134, 154),
                  WALL_MORTAR=(50, 44, 62), CAP=(90, 84, 104), MOSS=(176, 176, 188), MOSS_L=(214, 214, 224), MOSS_D=(138, 136, 150)),
    # dark basalt; "moss" becomes glowing embers
    "Caves": dict(FLOOR=(70, 60, 60), MORTAR=(36, 28, 28), WALL=(74, 62, 60), WALL_HI=(104, 88, 82),
                  WALL_MORTAR=(32, 24, 24), CAP=(60, 50, 48), MOSS=(236, 112, 34), MOSS_L=(255, 196, 80), MOSS_D=(176, 62, 26)),
}
BONE = [(236, 232, 214), (204, 198, 176), (160, 154, 134), (112, 106, 92)]
LAVA = [(255, 236, 140), (255, 176, 60), (232, 104, 30), (168, 52, 22), (96, 26, 20)]
GHOST_GREEN = (110, 240, 140)


def use_theme(name):
    global THEME
    THEME = name
    globals().update(THEMES[name])


# ---------------------------------------------------------------- floor
def floor_tile(seed, variant):
    rnd = random.Random(seed)
    im = new(32, 32)
    # 2x2 slabs of 16x16, each slightly different shade, with bevel + mortar
    for sy in range(2):
        for sx in range(2):
            base = shade(FLOOR, rnd.randint(-7, 7))
            for y in range(16):
                for x in range(16):
                    c = base
                    if x == 15 or y == 15:
                        c = MORTAR
                    elif x == 0 or y == 0:
                        c = shade(base, 14)
                    elif x == 14 or y == 14:
                        c = shade(base, -10)
                    elif rnd.random() < 0.07:
                        c = shade(base, rnd.choice((-12, -8, 8)))
                    put(im, sx * 16 + x, sy * 16 + y, c)
    if variant == "cracked":
        x, y = rnd.randint(3, 12), rnd.randint(2, 6)
        for _ in range(14):
            put(im, x, y, MORTAR)
            put(im, x + 1, y, shade(FLOOR, -18))
            x += rnd.choice((-1, 0, 1))
            y += 1
    if variant == "mossy" and THEME == "Crypt":           # scattered bones and a skull
        for _ in range(2):
            x, y = rnd.randint(4, 22), rnd.randint(5, 25)
            for i in range(7):                                # shaft with knobbly ends
                put(im, x + i, y, BONE[0] if i in (0, 6) else BONE[1])
                put(im, x + i, y + 1, BONE[2] if i in (0, 6) else BONE[3])
            for ex in (x - 1, x + 7):
                put(im, ex, y, BONE[1])
                put(im, ex, y + 1, BONE[2])
                put(im, ex + (1 if ex < x else -1), y - 1, BONE[0])
                put(im, ex + (1 if ex < x else -1), y + 2, BONE[2])
        sx, sy = rnd.randint(8, 22), rnd.randint(8, 22)
        skull = ellipse_mask(sx, sy, 3, 2.6)
        for y in range(32):
            for x in range(32):
                if skull(x, y):
                    put(im, x, y, BONE[0] if y < sy else BONE[2])
        put(im, sx - 1, sy, VOID)
        put(im, sx + 1, sy, VOID)
        return im
    if variant == "mossy" and THEME == "Caves":            # glowing lava veins in the cracks
        x, y = rnd.randint(6, 25), rnd.randint(2, 12)
        for _ in range(rnd.randint(8, 14)):                   # one short glowing crack
            put(im, x, y, MOSS)
            if rnd.random() < 0.3:
                put(im, x + 1, y, MOSS_D)
            x = max(1, min(30, x + rnd.choice((-1, 0, 1))))
            y += 1
        return im
    if variant in ("mossy", "puddle_moss"):
        for _ in range(3):
            cx, cy = rnd.choice((14, 15, 16)), rnd.randint(4, 28)
            if rnd.random() < 0.5:
                cx, cy = cy, cx
            for y in range(-3, 4):
                for x in range(-4, 5):
                    if (x / 4.2) ** 2 + (y / 3.0) ** 2 <= 1 and rnd.random() < 0.85:
                        put(im, cx + x, cy + y, MOSS_L if y < -1 else (MOSS if y < 2 else MOSS_D))
    if variant == "puddle":
        cx, cy = rnd.randint(10, 22), rnd.randint(10, 22)
        inside = ellipse_mask(cx, cy, 6, 3.5)
        shine = ellipse_mask(cx - 2, cy - 1, 2.5, 1.2)
        # water / glowing green ooze / a little lava pool
        deep, light = {"Crypt": ((52, 104, 70), (120, 220, 140)), "Caves": (LAVA[2], LAVA[0])}.get(THEME, ((66, 74, 92), (104, 116, 138)))
        for y in range(32):
            for x in range(32):
                if inside(x, y):
                    put(im, x, y, light if shine(x, y) else deep)
    return im


# Floor_0-4 plain, 5-6 cracked, 7-8 mossy, 9 puddle (the room builder mostly picks plain ones)
for i, variant in enumerate(("plain",) * 5 + ("cracked",) * 2 + ("mossy",) * 2 + ("puddle",)):
    OUT[("Room", f"Floor_{i}")] = (floor_tile(100 + i, variant), 16)


# ---------------------------------------------------------------- walls
def brick_face(seed, moss=True, shadow=True):
    """North wall: front-facing bricks with a dark base where it meets the floor."""
    rnd = random.Random(seed)
    im = new(32, 32)
    for y in range(32):
        row = y // 8
        offset = 8 if row % 2 else 0
        for x in range(32):
            bx = (x + offset) % 16
            by = y % 8
            c = shade(WALL, ((x + offset) // 16 * 7 + row * 5) % 9 - 4)
            if by == 7 or bx == 15:
                c = WALL_MORTAR
            elif by == 0:
                c = WALL_HI
            elif rnd.random() < 0.06:
                c = shade(c, rnd.choice((-10, 10)))
            if shadow and y >= 29:
                c = shade(c, -30 - (y - 29) * 10)    # shadow at the foot of the wall
            put(im, x, y, c)
    if moss and THEME == "Crypt":
        # a skull set into a brick niche, and a cobweb hanging in the top corner
        if rnd.random() < 0.7:
            nx, ny = rnd.choice((4, 12, 20)), rnd.choice((9, 17))
            for y in range(ny, ny + 6):
                for x in range(nx, nx + 8):
                    put(im, x, y, shade(WALL_MORTAR, -10))
            skull = ellipse_mask(nx + 4, ny + 3, 2.6, 2.4)
            for y in range(ny, ny + 6):
                for x in range(nx, nx + 8):
                    if skull(x, y):
                        put(im, x, y, BONE[0] if y < ny + 3 else BONE[2])
            put(im, nx + 3, ny + 3, VOID)
            put(im, nx + 5, ny + 3, VOID)
        cx = rnd.choice((0, 31))
        d = 1 if cx == 0 else -1
        for i in range(9):
            put(im, cx + d * i, 0, MOSS_L)
            put(im, cx, i, MOSS_L)
            put(im, cx + d * i // 2, i // 2, MOSS)
        for i in range(1, 6):
            put(im, cx + d * i, 6 - i, MOSS)
        return im
    if moss and THEME == "Caves":
        for _ in range(rnd.randint(1, 2)):                     # a glowing crack running down the rock
            x, y = rnd.randint(3, 28), rnd.randint(0, 8)
            for _ in range(rnd.randint(8, 18)):
                put(im, x, y, MOSS)
                put(im, x, y + 1, MOSS_D)
                if rnd.random() < 0.25:
                    put(im, x + 1, y, MOSS_L)
                x = max(1, min(30, x + rnd.choice((-1, 0, 1))))
                y += 1
                if y > 28:
                    break
        return im
    if moss:
        for _ in range(rnd.randint(1, 3)):
            x = rnd.randint(1, 30)
            length = rnd.randint(3, 10)
            for y in range(length):
                put(im, x, y, MOSS if y < length - 2 else MOSS_D)
                if rnd.random() < 0.4:
                    put(im, x + 1, y, MOSS_L)
    return im


def wall_cap(seed, inner_edge):
    """Top of the side/bottom walls seen from above: big cap stones, lit edge facing the room."""
    rnd = random.Random(seed)
    im = new(32, 32)
    for sy in range(2):
        for sx in range(2):
            base = shade(CAP, rnd.randint(-6, 6))
            for y in range(16):
                for x in range(16):
                    c = base
                    if x == 15 or y == 15:
                        c = WALL_MORTAR
                    elif x == 0 or y == 0:
                        c = shade(base, 12)
                    elif rnd.random() < 0.05:
                        c = shade(base, -10)
                    put(im, sx * 16 + x, sy * 16 + y, c)
    # The edge facing the floor gets a bright lip and a little moss
    for i in range(32):
        for d, c in ((0, WALL_HI), (1, shade(WALL_HI, -16))):
            if inner_edge == "top":
                put(im, i, d, c)
            elif inner_edge == "bottom":
                put(im, i, 31 - d, c)
            elif inner_edge == "left":
                put(im, d, i, c)
            elif inner_edge == "right":
                put(im, 31 - d, i, c)
        if rnd.random() < 0.15 and inner_edge != "none":
            mx = {"top": (i, 2), "bottom": (i, 29), "left": (2, i), "right": (29, i)}[inner_edge]
            put(im, mx[0], mx[1], MOSS)
    return im


OUT[("Room", "Wall_N_0")] = (brick_face(1), 16)
OUT[("Room", "Wall_N_1")] = (brick_face(2), 16)
OUT[("Room", "Wall_N_2")] = (brick_face(3, moss=False), 16)


def inner_corner():
    """Mitred corner, drawn for the top-left of the room (north wall to its right, west wall below it):
    the upper-right triangle is horizontal north-wall bricks, the lower-left triangle is the same bricks
    turned for the west wall, meeting along a 45 degree seam. Each half keeps its shaded base, so the
    shadows meet in the inner (bottom-right) corner. The room builder rotates it for the other corners."""
    north = brick_face(4, moss=False)
    west = north.rotate(90)          # same rotation the west wall gets in the room
    im = new(32, 32)
    for y in range(32):
        for x in range(32):
            if x == y:
                c = WALL_MORTAR       # the diagonal seam
                if x >= 29:
                    c = shade(WALL_MORTAR, -12)
            else:
                c = (north if x > y else west).getpixel((x, y))
                # Ambient shadow: darker close to the seam, and deeper toward the inner corner
                near_seam = max(0.0, 1.0 - abs(x - y) / 6.0)
                inward = (x + y) / 62.0
                c = shade(c, -int(near_seam * (8 + 22 * inward)) - int(10 * inward * inward))
            put(im, x, y, c)
    return im


def floor_corner_shadow():
    """Soft shadow the walls cast into the floor tile in a room corner (drawn for the top-left
    corner: walls above and to the left). Overlaid on the floor and rotated per corner."""
    im = new(32, 32)
    for y in range(32):
        for x in range(32):
            corner = max(0.0, 1.0 - ((x * x + y * y) ** 0.5) / 22.0)      # pooled in the corner
            edges = max(0.0, 1.0 - min(x, y) / 5.0) * 0.45                 # thin strip along both walls
            a = int(120 * max(corner, edges * max(0.0, 1.0 - max(x, y) / 30.0)))
            if a > 0:
                put(im, x, y, (12, 8, 16, a))
    return im


OUT[("Room", "Wall_Corner_Inner")] = (inner_corner(), 16)
OUT[("Room", "Floor_CornerShadow")] = (floor_corner_shadow(), 16)
OUT[("Room", "Wall_S")] = (wall_cap(10, "top"), 16)
OUT[("Room", "Wall_W")] = (wall_cap(11, "right"), 16)
OUT[("Room", "Wall_E")] = (wall_cap(12, "left"), 16)
OUT[("Room", "Wall_Corner")] = (wall_cap(13, "none"), 16)


# ---------------------------------------------------------------- doors (drawn for the north wall; rotated in-game)
GOLD = [(255, 230, 130), (236, 186, 70), (186, 130, 44), (130, 86, 30)]
BLOOD = [(214, 50, 50), (160, 28, 36), (110, 16, 26), (64, 8, 16)]
DARK_IRON = [(120, 112, 124), (84, 78, 92), (58, 52, 64), (36, 32, 42)]


def door(closed, style="normal"):
    """style: normal / boss (dark iron, skull keystone, blood-red light) / treasure (gold frame,
    gem keystone, warm golden light)."""
    if style != "normal":
        return special_door(closed, style)
    im = brick_face(7, moss=False)
    left, right, top = 6, 25, 5
    for y in range(top, 32):
        for x in range(left, right + 1):
            # rounded arch top
            if y < top + 4 and ((x - 15.5) / 10) ** 2 + ((y - (top + 4)) / 4.2) ** 2 > 1:
                continue
            edge = x in (left, left + 1, right - 1, right) or y in (top, top + 1)
            if edge:
                c = (128, 126, 136) if (x in (left, right) or y == top) else (100, 98, 110)
            elif closed:
                plank = (x - left - 2) // 4
                c = WOOD if plank % 2 == 0 else WOOD_D
                if (x - left - 2) % 4 == 3:
                    c = shade(WOOD_D, -18)
                if y in (top + 9, top + 10, top + 19, top + 20):
                    c = IRON if y % 2 else IRON_L
                    if (x - left) % 5 == 2:
                        c = (170, 170, 180)   # rivets
                if y == top + 3 and plank % 2 == 0:
                    c = WOOD_L
            else:
                depth = (y - top) / (32 - top)
                c = shade(VOID, int(20 * depth))
            put(im, x, y, c)
    if closed:   # ring handle
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            put(im, 22 + dx, 19 + dy, (196, 160, 70))
    return im


def special_door(closed, style):
    im = brick_face(7, moss=False)
    boss = style == "boss"
    frame = DARK_IRON if boss else GOLD
    left, right, top = 5, 26, 4
    for y in range(top, 32):
        for x in range(left, right + 1):
            if y < top + 5 and ((x - 15.5) / 11) ** 2 + ((y - (top + 5)) / 5.2) ** 2 > 1:
                continue                                            # pointed / rounded arch
            edge = x in (left, left + 1, left + 2, right - 2, right - 1, right) or y in (top, top + 1, top + 2)
            if edge:
                outer = x in (left, right) or y == top
                c = frame[0] if outer else frame[1] if x in (left + 1, right - 1) or y == top + 1 else frame[2]
                if boss and (y - top) % 6 == 3 and edge and not outer:
                    c = (200, 196, 180)                             # bone studs down the frame
            elif closed:
                plank = (x - left - 3) // 4
                if boss:
                    c = BLOOD[2] if plank % 2 == 0 else BLOOD[3]
                    if (x - left - 3) % 4 == 3:
                        c = (40, 6, 12)
                    if y in (top + 8, top + 9, top + 16, top + 17, top + 24, top + 25):
                        c = DARK_IRON[1] if y % 2 else DARK_IRON[0]
                        if (x - left) % 4 == 1:
                            c = (170, 160, 170)                     # rivets
                else:
                    c = WOOD_L if plank % 2 == 0 else WOOD
                    if (x - left - 3) % 4 == 3:
                        c = WOOD_D
                    if y in (top + 9, top + 10, top + 20, top + 21):
                        c = GOLD[1] if y % 2 else GOLD[0]
            else:
                depth = (y - top) / (32 - top)
                glow = BLOOD[1] if boss else GOLD[2]
                k = 0.55 * depth                                    # light spilling from the room beyond
                c = tuple(int(VOID[i] * (1 - k) + glow[i] * k) for i in range(3))
            put(im, x, y, c)
    # keystone: a skull (boss) or a red gem (treasure) set over the arch
    kx, ky = 15, top + 1
    if boss:
        skull = ellipse_mask(kx + 0.5, ky + 2, 3.2, 2.8)
        for y in range(ky - 2, ky + 6):
            for x in range(kx - 4, kx + 6):
                if skull(x, y):
                    put(im, x, y, (236, 232, 214) if y < ky + 2 else (190, 184, 164))
        put(im, kx - 1, ky + 2, (230, 40, 40))
        put(im, kx + 2, ky + 2, (230, 40, 40))
        put(im, kx, ky + 4, VOID)
        put(im, kx + 1, ky + 4, VOID)
        for d in (-1, 1):                                           # horns
            hx = kx + (5 if d > 0 else -4)
            for i in range(4):
                put(im, hx + d * i // 2, ky + 1 - i, (220, 214, 196) if i < 3 else (160, 154, 140))
    else:
        for y in range(ky - 1, ky + 5):
            for x in range(kx - 2, kx + 4):
                if abs(x - kx - 0.5) + abs(y - ky - 1.5) <= 3:
                    put(im, x, y, (230, 50, 70) if x + y < kx + ky + 2 else (150, 20, 40))
        put(im, kx - 1, ky, (255, 200, 210))
    if closed and not boss:                                         # golden lock plate
        for y in range(18, 23):
            for x in range(14, 18):
                put(im, x, y, GOLD[0] if x == 14 or y == 18 else GOLD[2])
        put(im, 15, 20, VOID)
        put(im, 16, 20, VOID)
        put(im, 15, 21, VOID)
    if closed and boss:                                             # a heavy iron bar across it
        for x in range(left + 2, right - 1):
            put(im, x, 19, DARK_IRON[0])
            put(im, x, 20, DARK_IRON[2])
    return im


OUT[("Room", "Door_Open")] = (door(False), 16)
OUT[("Room", "Door_Closed")] = (door(True), 16)
for _style, _prefix in (("boss", "Door_Boss"), ("treasure", "Door_Treasure")):
    OUT[("Room", f"{_prefix}_Open")] = (door(False, _style), 16)
    OUT[("Room", f"{_prefix}_Closed")] = (door(True, _style), 16)


# ---------------------------------------------------------------- torch (on north walls)
def candles(frame):
    im = new(10, 18)
    for i, (x, top) in enumerate(((2, 10), (5, 8), (8, 11))):
        for y in range(top, 17):
            put(im, x, y, BONE[0] if y < top + 2 else BONE[1])
        flicker = (frame + i) % 2
        put(im, x, top - 1, (255, 200, 90))
        put(im, x, top - 2 - flicker, (255, 236, 150))
    for x in range(1, 10):
        put(im, x, 17, BONE[2])                               # wax pool
    return outline(im)


def brazier(frame):
    im = new(10, 18)
    for y in range(12, 17):
        put(im, 4, y, IRON)
        put(im, 5, y, IRON_L if y < 14 else IRON)
    for x in range(1, 9):                                     # bowl
        put(im, x, 10, IRON_L)
        put(im, x, 11, IRON)
    flame = [(2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (3, 8), (4, 8), (5, 8), (6, 8), (4, 7), (5, 7),
             (4, 6 - frame), (5, 5 + frame), (3, 7 - frame), (6, 6 + frame)]
    for x, y in flame:
        put(im, x, y, LAVA[1])
    for x, y in ((4, 8), (5, 8), (4 + frame, 7)):
        put(im, x, y, LAVA[0])
    return outline(im)


def torch(frame):
    if THEME == "Crypt":
        return candles(frame)
    if THEME == "Caves":
        return brazier(frame)
    im = new(10, 18)
    for y in range(10, 17):
        put(im, 4, y, IRON)
        put(im, 5, y, IRON_L if y < 12 else IRON)
    for x in range(2, 8):
        put(im, x, 10, IRON_L)
        put(im, x, 11, IRON)
    flame = [(4, 9), (5, 9), (3, 8), (4, 8), (5, 8), (6, 8), (3, 7), (4, 7), (5, 7), (6, 7),
             (4, 6), (5, 6), (4, 5), (5, 4 if frame else 5), (4, 3 if frame == 0 else 4), (3, 6 if frame else 5)]
    for x, y in flame:
        put(im, x, y, (255, 150, 40))
    for x, y in ((4, 8), (5, 8), (4, 7), (5, 7) if frame else (4, 6)):
        put(im, x, y, (255, 236, 120))
    return outline(im)


OUT[("Room", "Torch_0")] = (torch(0), 16)
OUT[("Room", "Torch_1")] = (torch(1), 16)


# ---------------------------------------------------------------- obstacles
def bone_pile(seed, w, h):
    rnd = random.Random(seed)
    im = new(32, 32)
    cx, base = 16, 29
    for i in range(int(w * h / 18)):                          # heap of bones
        x = cx + rnd.randint(-w // 2 + 2, w // 2 - 2)
        top = base - int((1 - abs(x - cx) / (w / 2)) * h * 0.8) - 1
        y = rnd.randint(top, base - 1)
        horizontal = rnd.random() < 0.6
        for j in range(4):
            bx, by = (x + j - 2, y) if horizontal else (x, y + j - 2)
            put(im, bx, by, BONE[rnd.randint(0, 2)])
    for sx, sy in ((cx - 3, base - h // 2), (cx + 4, base - h // 3)):    # skulls on top
        skull = ellipse_mask(sx, sy, 3, 2.6)
        for y in range(32):
            for x in range(32):
                if skull(x, y):
                    put(im, x, y, BONE[0] if y < sy else BONE[2])
        put(im, sx - 1, sy, VOID)
        put(im, sx + 1, sy, VOID)
        put(im, sx, sy + 2, BONE[3])
    im = outline(im)
    for x in range(cx - w // 2 + 1, cx + w // 2):
        if get(im, x, 31)[3] == 0:
            put(im, x, 31, (20, 16, 24, 110))
    return im


def rock(seed, w, h):
    if THEME == "Crypt":
        return bone_pile(seed, w, h)
    rnd = random.Random(seed)
    im = new(32, 32)
    cx, cy = 16, 32 - h / 2 - 2
    inside = ellipse_mask(cx, cy, w / 2, h / 2)
    for y in range(32):
        for x in range(32):
            if not inside(x, y):
                continue
            # light from the top-left
            t = ((x - cx) / w + (y - cy) / h)
            c = (150, 148, 156) if t < -0.25 else (118, 116, 126) if t < 0.15 else (86, 84, 96)
            if THEME == "Caves":
                c = (96, 82, 78) if t < -0.25 else (70, 58, 56) if t < 0.15 else (48, 38, 38)
            if rnd.random() < 0.08:
                c = shade(c, -14)
            put(im, x, y, c)
    for _ in range(2):   # cracks (glowing in the caves)
        x, y = rnd.randint(int(cx - w / 3), int(cx + w / 3)), int(cy - h / 4)
        for _ in range(rnd.randint(3, 6) + (3 if THEME == "Caves" else 0)):
            put(im, x, y, MOSS if THEME == "Caves" else (60, 58, 70))
            x += rnd.choice((-1, 0, 1))
            y += 1
    for _ in range(rnd.randint(4, 8)):   # moss on top
        x = rnd.randint(int(cx - w / 3), int(cx + w / 3))
        top = next((yy for yy in range(32) if get(im, x, yy)[3] > 0), None)
        if top is not None:
            put(im, x, top, MOSS_L)
            put(im, x, top + 1, MOSS)
    im = outline(im)
    # contact shadow on the floor
    for x in range(int(cx - w / 2) + 1, int(cx + w / 2)):
        if get(im, x, 31)[3] == 0:
            put(im, x, 31, (20, 16, 24, 110))
    return im


def pillar():
    im = new(32, 32)
    for y in range(2, 30):
        for x in range(5, 27):
            if y < 9:
                c = (150, 148, 158) if y > 3 else (170, 168, 178)          # top face
            else:
                c = (110, 108, 120) if x < 9 else (96, 94, 106) if x < 23 else (78, 76, 88)
                if (y - 9) % 7 == 6:
                    c = WALL_MORTAR
            put(im, x, y, c)
    for x in range(6, 12):
        put(im, x, 9 + (x % 3), MOSS)
    im = outline(im)
    for x in range(6, 27):
        put(im, x, 31, (20, 16, 24, 110))
    return im


def pot(mimic=False):
    """mimic: the pot hides a mimic - its only tell is a jagged crack like a grin along the band."""
    # clay pot / grey-blue funeral urn (crypt)
    hi, mid, lo, rim, band, lip = ((214, 140, 82), (178, 104, 60), (130, 72, 42), (196, 124, 72), (110, 60, 36), (150, 86, 50))
    if THEME == "Crypt":
        hi, mid, lo, rim, band, lip = ((168, 176, 196), (128, 136, 160), (92, 98, 122), (150, 158, 180), (196, 168, 96), (110, 116, 138))
    im = new(32, 32)
    body = ellipse_mask(16, 22, 8, 8)
    for y in range(32):
        for x in range(32):
            if body(x, y) or (12 <= x <= 19 and 11 <= y <= 14):
                t = (x - 16) / 8 + (y - 22) / 10
                c = hi if t < -0.4 else mid if t < 0.3 else lo
                if y in (11, 12) and 11 <= x <= 20:
                    c = rim
                if y == 19 and 9 <= x <= 23:
                    c = band   # painted band
                put(im, x, y, c)
    for x in range(11, 21):
        put(im, x, 10, lip)
    if mimic:
        # zig-zag crack just under the band, a bit like a row of teeth
        for i, x in enumerate(range(10, 23)):
            put(im, x, 21 + (i % 2), shade(lo, -40))
    im = outline(im)
    for x in range(10, 23):
        put(im, x, 31, (20, 16, 24, 110))
    return im


def rubble(seed):
    rnd = random.Random(seed)
    im = new(32, 32)
    for _ in range(6):
        cx, cy, r = rnd.randint(6, 26), rnd.randint(14, 28), rnd.randint(2, 4)
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    put(im, cx + x, cy + y, (128, 126, 134) if y < 0 else (96, 94, 104))
    return outline(im)


OUT[("Room", "Rock_0")] = (rock(21, 26, 22), 16)
OUT[("Room", "Rock_1")] = (rock(22, 22, 18), 16)
OUT[("Room", "Pillar")] = (pillar(), 16)
OUT[("Room", "Pot")] = (pot(), 16)
OUT[("Room", "Pot_Mimic")] = (pot(mimic=True), 16)
OUT[("Room", "Rubble")] = (rubble(5), 16)


# ---------------------------------------------------------------- pits (16 versions: a rim on every side that borders floor)
def lava_pit(mask):
    im = new(32, 32)
    rnd = random.Random(mask)
    for y in range(32):
        for x in range(32):
            put(im, x, y, LAVA[1] if (x + y * 3 + rnd.randint(0, 6)) % 11 else LAVA[0])
            if rnd.random() < 0.08:
                put(im, x, y, LAVA[2])
    # dark cooled crust along every edge that touches floor
    for bit, cells in ((1, [(x, y) for y in range(3) for x in range(32)]), (4, [(x, 31 - y) for y in range(2) for x in range(32)]),
                       (8, [(y, x) for y in range(2) for x in range(32)]), (2, [(31 - y, x) for y in range(2) for x in range(32)])):
        if mask & bit:
            for x, y in cells:
                put(im, x, y, LAVA[4] if min(x, y, 31 - x, 31 - y) == 0 else LAVA[3])
    return im


def pit(mask):
    """mask bits: 1 = floor above, 2 = floor right, 4 = floor below, 8 = floor left"""
    if THEME == "Caves":
        return lava_pit(mask)
    im = new(32, 32)
    for y in range(32):
        for x in range(32):
            put(im, x, y, shade(VOID, int(6 * (y / 32))))
            if THEME == "Crypt" and y > 12:                   # an eerie green glow far below
                g = (y - 12) / 20
                put(im, x, y, (int(14 + 10 * g), int(10 + 70 * g), int(18 + 30 * g)))
    if mask & 1:      # far edge: the pit's inner wall is visible, lit at the top
        for y in range(7):
            for x in range(32):
                put(im, x, y, (118, 116, 126) if y == 0 else shade((70, 68, 80), -y * 7))
    if mask & 4:
        for x in range(32):
            put(im, x, 31, (110, 108, 120))
            put(im, x, 30, (70, 68, 80))
    if mask & 8:
        for y in range(32):
            put(im, 0, y, (100, 98, 110))
            put(im, 1, y, (56, 54, 66))
    if mask & 2:
        for y in range(32):
            put(im, 31, y, (100, 98, 110))
            put(im, 30, y, (56, 54, 66))
    return im


for m in range(16):
    OUT[("Room", f"Pit_{m}")] = (pit(m), 16)


# ---------------------------------------------------------------- spike trap
def spikes(state):
    """state: down, warn, up"""
    im = new(32, 32)
    for y in range(2, 30):
        for x in range(2, 30):
            c = (84, 82, 94)
            if x in (2, 29) or y in (2, 29):
                c = (60, 58, 70)
            elif x == 3 or y == 3:
                c = (106, 104, 116)
            put(im, x, y, c)
    holes = [(9, 10), (21, 10), (15, 17), (9, 24), (21, 24)]
    for hx, hy in holes:
        for dx in range(-1, 2):
            for dy in range(0, 2):
                put(im, hx + dx, hy + dy, (24, 20, 28))
        if state == "warn":
            put(im, hx, hy, (200, 200, 210))
        if state == "up":
            for i in range(7):
                w = max(0, 2 - i // 3)
                for dx in range(-w, w + 1):
                    put(im, hx + dx, hy - i, (210, 210, 220) if dx <= 0 else (140, 140, 154))
            put(im, hx, hy - 7, (240, 240, 248))
    return outline(im) if state == "up" else im


for s in ("down", "warn", "up"):
    OUT[("Room", f"Spikes_{s}")] = (spikes(s), 16)


# ---------------------------------------------------------------- stairs down (after the boss)
def stairs():
    im = new(32, 32)
    for y in range(2, 30):
        for x in range(2, 30):
            put(im, x, y, WOOD_D if (x in (2, 3, 28, 29) or y in (2, 3, 28, 29)) else VOID)
    for step in range(5):
        y0 = 6 + step * 4
        for y in range(y0, y0 + 3):
            for x in range(5 + step, 27 - step):
                put(im, x, y, shade((110, 108, 120), -step * 16 - (y - y0) * 8))
    return outline(im)


OUT[("Room", "Stairs")] = (stairs(), 16)


# ---------------------------------------------------------------- pedestal + coloured heart cost icons
def pedestal():
    im = new(22, 26)
    for y in range(26):
        for x in range(22):
            c = None
            if y < 4 and 0 <= x < 22:                     # top slab
                c = (176, 174, 184) if y < 2 else (150, 148, 158)
            elif 4 <= y < 19 and 3 <= x < 19:             # plain pillar face (cost hearts go here)
                c = (128, 126, 136) if x < 5 else (112, 110, 122) if x < 17 else (92, 90, 102)
            elif 19 <= y < 26 and 1 <= x < 21:            # base
                c = (150, 148, 158) if y < 21 else (110, 108, 120)
            if c:
                put(im, x, y, c)
    for x in range(3, 19):
        put(im, x, 4, (78, 76, 88))     # shadow under the top slab
    return outline(im)


OUT[("Effects", "Pedestal")] = (pedestal(), 16)

MINI_HEART = [
".XX.XX.",
"XXXXXXX",
"XXXXXXX",
".XXXXX.",
"..XXX..",
"...X...",
]


def cost_heart(half):
    im = new(9, 8)
    for my, row in enumerate(MINI_HEART):
        for mx, ch in enumerate(row):
            if ch != 'X':
                continue
            x, y = mx + 1, my + 1
            if half and mx > 3:
                continue
            c = (226, 44, 66)
            if (mx, my) in ((1, 1), (1, 2)):
                c = (255, 196, 196)
            elif my >= 3 or mx >= 5:
                c = (150, 22, 44)
            put(im, x, y, c)
    return outline(im)


OUT[("Room", "CostHeart_full")] = (cost_heart(False), 16)
OUT[("Room", "CostHeart_half")] = (cost_heart(True), 16)


# ---------------------------------------------------------------- minimap icons (UI)
def icon(rows, pal):
    im = new(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                put(im, x, y, pal[ch])
    return im


OUT[("UI", "Map_Crown")] = (icon([
"Y.Y.Y",
"YYYYY",
"YRYRY",
"YYYYY",
], {'Y': (240, 188, 64), 'R': (226, 44, 66)}), 16)
OUT[("UI", "Map_Skull")] = (icon([
".WWW.",
"WWWWW",
"WKWKW",
"WWWWW",
".W.W.",
], {'W': (236, 232, 222), 'K': K}), 16)


# The room sprites redrawn for every theme (everything else is shared)
def room_set():
    sprites = {}
    for i, variant in enumerate(("plain",) * 5 + ("cracked",) * 2 + ("mossy",) * 2 + ("puddle",)):
        sprites[f"Floor_{i}"] = floor_tile(100 + i, variant)
    sprites["Wall_N_0"] = brick_face(1)
    sprites["Wall_N_1"] = brick_face(2)
    sprites["Wall_N_2"] = brick_face(3, moss=False)
    sprites["Wall_Corner_Inner"] = inner_corner()
    sprites["Wall_S"] = wall_cap(10, "top")
    sprites["Wall_W"] = wall_cap(11, "right")
    sprites["Wall_E"] = wall_cap(12, "left")
    sprites["Wall_Corner"] = wall_cap(13, "none")
    sprites["Door_Open"] = door(False)
    sprites["Door_Closed"] = door(True)
    for style, prefix in (("boss", "Door_Boss"), ("treasure", "Door_Treasure")):
        sprites[f"{prefix}_Open"] = door(False, style)
        sprites[f"{prefix}_Closed"] = door(True, style)
    sprites["Torch_0"] = torch(0)
    sprites["Torch_1"] = torch(1)
    sprites["Rock_0"] = rock(21, 26, 22)
    sprites["Rock_1"] = rock(22, 22, 18)
    sprites["Pillar"] = pillar()
    sprites["Pot"] = pot()
    sprites["Pot_Mimic"] = pot(mimic=True)
    sprites["Rubble"] = rubble(5)
    for m in range(16):
        sprites[f"Pit_{m}"] = pit(m)
    for st in ("down", "warn", "up"):
        sprites[f"Spikes_{st}"] = spikes(st)
    sprites["Stairs"] = stairs()
    return sprites


for _theme in ("Crypt", "Caves"):
    use_theme(_theme)
    for _name, _im in room_set().items():
        OUT[(f"Room/{_theme}", _name)] = (_im, 16)
use_theme("Dungeon")


if __name__ == "__main__":
    resources = os.path.dirname(ROOT)
    for d in (resources, ROOT):
        os.makedirs(d, exist_ok=True)
        folder_meta(d)
    previews = []
    for (group, name), (im, ppu) in OUT.items():
        folder = os.path.join(ROOT, *group.split("/"))
        os.makedirs(folder, exist_ok=True)
        folder_meta(folder)
        path = os.path.join(folder, name + ".png")
        im.save(path)
        with open(path + ".meta", "w", newline="\n") as f:
            f.write(meta(hashlib.md5(f"hfp_fx_{group}_{name}".encode()).hexdigest(), ppu))
    if os.path.isdir(os.path.join(ROOT, "Room")):
        for theme_folder in ("Crypt", "Caves"):
            folder_meta(os.path.join(ROOT, "Room", theme_folder))
        previews.append(im)

    # Contact sheet + a mock room to judge how the tiles fit together
    cols, cell = 10, 34
    sheet = Image.new("RGBA", (cols * cell, ((len(previews) + cols - 1) // cols) * cell), (40, 40, 48, 255))
    for i, im in enumerate(previews):
        sheet.alpha_composite(im, ((i % cols) * cell + (cell - im.width) // 2, (i // cols) * cell + (cell - im.height) // 2))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(os.path.dirname(__file__), "tiles_preview.png"))

    tiles = {n: im for (g, n), (im, _) in OUT.items()}
    room = Image.new("RGBA", (15 * 32, 9 * 32), (0, 0, 0, 255))
    rnd = random.Random(3)
    for ty in range(9):
        for tx in range(15):
            if ty == 0 and tx == 7:
                t = tiles["Door_Closed"]
            elif ty == 0:
                t = tiles[f"Wall_N_{rnd.randint(0, 2)}"] if 0 < tx < 14 else tiles["Wall_Corner"]
            elif ty == 8:
                t = tiles["Wall_S"] if 0 < tx < 14 else tiles["Wall_Corner"]
            elif tx == 0:
                t = tiles["Wall_W"]
            elif tx == 14:
                t = tiles["Wall_E"]
            else:
                t = tiles[f"Floor_{rnd.choice((0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9))}"]
            room.alpha_composite(t, (tx * 32, ty * 32))
    for name, tx, ty in (("Rock_0", 4, 3), ("Rock_1", 10, 5), ("Pillar", 3, 6), ("Pot", 12, 2), ("Spikes_up", 7, 4),
                         ("Spikes_down", 8, 4), ("Pit_9", 5, 5), ("Pit_3", 6, 5), ("Pit_12", 5, 6), ("Pit_6", 6, 6), ("Stairs", 9, 2)):
        room.alpha_composite(tiles[name], (tx * 32, ty * 32))
    room.alpha_composite(tiles["Torch_0"], (3 * 32 + 11, 6))
    room.alpha_composite(tiles["Torch_1"], (11 * 32 + 11, 6))
    room.alpha_composite(tiles["Pedestal"], (11 * 32 + 5, 3 * 32 + 3))
    room.alpha_composite(tiles["CostHeart_half"], (11 * 32 + 11, 3 * 32 + 12))
    room.resize((room.width * 2, room.height * 2), Image.NEAREST).save(os.path.join(os.path.dirname(__file__), "room_preview.png"))
    print(f"wrote {len(OUT)} sprites")
