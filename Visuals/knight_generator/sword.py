"""Knight's sword: 32x10 pixel art pointing right, pivot on the grip. Writes the PNG + .meta into Unity."""
import hashlib, os
from PIL import Image

PAL = {'K': (24, 18, 26), 'W': (236, 234, 226), 'H': (200, 202, 212), 'G': (150, 152, 166), 'g': (104, 106, 120),
       'Y': (240, 188, 64), 'y': (186, 128, 44), 'b': (120, 78, 52)}
SWORD = [
"....KKK.........................",
"...KYyYK........................",
"...KYyYKKKKKKKKKKKKKKKKKKKKKK...",
"KK.KYyYKWWWWWWWWWWWWWWWWWWWWWKK.",
"KbKKYyYKHHHHHHHHHHHHHHHHHHHHHHHK",
"KbbbYyYKGGGGGGGGGGGGGGGGGGGGGKK.",
"KbKKYyYKKKKKKKKKKKKKKKKKKKKKK...",
"KK.KYyYK........................",
"...KYyYK........................",
"....KKK.........................",
]
PIVOT = (2.5 / 32, 4.5 / 10)   # middle of the grip (Unity pivots count from the bottom)

im = Image.new("RGBA", (32, 10), (0, 0, 0, 0))
for y, row in enumerate(SWORD):
    for x, c in enumerate(row):
        if c != '.':
            im.putpixel((x, y), PAL[c] + (255,))

out = os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Animations", "Knight", "Sprites", "Knight_Sword.png")
im.save(out)
im.resize((32 * 10, 10 * 10), Image.NEAREST).save(os.path.join(os.path.dirname(__file__), "sword_preview.png"))
guid = hashlib.md5(b"hfp_knight_sword").hexdigest()
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
meta = f"""fileFormatVersion: 2
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
  alignment: 9
  spritePivot: {{x: {PIVOT[0]:.6f}, y: {PIVOT[1]:.6f}}}
  spritePixelsToUnits: 32
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
    spriteID: {hashlib.md5(b"knight_sword_sprite").hexdigest()}
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
with open(out + ".meta", "w", newline="\n") as f:
    f.write(meta)
print(guid)
