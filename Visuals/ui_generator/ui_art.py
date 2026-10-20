"""Menu art for the title / pause / settings / death screens -> Assets/Resources/Sprites/UI:
  TitleEmblem   a big pixel-art heart pierced by a sword, dripping blood, wrapped in a thorny chain
  Panel         a dark stone tablet with an iron rim and corner studs (9-sliced, so it stretches)
  Divider       a thin ornamental line with a little heart in the middle
Run: python ui_art.py"""
import hashlib
import math
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fx_generator"))
from fx import meta, folder_meta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Resources", "Sprites", "UI"))
K = (24, 18, 26)
RED = [(255, 120, 130), (232, 54, 70), (186, 28, 50), (130, 14, 36), (82, 8, 24)]
STEEL = [(240, 242, 250), (200, 204, 218), (150, 154, 172), (104, 108, 126), (66, 68, 84)]
GOLD = [(255, 230, 130), (236, 186, 70), (186, 130, 44), (130, 86, 30)]
STONE = [(78, 72, 88), (62, 56, 72), (48, 43, 57), (36, 32, 44), (26, 22, 32)]
IRON = [(150, 146, 160), (110, 106, 122), (78, 74, 90), (52, 48, 62)]


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), tuple(c[:3]) + ((c[3],) if len(c) == 4 else (255,)))


def get(im, x, y):
    return im.getpixel((x, y)) if 0 <= x < im.width and 0 <= y < im.height else (0, 0, 0, 0)


def outline(im, color=K):
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if get(im, x, y)[3] > 0:
                continue
            if any(get(im, x + dx, y + dy)[3] > 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                put(out, x, y, color)
    return out


def pick(ramp, t):
    for limit, c in zip((0.55, 0.18, -0.22, -0.6), ramp):
        if t > limit:
            return c
    return ramp[-1]


# ---------------------------------------------------------------- the emblem
def heart_shape(x, y, cx, cy, s):
    """Classic implicit heart curve, scaled by s around (cx, cy)."""
    u = (x + 0.5 - cx) / s
    v = -(y + 0.5 - cy) / s
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


def emblem():
    """A heart run clean through by a sword: the sword is drawn first and the heart over it, so the
    hilt stands out of the top, the blade disappears inside, and the bloody tip bursts out below.
    Torn wounds where it goes in and comes out, blood running down."""
    W, H = 118, 122
    im = new(W, H)
    cx, cy, s = 58, 66, 31
    # --- the sword along a diagonal, upper right -> lower left
    angle = math.radians(32)                                   # leaning: hilt top-right, tip bottom-left
    ux, uy = -math.sin(angle), math.cos(angle)                 # unit vector down the blade
    px_, py_ = math.cos(angle), math.sin(angle)                # across the blade
    hx, hy = cx + 40, cy - 62                                  # pommel position (hilt well clear of the heart)
    length = 118

    def blade_point(along, across):
        return hx + ux * along + px_ * across, hy + uy * along + py_ * across

    sword = new(W, H)
    for a10 in range(0, length * 10):
        along = a10 / 10
        if along < 4:                                          # pommel
            half, cols = 2.5, lambda q: GOLD[0] if q < 0 else GOLD[2]
        elif along < 17:                                       # leather grip
            half, cols = 1.8, lambda q, a=along: (110, 70, 44) if int(a) % 3 else (76, 46, 30)
        elif along < 20:                                       # crossguard
            half, cols = 12, lambda q: GOLD[1] if q < 0 else GOLD[2]
        else:                                                  # blade, tapering to the point
            half = 4.2 if along < length - 14 else max(0.4, 4.2 * (length - along) / 14)
            cols = lambda q, h=half: STEEL[3] if abs(q) > h - 0.9 else STEEL[0] if q < -0.5 else STEEL[2] if q > 0.5 else STEEL[1]
        for q10 in range(int(-half * 10), int(half * 10) + 1, 4):
            q = q10 / 10
            x, y = blade_point(along, q)
            put(sword, x, y, cols(q))
    sword = outline(sword)
    # blood smeared on the steel that has been through the heart (the tip end)
    for a10 in range(int((length - 40) * 10), length * 10, 7):
        along = a10 / 10
        for q in (-1, 0, 1, 2):
            if (int(along) * 7 + q * 3) % 5 < 3:
                x, y = blade_point(along, q * 0.9)
                if get(sword, int(round(x)), int(round(y)))[3] and get(sword, int(round(x)), int(round(y)))[:3] != K:
                    put(sword, x, y, RED[2] if (int(along) + q) % 3 else RED[1])
    im.alpha_composite(sword)

    # --- the heart on top, hiding the middle of the blade
    heart = new(W, H)
    for y in range(H):
        for x in range(W):
            if not heart_shape(x, y, cx, cy, s):
                continue
            t = -((x - cx) / 40) - ((y - cy) / 40) * 1.2
            if not heart_shape(x, y, cx, cy, s * 0.9):
                t -= 0.5
            put(heart, x, y, pick(RED, t))
    for y in range(H):                                         # glossy highlight
        for x in range(W):
            if ((x - cx + 18) / 7) ** 2 + ((y - cy + 16) / 4.5) ** 2 <= 1:
                put(heart, x, y, RED[0])
            if ((x - cx + 20) / 2.2) ** 2 + ((y - cy + 17) / 1.6) ** 2 <= 1:
                put(heart, x, y, (255, 220, 224))
    heart = outline(heart)
    im.alpha_composite(heart)

    # --- wounds where the blade enters and leaves: dark torn slits with the steel just showing
    def boundary_along(entering):
        rng_ = range(20, length) if entering else range(length - 1, 20, -1)
        for along in rng_:
            x, y = blade_point(along, 0)
            if heart_shape(int(x), int(y), cx, cy, s * 0.97):
                return along
        return None

    for entering in (True, False):
        along = boundary_along(entering)
        if along is None:
            continue
        step = 2 if entering else -2
        for k in range(0, 6):                                  # a torn opening around the blade
            a_ = along + step * k * 0.5
            for q in range(-6, 7):
                x, y = blade_point(a_, q)
                d = abs(q) / 6 + k / 7
                if d < 1:
                    put(im, x, y, RED[4] if d > 0.55 else (40, 4, 14))
        for q in range(-3, 4):                                 # the blade disappearing into the dark
            x, y = blade_point(along + step * 0.5, q)
            put(im, x, y, STEEL[3] if abs(q) == 3 else STEEL[2])
        # blood running down from the wound
        wx, wy = blade_point(along, 0)
        for dx, length_ in ((-4, 10), (2, 15), (6, 7)):
            bx = int(wx + dx)
            top = int(wy) + 2
            for y in range(top, min(H - 2, top + length_)):
                if get(im, bx, y)[3] == 0 or True:
                    put(im, bx, y, RED[2] if y < top + length_ - 1 else RED[1])
            put(im, bx + 1, min(H - 2, top + length_ - 1), RED[2])

    # drops falling from the tip of the blade
    tx, ty = blade_point(length - 1, 0)
    for i, dy in enumerate((3, 7, 12)):
        put(im, tx, ty + dy, RED[1])
        put(im, tx, ty + dy + 1, RED[2])
    return outline(im)


# ---------------------------------------------------------------- panel (9-slice)
PANEL = 48
BORDER = 12


def panel():
    im = new(PANEL, PANEL)
    for y in range(PANEL):
        for x in range(PANEL):
            edge = min(x, y, PANEL - 1 - x, PANEL - 1 - y)
            if edge < 2:
                c = IRON[3] if edge == 0 else IRON[1]
            elif edge < 4:
                c = IRON[0] if (x < 4 or y < 4) else IRON[2]           # lit top-left rim
            elif edge < 6:
                c = STONE[4]                                           # inner shadow
            else:
                row = y // 7                                           # dark, subtle stone bricks
                bx = (x + (6 if row % 2 else 0)) % 12
                c = STONE[2] if ((x + (6 if row % 2 else 0)) // 12 + row) % 3 else (52, 47, 62)
                if y % 7 == 0 or bx == 0:
                    c = STONE[3]
            put(im, x, y, c + (245,))
    for sx, sy in ((5, 5), (PANEL - 6, 5), (5, PANEL - 6), (PANEL - 6, PANEL - 6)):   # iron studs
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                put(im, sx + dx, sy + dy, IRON[0] if dx + dy < 0 else IRON[2])
        put(im, sx - 1, sy - 1, (210, 206, 220))
    return im


def divider():
    im = new(120, 9)
    for x in range(120):
        fade = min(x, 119 - x) / 30
        if fade <= 0:
            continue
        put(im, x, 4, GOLD[1] + (int(255 * min(1, fade)),))
        put(im, x, 5, GOLD[3] + (int(200 * min(1, fade)),))
    for y in range(9):                                                 # a little heart in the middle
        for x in range(53, 67):
            if heart_shape(x, y, 60, 4.2, 4.3):
                put(im, x, y, RED[1] if x < 60 else RED[2])
    return im


def soulfire():
    """The spirits' projectile: a small green fireball with a flickering tail (drawn flying right)."""
    im = new(14, 10)
    soul = [(220, 255, 214), (140, 246, 150), (80, 210, 110), (40, 150, 80)]
    for y in range(10):
        for x in range(14):
            d = ((x - 9.5) / 4.2) ** 2 + ((y - 4.5) / 4.2) ** 2
            tail = x < 9 and abs(y - 4.5) < (x - 1) * 0.45 and (x + y) % 3 != 0
            if d <= 1 or tail:
                t = 1 - min(1, d) if d <= 1 else 0.1 + x / 30
                put(im, x, y, soul[0] if t > 0.75 else soul[1] if t > 0.4 else soul[2] if t > 0.15 else soul[3])
    return outline(im, (16, 40, 24))


def save(im, name, border=None, folder="UI"):
    root = os.path.join(os.path.dirname(ROOT), folder)
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, name + ".png")
    im.save(path)
    text = meta(hashlib.md5(f"hfp_fx_{folder}_{name}".encode()).hexdigest(), 16)
    if border:
        text = text.replace("spriteBorder: {x: 0, y: 0, z: 0, w: 0}", f"spriteBorder: {{x: {border}, y: {border}, z: {border}, w: {border}}}")
    with open(path + ".meta", "w", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    folder_meta(ROOT)
    save(emblem(), "TitleEmblem")
    save(panel(), "Panel", border=BORDER)
    save(divider(), "Divider")
    save(soulfire(), "SoulFire", folder="Effects")
    preview = Image.new("RGBA", (260, 100), (40, 30, 40, 255))
    preview.alpha_composite(emblem(), (2, 6))
    preview.alpha_composite(panel(), (104, 6))
    preview.alpha_composite(divider(), (104, 70))
    preview.resize((preview.width * 4, preview.height * 4), Image.NEAREST).save(os.path.join(os.path.dirname(__file__), "ui_preview.png"))
    print("wrote menu art")
