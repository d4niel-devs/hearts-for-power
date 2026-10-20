"""Illustrated itch.io cover (630x500), painted as pixel art on a 315x250 canvas at 2x.

The ruby heart floats in a torch-lit dungeon hall, run through by the sword (hilt above, blade inside,
bloody tip out the bottom, a burning crack where it passes). The bosses loom at the sides, painted
large in their real game colours and lit by the heart: the Ancient Lich (violet robes, green rune
panel, bronze crown, phylactery, horned-skull staff in soul-fire, wisps for feet), the Orc Warlord
(green skin, horned iron helm, red eyes, tusks, spiked pauldrons, fur collar, red cape, double axe
raised) and the King Slime (blue, gold crown, angry eyes). The game's own monsters creep in from the
dark, and the knight - blond mop of hair, white tunic, grey trousers, brown belt - stands at the foot
of the steps with his back to us, sword lowered.
Run: python poster.py  ->  Visuals/cover/cover_630x500.png"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
FONTS = os.path.join(PROJ, "Assets", "Resources", "Fonts")
MONSTERS = os.path.join(PROJ, "Assets", "Animations", "Monsters")
SPRITES = os.path.join(PROJ, "Assets", "Resources", "Sprites")
W, H = 315, 250
rnd = random.Random(12)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
K = (16, 6, 14)
CX, CY = 157, 108              # the heart, and the centre of the light

LIGHT = [(9, 3, 11), (22, 5, 16), (40, 7, 22), (66, 10, 28), (102, 14, 34), (142, 22, 38),
         (186, 36, 40), (222, 66, 44), (246, 112, 60), (255, 168, 96), (255, 216, 150)]
RUBY = [(255, 238, 228), (255, 150, 150), (236, 64, 78), (190, 28, 52), (134, 14, 40), (80, 6, 28)]
GOLD = [(255, 242, 180), (252, 204, 96), (206, 142, 52), (150, 96, 34), (96, 58, 24)]
STEEL = [(255, 255, 255), (214, 218, 232), (160, 166, 188), (104, 108, 132), (60, 62, 82)]
RIM_HOT, RIM = (255, 206, 150), (242, 104, 70)
# boss palettes (from the game's generators)
ROBE = [(140, 120, 178), (104, 86, 140), (74, 60, 106), (52, 42, 78), (32, 26, 52)]
INNER = [(84, 120, 96), (60, 92, 72), (42, 68, 54), (30, 48, 40), (20, 32, 28)]
SKULL = [(230, 232, 210), (196, 198, 176), (150, 152, 132), (106, 108, 94), (68, 70, 62)]
BRONZE = [(214, 186, 120), (170, 138, 84), (124, 98, 60), (86, 66, 44), (56, 42, 32)]
WOOD = [(150, 112, 80), (118, 84, 60), (88, 62, 44), (62, 42, 32), (42, 28, 22)]
GREEN = [(230, 255, 230), (130, 255, 160), (50, 200, 100), (24, 120, 60)]
SKIN = [(184, 222, 128), (146, 188, 98), (108, 150, 76), (78, 112, 58), (52, 78, 44)]
IRON = [(232, 234, 242), (182, 186, 200), (134, 138, 156), (94, 98, 118), (62, 64, 82)]
CAPE = [(214, 66, 60), (170, 42, 46), (128, 28, 38), (92, 20, 30), (62, 14, 24)]
FUR = [(176, 156, 130), (140, 122, 100), (108, 92, 76), (80, 66, 56), (56, 46, 40)]
BONE = [(250, 244, 222), (222, 212, 184), (184, 172, 144), (140, 130, 108), (100, 92, 78)]
SLIME = [(196, 232, 255), (120, 186, 250), (70, 136, 230), (44, 92, 190), (28, 56, 132)]
HAIR = [(255, 232, 160), (247, 200, 108), (226, 150, 72), (168, 98, 52), (112, 62, 34)]
TUNIC = [(246, 244, 236), (226, 222, 210), (188, 184, 176), (140, 138, 136), (96, 94, 98)]
TROUSERS = [(196, 198, 208), (164, 166, 176), (128, 130, 144), (104, 106, 120), (72, 74, 88)]
LEATHER = [(168, 98, 52), (128, 74, 42), (92, 62, 48), (66, 44, 34), (44, 30, 24)]


def dither(a, x, y):
    return a * 16 > BAYER[y % 4][x % 4] + 0.5


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pick(ramp, t):
    for limit, c in zip((0.55, 0.18, -0.22, -0.6), ramp):
        if t > limit:
            return c
    return ramp[-1]


# ---------------------------------------------------------------- painting layers
class Layer:
    """A canvas-sized layer of shaded shapes; outlined when flattened."""
    def __init__(self):
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.p[x, y] = tuple(c[:3]) + (255,)

    def get(self, x, y):
        return self.p[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)

    def blob(self, cx, cy, rx, ry_top, ry_bottom, ramp, light=(-0.55, -0.85), only=None):
        for y in range(max(0, int(cy - ry_top - 1)), min(H, int(cy + ry_bottom + 2))):
            for x in range(max(0, int(cx - rx - 1)), min(W, int(cx + rx + 2))):
                ry = ry_top if y + 0.5 < cy else ry_bottom
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = nx * nx + ny * ny
                if d > 1 or (only and not only(x, y)):
                    continue
                self.px(x, y, pick(ramp, nx * light[0] + ny * light[1] - (0.35 if d > 0.8 else 0)))

    def poly(self, pts, c):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        mp = m.load()
        for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(W, int(max(xs)) + 1)):
                if mp[x, y]:
                    self.px(x, y, c(x, y) if callable(c) else c)

    def limb(self, x0, y0, x1, y1, width, ramp, light_side=1):
        dx, dy = x1 - x0, y1 - y0
        length = max(0.001, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        r = width / 2
        for y in range(max(0, int(min(y0, y1) - r - 1)), min(H, int(max(y0, y1) + r + 2))):
            for x in range(max(0, int(min(x0, x1) - r - 1)), min(W, int(max(x0, x1) + r + 2))):
                t = max(0.0, min(1.0, ((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / (length * length)))
                ox, oy = x + 0.5 - (x0 + dx * t), y + 0.5 - (y0 + dy * t)
                if ox * ox + oy * oy > r * r:
                    continue
                side = (ox * nx + oy * ny) / r * light_side
                self.px(x, y, pick(ramp, side * 0.8 - 0.05))


def flatten(layers):
    """Stack layers, each with a dark outline (pixel-art style)."""
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for layer in layers:
        im = layer.im if isinstance(layer, Layer) else layer
        o = im.copy()
        src, dst = im.load(), o.load()
        for y in range(H):
            for x in range(W):
                if src[x, y][3]:
                    continue
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + ox < W and 0 <= y + oy < H and src[x + ox, y + oy][3] == 255:
                        dst[x, y] = K + (255,)
                        break
        out.alpha_composite(o)
    return out


def light_figure(im, toward, ambient=0.78, warm=0.16, rim_width=2):
    """Bathe a painted figure in the heart's light: darker and redder away from it, a hot rim
    on the edges facing it."""
    p = im.load()
    alpha = [[p[x, y][3] for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            if not alpha[y][x]:
                continue
            r, g, b, a = p[x, y]
            dx, dy = toward[0] - x, toward[1] - y
            d = math.hypot(dx, dy) or 1
            c = lerp((int(r * ambient), int(g * ambient), int(b * ambient)), (120, 18, 40), warm)
            ux, uy = dx / d, dy / d
            for k in range(1, rim_width + 1):
                nx, ny = round(x + ux * k), round(y + uy * k)
                if not (0 <= nx < W and 0 <= ny < H) or not alpha[ny][nx]:
                    c = lerp(c, RIM_HOT if k == 1 else RIM, 0.75 if k == 1 else 0.5)
                    break
            p[x, y] = c + (a,)
    return im


def glow(cv, cx, cy, r, color, strength):
    p = cv.load()
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1 and dither((1 - d) ** 2 * strength, x, y):
                p[x, y] = lerp(p[x, y][:3], color, 0.55) + (255,)


# ---------------------------------------------------------------- the hall and its light
def hall(cv):
    p = cv.load()
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - CX) / 175, (y - CY) / 150)
            level = (1 - d) ** 1.35 * 10.6 if d < 1 else 0
            a = math.atan2(y - CY, x - CX)
            level += (math.sin(a * 9 + 1.3) * 0.5 + 0.5) ** 10 * max(0.0, 1 - d) * 1.5
            # stone brick wall of the hall, picked out by the light
            row = y // 9
            bx = (x + (11 if row % 2 else 0)) % 22
            if y < 196 and (y % 9 == 0 or bx == 0):
                level -= 1.1
            if y > 196:
                level -= (y - 196) / 10
            level = max(0.0, min(len(LIGHT) - 1.001, level))
            i = int(level)
            p[x, y] = (LIGHT[i + 1] if dither(level - i, x, y) else LIGHT[i]) + (255,)
    d = ImageDraw.Draw(cv)
    for tx in (112, 202):                                         # wall torches either side of the heart
        glow(cv, tx, 150, 22, (255, 170, 80), 0.6)
        d.rectangle((tx - 1, 152, tx + 1, 160), fill=(60, 50, 60))
        d.rectangle((tx - 3, 150, tx + 3, 152), fill=(90, 80, 92))
        d.polygon([(tx - 3, 150), (tx, 141), (tx + 3, 150)], fill=(255, 150, 50))
        d.polygon([(tx - 1, 150), (tx, 144), (tx + 1, 150)], fill=(255, 236, 140))


def steps(cv):
    d = ImageDraw.Draw(cv)
    rows = [(196, 92, 222), (207, 68, 246), (219, 40, 274), (232, 6, 309)]
    for i, (y, x0, x1) in enumerate(rows):
        d.rectangle((x0, y, x1, H), fill=lerp((26, 6, 18), (64, 14, 30), (3 - i) / 3))
        d.line((x0, y, x1, y), fill=lerp((150, 34, 40), (255, 140, 90), (3 - i) / 3))
        d.line((x0, y + 1, x1, y + 1), fill=lerp((80, 14, 30), (170, 50, 46), (3 - i) / 3))
        for x in range(x0 + 7, x1, 13 + i * 2):
            d.line((x, y + 2, x, y + 6), fill=(14, 3, 10))
    glow(cv, CX, 222, 62, (255, 120, 80), 0.45)


# ---------------------------------------------------------------- the heart and the sword
def heart_in(x, y, s):
    px_, py_ = x + 0.5, y + 0.5
    r = s * 0.6
    for lx in (CX - s * 0.52, CX + s * 0.52):
        if (px_ - lx) ** 2 + (py_ - (CY - s * 0.28)) ** 2 <= r * r:
            return True
    top, tip = CY - s * 0.2, CY + s * 1.12
    if top <= py_ <= tip:
        half = (s * 1.1) * (1 - (py_ - top) / (tip - top)) ** 0.85
        return abs(px_ - CX) <= half
    return False


def outline_mask(cv, mask):
    mp, p = mask.load(), cv.load()
    for y in range(H):
        for x in range(W):
            if not mp[x, y] and any(0 <= x + ox < W and 0 <= y + oy < H and mp[x + ox, y + oy]
                                    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p[x, y] = K + (255,)


def heart_and_sword(cv):
    s = 36
    glow(cv, CX, CY, 90, (255, 120, 90), 0.5)
    p = cv.load()
    d = ImageDraw.Draw(cv)
    top, guard, tip = 44, 62, 166
    blade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(blade).polygon([(CX - 5, guard), (CX + 5, guard), (CX + 5, tip - 14), (CX, tip), (CX - 5, tip - 14)], fill=255)
    outline_mask(cv, blade)
    bp = blade.load()
    for y in range(H):
        for x in range(W):
            if bp[x, y]:
                c = STEEL[1] if x < CX - 1 else STEEL[0] if x <= CX else STEEL[2]
                if x in (CX - 5, CX + 5):
                    c = STEEL[3]
                p[x, y] = c + (255,)
    hm = Image.new("L", (W, H), 0)
    hp = hm.load()
    for y in range(H):
        for x in range(W):
            if heart_in(x, y, s):
                hp[x, y] = 255
    outline_mask(cv, hm)
    for y in range(H):
        for x in range(W):
            if not hp[x, y]:
                continue
            t = math.hypot((x - CX + 9) / 32, (y - CY + 6) / 28) * 4.2
            if not heart_in(x, y, s * 0.92):
                t += 1.0
            if (x - CX) > (y - CY) * 0.4 + 6:
                t += 0.6
            if (y - CY) > 14 - abs(x - CX) * 0.3:
                t += 0.5
            i = max(0, min(len(RUBY) - 2, int(t)))
            p[x, y] = (RUBY[i + 1] if dither(t - int(t), x, y) else RUBY[i]) + (255,)
    # blood smeared on the steel below the heart
    bottom_of_heart = max(y for y in range(H) if hp[CX, y])
    for y in range(bottom_of_heart + 1, tip):
        if (y * 7) % 5 < 3:
            p[CX, y] = RUBY[3] + (255,)
            if y % 3 == 0:
                p[CX + 1, y] = RUBY[2] + (255,)
    d.ellipse((CX - 25, CY - 21, CX - 12, CY - 12), fill=RUBY[1])
    d.ellipse((CX - 22, CY - 20, CX - 17, CY - 16), fill=RUBY[0])
    for sx, sy in ((CX + 15, CY - 17), (CX - 28, CY + 2)):
        d.point((sx, sy), fill=RUBY[0])
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.point((sx + ox, sy + oy), fill=RUBY[1])
    # the wound the blade makes going in at the top and out at the bottom: dark, torn, bleeding
    for wy in (min(y for y in range(H) if hp[CX, y]), bottom_of_heart):
        for ox in range(-7, 8):
            for oy in range(-2, 3):
                if abs(ox) / 7 + abs(oy) / 2.5 < 1 and hp[CX + ox, wy + oy] if 0 <= wy + oy < H else False:
                    p[CX + ox, wy + oy] = (RUBY[5] if abs(ox) > 3 else (40, 2, 14)) + (255,)
    x = CX
    for y in range(CY - 24, CY + 28):                            # burning crack along the blade
        if not hp[x, y]:
            continue
        p[x, y] = GOLD[0] + (255,)
        p[x + 1, y] = GOLD[1] + (255,)
        p[x - 1, y] = RUBY[4] + (255,)
        if y % 6 == 0:
            x = max(CX - 2, min(CX + 2, x + rnd.choice((-1, 1))))
    hilt = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hilt)
    hd.rectangle((CX - 22, guard - 4, CX + 22, guard + 1), fill=255)
    hd.polygon([(CX - 26, guard - 2), (CX - 22, guard - 6), (CX - 22, guard + 2)], fill=255)
    hd.polygon([(CX + 26, guard - 2), (CX + 22, guard - 6), (CX + 22, guard + 2)], fill=255)
    hd.rectangle((CX - 3, top + 6, CX + 3, guard - 4), fill=255)
    hd.ellipse((CX - 6, top - 2, CX + 6, top + 8), fill=255)
    outline_mask(cv, hilt)
    hpx = hilt.load()
    for y in range(H):
        for x in range(W):
            if hpx[x, y]:
                if y >= guard - 6:
                    c = GOLD[0] if y == guard - 4 else GOLD[1] if y < guard else GOLD[2]
                elif y >= top + 6:
                    c = (150, 96, 58) if (y + x) % 3 else (98, 58, 36)
                else:
                    c = GOLD[1] if (x - CX) + (y - top) < 4 else GOLD[2]
                p[x, y] = c + (255,)
    p[CX, top + 3] = (230, 40, 60, 255)
    p[CX - 1, top + 2] = (255, 140, 140, 255)
    bottoms = {x: max(y for y in range(H) if hp[x, y]) for x in range(CX - 30, CX + 31) if any(hp[x, y] for y in range(H))}
    for dx, length in ((-14, 9), (-6, 13), (9, 11), (17, 6)):
        bx = CX + dx
        if bx in bottoms:
            for y in range(bottoms[bx] + 1, bottoms[bx] + length):
                p[bx, y] = RUBY[3] + (255,)
            p[bx, bottoms[bx] + length] = RUBY[2] + (255,)
    for y in (tip + 3, tip + 7):
        p[CX, y] = RUBY[2] + (255,)


# ---------------------------------------------------------------- the Ancient Lich (left)
def paint_lich():
    staff, robe, panel, arm, mantle, hood, face, crown, top = (Layer() for _ in range(9))
    lit = (0.7, -0.55)                                            # light comes from the heart, to the right
    staff.limb(30, 250, 36, 66, 5, WOOD)
    for ky in range(80, 250, 22):                                 # knots on the gnarled staff
        staff.blob(31 + (250 - ky) * 0.03, ky, 3.5, 2.5, 2.5, WOOD)
    top.blob(36, 58, 7, 6, 5, SKULL, light=lit)                    # horned skull on the staff
    for dx in (-1, 1):
        top.limb(36 + dx * 5, 55, 36 + dx * 11, 44, 3, BONE)
    top.px(33, 58, (10, 30, 16))
    top.px(39, 58, (10, 30, 16))
    robe.poly([(0, 250), (6, 150), (24, 126), (94, 126), (106, 162), (112, 250)],
              lambda x, y: pick(ROBE, (x - 56) / 56 * 0.9 - 0.15 - (0.3 if (x + y // 4) % 9 == 0 else 0)))
    for y0, reach in ((168, 12), (196, 16), (226, 11)):           # a few big ragged tatters
        robe.poly([(106, y0), (106 + reach, y0 + 14), (110, y0 + 10), (104, y0 + 22)], lambda x, yy: ROBE[2])
    panel.poly([(48, 130), (68, 130), (74, 250), (42, 250)], lambda x, y: pick(INNER, -abs(x - 58) / 16))
    for ry in range(142, 250, 12):                                # glowing runes down the panel
        for ox, oy in ((0, 0), (-1, 1), (1, 1), (0, 2), (0, 3)):
            panel.px(58 + ox, ry + oy, GREEN[1])
    for y in range(130, 250):
        t = (y - 130) / 120
        panel.px(48 - 6 * t, y, BRONZE[2])
        panel.px(68 + 6 * t, y, BRONZE[2])
    mantle.blob(58, 128, 48, 11, 11, ROBE, light=lit)
    for sx, d in ((16, -1), (100, 1)):                            # bone spikes on the shoulders
        mantle.blob(sx, 126, 8, 6, 6, BONE, light=lit)
        for ox, h in ((-2, 14), (5, 9)):
            mantle.poly([(sx + ox * d - 3, 122), (sx + ox * d + d * 5, 122 - h), (sx + ox * d + 3, 122)], lambda x, y: BONE[1])
    mantle.blob(58, 144, 6, 6, 6, BRONZE, light=lit)              # phylactery
    mantle.blob(58, 144, 3.5, 3.5, 3.5, GREEN[1:], light=lit)
    for i in range(-14, 15):                                     # its chain
        mantle.px(58 + i, 134 + abs(i) // 2, BRONZE[2] if i % 2 else BRONZE[3])
    arm.limb(94, 134, 116, 158, 12, ROBE)                         # sleeve reaching toward the heart
    arm.blob(117, 159, 7, 5, 6, ROBE, light=lit)
    for fx, fy, ex, ey in ((120, 156, 134, 148), (121, 160, 137, 158), (119, 163, 132, 168)):   # bony claws
        arm.limb(fx, fy, ex, ey, 3, SKULL)
    hood.blob(58, 100, 30, 34, 28, ROBE, light=lit)
    hood.poly([(38, 82), (58, 62), (80, 82)], lambda x, y: ROBE[2])
    hood.blob(58, 106, 18, 20, 18, [(8, 4, 12)] * 5)               # the dark inside the hood
    face.blob(58, 104, 12, 12, 10, SKULL, light=(0.6, 0.4))
    face.blob(58, 116, 7, 3, 3, SKULL, light=(0.6, 0.4))
    for y in range(92, 98):                                       # the hood's shadow over the brow
        for x in range(46, 71):
            if face.get(x, y)[3]:
                face.px(x, y, SKULL[4])
    for ex in (52, 63):
        face.blob(ex, 104, 3.2, 3.2, 3.2, [(8, 18, 12)] * 5)
    face.rect = None
    for tx in range(53, 64, 2):
        face.px(tx, 117, (10, 6, 10))
    face.px(57, 110, (10, 6, 10))
    face.px(59, 110, (10, 6, 10))
    crown.poly([(36, 78), (80, 78), (80, 84), (36, 84)], lambda x, y: BRONZE[1] if y < 80 else BRONZE[2])
    for i, (dx, h) in enumerate(((-20, 9), (-11, 6), (-2, 13), (7, 6), (16, 10))):
        crown.poly([(58 + dx - 3, 79), (58 + dx + 1, 79 - h), (58 + dx + 5, 79)], lambda x, y: BRONZE[1] if x < 58 + dx + 1 else BRONZE[3])
    for gx in (46, 58, 70):
        crown.px(gx, 81, GREEN[1])
    im = flatten([staff, robe, panel, mantle, arm, hood, face, crown, top])
    im = light_figure(im, (CX, CY), ambient=0.8, warm=0.14)
    p = im.load()
    for y in range(205, 250):                                    # the robe dissolving into wisps
        fade = (y - 205) / 45
        for x in range(0, 125):
            r, g, b, a = p[x, y]
            if a and not dither(1 - fade * 0.85, x, y):
                p[x, y] = (0, 0, 0, 0)
    return im


def lich_effects(cv):
    d = ImageDraw.Draw(cv)
    for ex in (52, 63):                                           # soul-fire in the eye sockets
        glow(cv, ex, 104, 10, (60, 230, 110), 0.7)
        d.rectangle((ex - 1, 103, ex + 1, 105), fill=GREEN[1])
        d.point((ex, 103), fill=GREEN[0])
        for k in range(1, 7):
            if rnd.random() < 0.8:
                d.point((ex + rnd.randint(-1, 1), 103 - k), fill=GREEN[1] if k < 4 else GREEN[2])
    glow(cv, 58, 144, 12, (80, 255, 140), 0.6)
    fx, fy = 36, 44                                              # green flame wreathing the staff's skull
    glow(cv, fx, fy + 6, 26, (70, 230, 120), 0.75)
    for i in range(14):
        h = rnd.randint(6, 16)
        x = fx + rnd.randint(-7, 7)
        for k in range(h):
            if rnd.random() < 0.85:
                d.point((x + rnd.randint(-1, 1), fy + 10 - k), fill=GREEN[0] if k < 3 else GREEN[1] if k < 9 else GREEN[2])
    for _ in range(22):                                          # soul motes drifting about it
        x, y = rnd.randint(4, 120), rnd.randint(60, 230)
        d.point((x, y), fill=GREEN[1] if rnd.random() < 0.6 else GREEN[0])


# ---------------------------------------------------------------- the Orc Warlord (right)
def paint_orc():
    cape, axe, body, arm, shoulders, head, helm, horns, hands = (Layer() for _ in range(9))
    lit = (-0.7, -0.55)                                           # light from the heart, to the left
    cape.poly([(214, 140), (315, 140), (315, 250), (204, 250)], lambda x, y: pick(CAPE, (262 - x) / 60 - 0.2 - (0.3 if (x + y // 6) % 7 == 0 else 0)))
    # breastplate: a broad torso narrowing to the waist, with overlapping plates
    body.poly([(226, 146), (298, 146), (292, 196), (284, 250), (240, 250), (232, 196)],
              lambda x, y: pick(IRON, (262 - x) / 34 * 0.9 - (y - 146) / 160))
    for sy in (170, 194, 218):
        for x in range(226, 300):
            if body.get(x, sy)[3]:
                body.px(x, sy, IRON[4])
                body.px(x, sy + 1, IRON[1] if x < 262 else IRON[2])
    for x in range(240, 286):                                     # sword belt across the waist
        for y in (226, 227, 228):
            if body.get(x, y)[3]:
                body.px(x, y, LEATHER[1] if y == 226 else LEATHER[2])
    for rx, ry in ((238, 162), (286, 162), (240, 186), (284, 186)):
        body.px(rx, ry, IRON[0])
    body.blob(262, 168, 10, 8, 8, BONE, light=lit)                # skull emblem on the chest
    body.px(259, 168, K)
    body.px(265, 168, K)
    shoulders.blob(262, 136, 36, 9, 9, FUR, light=lit)            # fur collar
    for sx, mirror in ((222, -1), (302, 1)):                     # spiked pauldrons
        shoulders.blob(sx, 142, 24, 18, 15, IRON, light=lit)
        for i, dx in enumerate((-10, 0, 10)):
            shoulders.poly([(sx + dx - 4, 128 + abs(dx) // 3), (sx + dx + mirror * 3, 108 + abs(dx) // 2), (sx + dx + 4, 128 + abs(dx) // 3)],
                           lambda x, y: BONE[1] if x < sx + dx else BONE[2])
    # the axe, raised overhead on the outer side, and the arm holding it
    axe.limb(306, 250, 300, 12, 5, WOOD, light_side=-1)
    for side in (-1, 1):
        cx_, cy_ = 300 + side * 2, 28
        pts = [(cx_, 14), (cx_ + side * 26, 4), (cx_ + side * 34, 28), (cx_ + side * 26, 54), (cx_, 44)]
        axe.poly(pts, lambda x, y, side=side: pick(IRON, (-side) * (x - 300) / 30 * 0.8 - (y - 28) / 40 * 0.5))
    arm.blob(300, 128, 11, 12, 12, SKIN, light=lit)                # bulging shoulder / bicep
    arm.limb(300, 132, 304, 96, 18, SKIN, light_side=-1)
    arm.blob(304, 98, 11, 7, 7, LEATHER, light=lit)               # bracer
    hands.blob(303, 84, 8, 7, 7, SKIN, light=lit)                 # fist round the haft
    head.blob(256, 112, 24, 22, 24, SKIN, light=lit)
    head.blob(256, 126, 18, 9, 9, SKIN, light=lit)                # heavy jaw
    for i in range(14):                                           # brow
        head.px(244 + i, 104 + (1 if 4 < i < 10 else 0), SKIN[4])
    for ex in (247, 262):
        head.blob(ex + 2, 109, 4, 2.5, 2.5, [(255, 64, 48)] * 5)
    head.poly([(242, 132), (246, 132), (244, 118)], lambda x, y: BONE[0] if x < 244 else BONE[2])   # tusks
    head.poly([(266, 132), (270, 132), (268, 118)], lambda x, y: BONE[0] if x < 268 else BONE[2])
    head.poly([(248, 128), (264, 128), (262, 131), (250, 131)], lambda x, y: (60, 26, 34))         # mouth
    helm.blob(256, 99, 24, 21, 4, IRON, light=lit, only=lambda x, y: y <= 99)
    helm.poly([(230, 96), (282, 96), (282, 100), (230, 100)], lambda x, y: IRON[3])
    for rx in (236, 246, 266, 276):
        helm.px(rx, 98, IRON[0])
    helm.poly([(254, 96), (258, 96), (258, 112), (254, 112)], lambda x, y: IRON[1] if x < 256 else IRON[3])   # nose guard
    horns.limb(236, 90, 218, 74, 11, BONE)                        # thick curved horns
    horns.limb(218, 74, 208, 52, 8, BONE)
    horns.limb(208, 52, 210, 34, 5, BONE)
    horns.limb(210, 34, 216, 24, 2.5, BONE)
    horns.limb(276, 90, 292, 74, 11, BONE, light_side=-1)
    horns.limb(292, 74, 300, 54, 8, BONE, light_side=-1)
    im = flatten([cape, axe, body, shoulders, arm, hands, head, helm, horns])
    return light_figure(im, (CX, CY), ambient=0.82, warm=0.12)


def orc_effects(cv):
    d = ImageDraw.Draw(cv)
    for ex in (249, 264):
        glow(cv, ex, 109, 9, (255, 50, 30), 0.75)
        d.rectangle((ex - 2, 108, ex + 2, 110), fill=(255, 70, 50))
        d.rectangle((ex - 1, 108, ex, 108), fill=(255, 225, 180))
    d.line((276, 6, 268, 28), fill=STEEL[0])                      # the axe's edge catching the light
    d.line((268, 28, 276, 52), fill=STEEL[1])


# ---------------------------------------------------------------- the King Slime (bottom right)
def paint_slime():
    body, crown, face = Layer(), Layer(), Layer()
    body.blob(270, 232, 46, 34, 24, SLIME, light=(-0.6, -0.8))
    for dx, length in ((-30, 9), (-12, 6), (16, 8)):             # drips
        body.limb(270 + dx, 246, 270 + dx, 246 + length, 4, SLIME)
    body.blob(252, 214, 9, 5, 4, [SLIME[0]] * 5)                  # gloss
    crown.poly([(250, 206), (292, 206), (292, 198), (285, 188), (279, 199), (271, 184), (263, 199), (257, 188), (250, 198)],
               lambda x, y: GOLD[1] if x < 271 else GOLD[2])
    for gx, c in ((258, (226, 44, 66)), (271, (90, 200, 255)), (284, (226, 44, 66))):
        crown.px(gx, 202, c)
        crown.px(gx + 1, 202, c)
    for ex, brow in ((256, 1), (282, -1)):                        # angry eyes
        face.blob(ex, 228, 6, 5, 5, [(250, 250, 255)] * 5)
        face.blob(ex + brow, 229, 2.5, 3, 3, [(14, 10, 26)] * 5)
        for i in range(9):
            face.px(ex - 4 + i, 221 + (i * brow) // 3 - (2 if brow > 0 else -1), (20, 30, 70))
    face.poly([(262, 240), (278, 240), (274, 243), (266, 243)], lambda x, y: (20, 30, 70))
    im = flatten([body, crown, face])
    return light_figure(im, (CX, CY), ambient=0.9, warm=0.08)


# ---------------------------------------------------------------- the knight (from behind)
def paint_knight():
    legs, body, arms, hair, sword = (Layer() for _ in range(5))
    cx, feet = CX, 247
    for lx, fx in ((cx - 6, cx - 9), (cx + 6, cx + 9)):
        legs.limb(lx, feet - 24, fx, feet - 5, 8, TROUSERS)
        legs.blob(fx, feet - 3, 5.5, 3, 3, LEATHER, light=(0, -1))
    body.blob(cx, feet - 34, 15, 13, 11, TUNIC, light=(0.1, -1))  # white tunic
    for x in range(cx - 14, cx + 15):                             # brown belt
        for y in (feet - 25, feet - 24):
            if body.get(x, y)[3]:
                body.px(x, y, LEATHER[1] if y == feet - 25 else LEATHER[2])
    for x in range(cx - 9, cx + 10, 4):                           # folds of the tunic's back
        for y in range(feet - 42, feet - 27):
            if body.get(x, y)[3]:
                body.px(x, y, TUNIC[2])
    arms.limb(cx - 15, feet - 42, cx - 19, feet - 26, 7, TUNIC)
    arms.blob(cx - 19, feet - 24, 3.5, 3, 3, [(245, 192, 150), (226, 168, 128), (212, 138, 104), (170, 104, 80), (120, 70, 56)])
    arms.limb(cx + 15, feet - 42, cx + 22, feet - 28, 7, TUNIC)
    arms.blob(cx + 23, feet - 26, 3.5, 3, 3, [(245, 192, 150), (226, 168, 128), (212, 138, 104), (170, 104, 80), (120, 70, 56)])
    # the big mop of blond hair that is the knight's whole look
    hair.blob(cx, feet - 62, 19, 17, 15, HAIR, light=(0.1, -1))
    hair.blob(cx - 13, feet - 51, 7, 7, 6, HAIR, light=(0.1, -1))
    hair.blob(cx + 13, feet - 51, 7, 7, 6, HAIR, light=(0.1, -1))
    for sx in range(cx - 14, cx + 15, 5):                         # strands
        for y in range(feet - 68, feet - 46):
            if hair.get(sx + (y % 3 == 0), y)[3]:
                hair.px(sx + (y % 3 == 0), y, HAIR[2])
    for ex in (cx - 19, cx + 19):                                 # ears peeking out
        hair.blob(ex, feet - 52, 2.5, 3, 3, [(245, 192, 150), (226, 168, 128), (212, 138, 104), (170, 104, 80), (120, 70, 56)])
    # his sword, lowered, point on the step
    sword.limb(cx + 25, feet - 26, cx + 46, feet - 1, 4, STEEL, light_side=-1)
    sword.limb(cx + 19, feet - 31, cx + 29, feet - 21, 3, GOLD)   # crossguard
    sword.limb(cx + 22, feet - 31, cx + 25, feet - 27, 3, LEATHER)
    im = flatten([legs, sword, body, arms, hair])
    return light_figure(im, (CX, CY), ambient=0.95, warm=0.05, rim_width=1)


# ---------------------------------------------------------------- the game's monsters
def monster(name, row=0, col=0, flip=False):
    sheet = Image.open(os.path.join(MONSTERS, name, f"{name}_Sheet.png")).convert("RGBA")
    im = sheet.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def place_monster(cv, im, x, feet, shadow=True):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(im, (int(x - 16), int(feet - 32)))
    layer = light_figure(layer, (CX, CY), ambient=0.82, warm=0.12, rim_width=1)
    if shadow:
        ImageDraw.Draw(cv).ellipse((x - 9, feet - 3, x + 9, feet + 1), fill=(10, 2, 9))
    cv.alpha_composite(layer)


# ---------------------------------------------------------------- finish
def embers(cv):
    p = cv.load()
    for _ in range(120):
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        c = rnd.choice([(255, 190, 110), (255, 140, 60), (255, 230, 170), (240, 70, 60)])
        p[x, y] = c + (255,)
        if rnd.random() < 0.25:
            for ox, oy in ((1, 0), (0, 1), (1, 1)):
                if x + ox < W and y + oy < H:
                    p[x + ox, y + oy] = c + (255,)
        elif rnd.random() < 0.4 and y + 2 < H:
            p[x, y + 1] = lerp(c, (60, 10, 20), 0.5) + (255,)
            p[x, y + 2] = lerp(c, (40, 8, 16), 0.75) + (255,)


def vignette(cv):
    p = cv.load()
    for y in range(H):
        for x in range(W):
            dx, dy = x / W * 2 - 1, y / H * 2 - 1
            a = (math.sqrt(dx * dx * 0.7 + dy * dy * 0.9) - 0.82) / 0.45
            if a > 0 and dither(min(1.0, a) * 0.85, x, y):
                p[x, y] = lerp(p[x, y][:3], (4, 1, 6), 0.7) + (255,)


def title(cv):
    font = ImageFont.truetype(os.path.join(FONTS, "Jacquard24-Regular.ttf"), 48)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.fontmode = "1"
    text = "Hearts for Power"
    w = d.textlength(text, font=font)
    d.text((int((W - w) / 2), -4), text, font=font, fill=255)
    top, bottom = m.getbbox()[1], m.getbbox()[3]
    mp, p = m.load(), cv.load()
    pts = [(x, y) for y in range(H) for x in range(W) if mp[x, y]]
    near = {}
    for x, y in pts:
        for oy in range(-6, 7):
            for ox in range(-6, 7):
                nx, ny = x + ox, y + oy
                if 0 <= nx < W and 0 <= ny < H:
                    near[(nx, ny)] = min(near.get((nx, ny), 99), math.hypot(ox, oy))
    for (x, y), dist in near.items():
        if mp[x, y]:
            continue
        if dist <= 2.2:
            p[x, y] = ((70, 4, 18) if y > top + (bottom - top) * 0.6 and dist > 1.1 else K) + (255,)
        elif dither((1 - dist / 6.5) * 0.7, x, y):
            p[x, y] = lerp(p[x, y][:3], (190, 24, 44), 0.6) + (255,)
    for x, y in pts:
        for oy in (1, 2, 3):
            if y + oy < H and not mp[x, y + oy]:
                p[x, y + oy] = (90, 6, 22, 255)
    grad = [(255, 246, 200), (255, 206, 120), (252, 140, 80), (238, 60, 60), (196, 26, 46), (150, 14, 38)]
    for x, y in pts:
        level = (y - top) / max(1, bottom - top) * (len(grad) - 1)
        i = int(level)
        p[x, y] = (grad[min(len(grad) - 1, i + 1)] if dither(level - i, x, y) else grad[i]) + (255,)


def main():
    cv = Image.new("RGBA", (W, H), LIGHT[0] + (255,))
    hall(cv)
    heart_and_sword(cv)
    steps(cv)
    cv.alpha_composite(paint_orc())
    orc_effects(cv)
    cv.alpha_composite(paint_lich())
    lich_effects(cv)
    # the game's monsters creeping in from the dark
    place_monster(cv, monster("Spirit", 0, 1), 104, 196, shadow=False)
    place_monster(cv, monster("Bat", 0, 2), 208, 74, shadow=False)
    place_monster(cv, monster("Ghost", 0, 1), 226, 178, shadow=False)
    place_monster(cv, monster("Skeleton", 2, 0, flip=True), 200, 219)
    place_monster(cv, monster("Goblin", 2, 1), 112, 219)
    place_monster(cv, monster("Mimic", 3, 3), 84, 244)
    place_monster(cv, monster("Slime", 0, 0), 30, 248)
    cv.alpha_composite(paint_slime())
    heart = Image.open(os.path.join(SPRITES, "UI", "Heart_full.png")).convert("RGBA")
    for hx, hy in ((132, 208), (184, 232)):                      # hearts lying on the steps
        glow(cv, hx, hy - 4, 10, (255, 70, 90), 0.6)
        cv.alpha_composite(heart, (hx - 5, hy - 10))
    ImageDraw.Draw(cv).ellipse((CX - 22, 245, CX + 30, 250), fill=(10, 2, 9))
    cv.alpha_composite(paint_knight())
    embers(cv)
    vignette(cv)
    title(cv)
    out = cv.convert("RGB").resize((W * 2, H * 2), Image.NEAREST)
    path = os.path.join(HERE, "cover_630x500.png")
    out.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
