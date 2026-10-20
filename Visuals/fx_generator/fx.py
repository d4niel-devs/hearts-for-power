"""Pixel art for the game loop: hearts, item icons, projectiles, bomb, pedestal and effect sprites.
Written to Assets/Resources/Sprites/<group>/<name>.png (+ .meta) so scripts can load them with
Resources.Load<Sprite>("Sprites/<group>/<name>"). Run: python fx.py"""
import hashlib
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Resources", "Sprites"))
K = (24, 18, 26)

SPRITES = {}   # (group, name) -> (Image, ppu)


def from_rows(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == '.':
                continue
            im.putpixel((x, y), (K if c == 'K' else pal[c]) + (255,))
    return im


def add(group, name, rows, pal, ppu=16):
    SPRITES[(group, name)] = (from_rows(rows, pal) if isinstance(rows, list) else rows, ppu)


# ------------------------------------------------------------------ hearts
HEART_MASK = [
".XX...XX.",
"XXXX.XXXX",
"XXXXXXXXX",
"XXXXXXXXX",
".XXXXXXX.",
"..XXXXX..",
"...XXX...",
"....X....",
]


def heart(kind):
    """kind: full, half, empty, halfcontainer_full, halfcontainer_empty"""
    W, H = 11, 10
    rows = [['.'] * W for _ in range(H)]

    def filled(x, y):
        mx, my = x - 1, y - 1
        return 0 <= my < 8 and 0 <= mx < 9 and HEART_MASK[my][mx] == 'X'

    half_container = kind.startswith("halfcontainer")
    for y in range(H):
        for x in range(W):
            if half_container and x > 5:
                continue
            if filled(x, y):
                if half_container and x == 5:
                    rows[y][x] = 'K'          # cut edge of the half container
                    continue
                red = kind in ("full", "halfcontainer_full") or (kind == "half" and x <= 5)
                if red:
                    c = 'R'
                    if (x, y) in ((2, 2), (3, 2), (2, 3)):
                        c = 'w'               # shine
                    elif y >= 6 or (x >= 7 and y >= 4):
                        c = 'r'               # shade
                else:
                    c = 'e'
                rows[y][x] = c
            elif any(filled(x + dx, y + dy) and not (half_container and x + dx > 5)
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                rows[y][x] = 'K'
    return [''.join(r) for r in rows]


HEART_PAL = {'R': (226, 44, 66), 'r': (150, 22, 44), 'w': (255, 196, 196), 'e': (58, 30, 42)}
for kind in ("full", "half", "empty", "halfcontainer_full", "halfcontainer_empty"):
    add("UI", f"Heart_{kind}", heart(kind), HEART_PAL)

# ------------------------------------------------------------------ item icons (16x16)
ICON_PAL = {
    'W': (240, 240, 236), 'G': (166, 168, 180), 'g': (104, 106, 120), 'Y': (240, 188, 64), 'y': (186, 128, 44),
    'b': (120, 78, 52), 'B': (60, 150, 240), 'c': (150, 220, 255), 'C': (90, 190, 240), 'd': (40, 90, 170),
    'P': (190, 110, 255), 'p': (120, 60, 200), 'O': (255, 150, 40), 'o': (230, 80, 30), 'L': (255, 236, 120),
    'D': (50, 46, 60), 'd2': (0, 0, 0), 'S': (255, 255, 255), 'R': (226, 44, 66),
}
add("Items", "Icon_Dash", [
"................",
"................",
"......KKKK......",
"......KBBK......",
"......KBBK......",
"......KBBK......",
"..KK..KBcK......",
".KcK..KBBKKK....",
"..KK..KBBBBBKK..",
"KKK...KcBBBBBBK.",
"KccK..KBBBBBBBK.",
"KKK...KddddddddK",
"..KK..KKKKKKKKK.",
".KcK............",
"..KK............",
"................",
], ICON_PAL)
add("Items", "Icon_Bomb", [
"..........YL....",
".........Y.L....",
"........b.......",
".......b........",
".....KKbKK......",
"....KDDDDDKK....",
"...KDDSDDDDDK...",
"..KDDSDDDDDDDK..",
"..KDDDDDDDDDDK..",
"..KDDDDDDDDDDK..",
"..KDDDDDDDDDDK..",
"..KDDDDDDDDDDK..",
"...KDDDDDDDDK...",
"....KDDDDDDK....",
".....KKKKKK.....",
"................",
], ICON_PAL)
add("Items", "Icon_Sword", [
"............KKK.",
"...........KWWK.",
"..........KWWGK.",
".........KWWGK..",
"........KWWGK...",
".......KWWGK....",
"......KWWGK.....",
"..KK.KWWGK......",
"..KYKWWGK.......",
"...KYWGK........",
"....KYK.........",
"...KbKYK........",
"..KbK.KYK.......",
".KbK...KK.......",
".KK.............",
"................",
], ICON_PAL)
add("Items", "Icon_MagicBolt", [
"................",
".......S........",
".......S........",
".....KKKKK......",
"....KPPPPPK.....",
"...KPPSSPPPK....",
"SS.KPSSPPPPK.SS.",
"...KPPPPPPpK....",
"...KPPPPPppK....",
"....KpPPppK.....",
".....KKKKK......",
".......S........",
".......S........",
"................",
"................",
"................",
], ICON_PAL)
add("Items", "Icon_Fireball", [
"......K.........",
".....KoK....K...",
".....KOoK..KoK..",
"....KOOoK.KOoK..",
"...KOOOOoKOOoK..",
"...KOOLOOOOOoK..",
"..KOOLLLOOOOOK..",
"..KOLLLLLOOOoK..",
"..KOLLSSLLOOoK..",
"..KOLLSSLLOOoK..",
"..KOOLLLLOOOoK..",
"...KOOLLOOOoK...",
"....KoOOOOoK....",
".....KKKKKK.....",
"................",
"................",
], ICON_PAL)
add("Items", "Icon_IceShards", [
".......K........",
"......KcK.......",
"......KcK.......",
".....KcCdK......",
".KK..KcCdK..KK..",
"KcCK.KcCdK.KcCK.",
".KCdKKcCdKKdCK..",
"..KCdKcCdKdCK...",
"...KCKcCdKCK....",
"....KKcCdKK.....",
".....KcCdK......",
".....KcCdK......",
"......KCK.......",
"......KdK.......",
".......K........",
"................",
], ICON_PAL)
add("Items", "Icon_Lightning", [
"........KKKK....",
".......KLLLK....",
"......KLLLK.....",
".....KLLLK......",
"....KLLLK.......",
"...KLLLKKKKK....",
"..KLLLLLLLLK....",
"..KKKKKKLLK.....",
".......KLLK.....",
"......KLLK......",
".....KLLK.......",
"....KLLK........",
"...KLLK.........",
"...KLK..........",
"...KK...........",
"................",
], ICON_PAL)

# ------------------------------------------------------------------ projectiles & world items (ppu 16)
FX_PAL = {
    'P': (200, 130, 255), 'p': (130, 70, 220), 'S': (255, 255, 255), 'O': (255, 150, 40), 'o': (220, 70, 30),
    'L': (255, 236, 120), 'c': (190, 240, 255), 'C': (110, 200, 245), 'd': (50, 110, 190), 'W': (240, 236, 220),
    'w': (190, 184, 168), 'R': (240, 70, 70), 'r': (150, 30, 40), 'B': (110, 180, 250), 'b': (60, 110, 210),
    'D': (50, 46, 60), 'Y': (240, 188, 64), 'n': (120, 78, 52), 'G': (150, 150, 160), 'g': (100, 100, 112),
    'h': (190, 190, 198), 'q': (70, 70, 82),
}
add("Effects", "MagicBolt", [
"..KKK..",
".KPPPK.",
"KPSSPpK",
"KPSPPpK",
"KPPPppK",
".KpppK.",
"..KKK..",
], FX_PAL)
add("Effects", "Fireball", [
"...KKK...",
"..KOOOK..",
".KOLLLOK.",
"KOLSSLLOK",
"KOLSSLLoK",
"KOLLLLOoK",
".KoOOOoK.",
"..KoooK..",
"...KKK...",
], FX_PAL)
add("Effects", "IceShard", [
"...KKK...",
".KKccCKK.",
"KcccCCddK",
".KKCCdKK.",
"...KKK...",
], FX_PAL)
add("Effects", "Bone", [
"KK.....KK",
"KWKKKKKWK",
"KwWWWWWwK",
"KK.....KK",
], FX_PAL)
add("Effects", "EnemyOrb", [
".KKKK.",
"KRSRrK",
"KRRRrK",
"KRRrrK",
".KKKK.",
], FX_PAL)
add("Effects", "SlimeBall", [
".KKKK.",
"KBSBbK",
"KBBBbK",
"KbBbbK",
".KKKK.",
], FX_PAL)
add("Effects", "Bomb", [
"......YL.",
".....n...",
"....n....",
"..KKnKK..",
".KDDDDDK.",
"KDDSDDDDK",
"KDSDDDDDK",
"KDDDDDDDK",
"KDDDDDDDK",
".KDDDDDK.",
"..KKKKK..",
], FX_PAL)
# The pedestal is drawn by Visuals/room_generator/room_art.py


def ring(size, thickness):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r_out = size / 2
    for y in range(size):
        for x in range(size):
            d = ((x + 0.5 - r_out) ** 2 + (y + 0.5 - r_out) ** 2) ** 0.5
            if r_out - thickness <= d <= r_out:
                im.putpixel((x, y), (255, 255, 255, 255))
    return im


def disc(size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r = size / 2
    for y in range(size):
        for x in range(size):
            if ((x + 0.5 - r) ** 2 + (y + 0.5 - r) ** 2) ** 0.5 <= r:
                im.putpixel((x, y), (255, 255, 255, 255))
    return im


add("Effects", "Ring", ring(32, 2), None, ppu=16)      # 2 units across; tint + scale in code
add("Effects", "Disc", disc(16), None, ppu=16)         # 1 unit across; shadows / flashes
add("Effects", "Pixel", Image.new("RGBA", (2, 2), (255, 255, 255, 255)), None, ppu=16)
add("UI", "White", Image.new("RGBA", (4, 4), (255, 255, 255, 255)), None, ppu=16)


# ------------------------------------------------------------------ writing
def meta(guid, ppu):
    plat = "".join(f"""  - serializedVersion: 4
    buildTarget: {t}
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 0
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
""" for t in ["DefaultTexturePlatform", "Standalone", "WebGL"])
    return f"""fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 0
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: {ppu}
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 0
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings:
{plat}  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    customData:
    physicsShape: []
    bones: []
    spriteID: {hashlib.md5((guid + "_sprite").encode()).hexdigest()}
    internalID: 0
    vertices: []
    indices:
    edges: []
    weights: []
    secondaryTextures: []
    spriteCustomMetadata:
      entries: []
    nameFileIdTable: {{}}
  mipmapLimitGroupName:
  pSDRemoveMatte: 0
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def folder_meta(path):
    if os.path.exists(path + ".meta"):
        return
    g = hashlib.md5(("hfp_folder_" + os.path.relpath(path, ROOT)).encode()).hexdigest()
    with open(path + ".meta", "w", newline="\n") as f:
        f.write(f"fileFormatVersion: 2\nguid: {g}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n"
                "  userData: \n  assetBundleName: \n  assetBundleVariant: \n")


if __name__ == "__main__":
    resources = os.path.dirname(ROOT)
    for d in (resources, ROOT):
        os.makedirs(d, exist_ok=True)
        folder_meta(d)
    preview_items = []
    for (group, name), (im, ppu) in SPRITES.items():
        folder = os.path.join(ROOT, group)
        os.makedirs(folder, exist_ok=True)
        folder_meta(folder)
        path = os.path.join(folder, name + ".png")
        im.save(path)
        with open(path + ".meta", "w", newline="\n") as f:
            f.write(meta(hashlib.md5(f"hfp_fx_{group}_{name}".encode()).hexdigest(), ppu))
        preview_items.append(im)
    # contact sheet preview
    cell = 34
    cols = 8
    rows = (len(preview_items) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (40, 40, 48, 255))
    for i, im in enumerate(preview_items):
        x, y = (i % cols) * cell + (cell - im.width) // 2, (i // cols) * cell + (cell - im.height) // 2
        sheet.alpha_composite(im, (max(0, x), max(0, y)))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(os.path.dirname(__file__), "fx_preview.png"))
    print(f"wrote {len(SPRITES)} sprites to {ROOT}")
