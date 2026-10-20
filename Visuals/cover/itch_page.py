"""Images for the itch.io page theme, in the style of the in-game title screen:
  itch_banner.png      960x210  the pierced-heart emblem and the blackletter logo on a dark vignette, with embers
  itch_profile_banner.png  the same for the profile, with the developer name
  itch_background.png  a dark, subtle stone-brick tile (the page background repeats it)
Run: python itch_page.py"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
FONTS = os.path.join(PROJ, "Assets", "Resources", "Fonts")
UI = os.path.join(PROJ, "Assets", "Resources", "Sprites", "UI")
BG = (11, 4, 16)
rnd = random.Random(5)


def banner(text="Hearts for Power", tagline="Give up your heart.  Take its power.", out="itch_banner.png"):
    S = 2                                       # drawn at 480x105, doubled -> crisp 2x pixels
    W, H = 480, 105
    im = Image.new("RGBA", (W, H), BG + (255,))
    p = im.load()
    for y in range(H):                          # a deep red glow behind the logo, fading to the page colour
        for x in range(W):
            d = math.hypot((x - W / 2) / (W * 0.55), (y - H * 0.55) / (H * 0.9))
            k = max(0.0, 1 - d) ** 1.8 * 0.55
            if k > 0:
                p[x, y] = tuple(int(BG[i] + ((120, 14, 32)[i] - BG[i]) * k) for i in range(3)) + (255,)
    emblem = Image.open(os.path.join(UI, "TitleEmblem.png")).convert("RGBA")
    emblem = emblem.resize((emblem.width * 3 // 4, emblem.height * 3 // 4), Image.NEAREST)
    im.alpha_composite(emblem, (16, (H - emblem.height) // 2))
    im.alpha_composite(emblem.transpose(Image.FLIP_LEFT_RIGHT), (W - 16 - emblem.width, (H - emblem.height) // 2))

    font = ImageFont.truetype(os.path.join(FONTS, "Jacquard24-Regular.ttf"), 48)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.fontmode = "1"
    w = d.textlength(text, font=font)
    x0, y0 = int((W - w) / 2), 18
    d.text((x0 + 2, y0 + 3), text, font=font, fill=(70, 4, 18), stroke_width=1, stroke_fill=(10, 2, 8))   # deep shadow
    d.text((x0, y0), text, font=font, fill=(232, 44, 62), stroke_width=1, stroke_fill=(10, 2, 8))
    im.alpha_composite(layer)
    tag = ImageFont.truetype(os.path.join(FONTS, "PixelifySans.ttf"), 10)
    t2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(t2)
    d2.fontmode = "1"
    tw = d2.textlength(tagline, font=tag)
    d2.text((int((W - tw) / 2), 78), tagline, font=tag, fill=(242, 220, 203), stroke_width=1, stroke_fill=(10, 2, 8))
    im.alpha_composite(t2)
    for _ in range(70):                         # embers drifting up
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        c = (255, 140, 50) if rnd.random() < 0.6 else (230, 50, 60)
        im.putpixel((x, y), c + (rnd.randint(120, 240),))
    for y in range(H):                          # fade the edges into the page background
        for x in range(W):
            e = min(x, W - 1 - x, y * 3, (H - 1 - y) * 3)
            if e < 30:
                k = (30 - e) / 30
                r, g, b, a = p[x, y]
                p[x, y] = tuple(int(c + (BG[i] - c) * k * 0.9) for i, c in enumerate((r, g, b))) + (255,)
    im.convert("RGB").resize((W * S, H * S), Image.NEAREST).save(os.path.join(HERE, out))


def background():
    """A 128x128 tile of very dark stone bricks (doubled to 256), barely lighter than the page colour."""
    W = H = 128
    im = Image.new("RGB", (W, H), BG)
    p = im.load()
    for y in range(H):
        row = y // 8
        for x in range(W):
            bx = (x + (8 if row % 2 else 0)) % 16
            shade = ((x + (8 if row % 2 else 0)) // 16 * 7 + row * 5) % 5
            c = (16 + shade, 7 + shade // 2, 22 + shade)
            if y % 8 == 7 or bx == 15:
                c = (7, 2, 10)                  # mortar
            elif y % 8 == 0:
                c = (c[0] + 4, c[1] + 2, c[2] + 5)
            p[x, y] = c
    im.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(HERE, "itch_background.png"))


if __name__ == "__main__":
    banner()
    banner("d4niel.wth", "Dark little pixel games", "itch_profile_banner.png")
    background()
    print("wrote itch_banner.png, itch_profile_banner.png and itch_background.png")
