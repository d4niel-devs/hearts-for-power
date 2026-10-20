import pickle, os, shutil, uuid, hashlib
from PIL import Image
ORDER, frames = pickle.load(open("frames.pkl","rb"))
PROJ = r"C:/Users/danie/Coding/Hearts_for_Power"
OUT = os.path.join(PROJ, "Assets/Animations/Knight/Sprites"); os.makedirs(OUT, exist_ok=True)
shutil.copy("knight_sheet.png", os.path.join(OUT, "Knight_Sheet.png"))
TEX_GUID = hashlib.md5(b"hearts_for_power_knight_sheet").hexdigest()

def iid(name):  # stable positive int64 internal id
    return int(hashlib.md5(name.encode()).hexdigest()[:15], 16)

H = 32*len(ORDER)
sprites=[]; table=[]
for r,anim in enumerate(ORDER):
    for c in range(4):
        n=f"knight_{anim}_{c}"
        sprites.append(f"""    - serializedVersion: 2
      name: {n}
      rect:
        serializedVersion: 2
        x: {c*32}
        y: {H-32*(r+1)}
        width: 32
        height: 32
      alignment: 0
      pivot: {{x: 0.5, y: 0.5}}
      border: {{x: 0, y: 0, z: 0, w: 0}}
      customData: 
      outline: []
      physicsShape: []
      tessellationDetail: -1
      bones: []
      spriteID: {hashlib.md5(n.encode()).hexdigest()}
      internalID: {iid(n)}
      vertices: []
      indices: 
      edges: []
      weights: []
""")
        table.append(f"""  - first:
      213: {iid(n)}
    second: {n}
""")
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
""" for t in ["DefaultTexturePlatform","Standalone","WebGL"])
meta = f"""fileFormatVersion: 2
guid: {TEX_GUID}
TextureImporter:
  internalIDToNameTable:
{''.join(table)}  externalObjects: {{}}
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
  spriteMode: 2
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
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
    sprites:
{''.join(sprites)}    outline: []
    customData: 
    physicsShape: []
    bones: []
    spriteID: 
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: []
    spriteCustomMetadata:
      entries: []
    nameFileIdTable:
{''.join(f"      knight_{a}_{c}: {iid(f'knight_{a}_{c}')}" + chr(10) for a in ORDER for c in range(4))}  mipmapLimitGroupName: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
open(os.path.join(OUT,"Knight_Sheet.png.meta"),"w",newline="\n").write(meta)

# ---- rewrite clip contents (their .meta files/GUIDs are left alone so Knight.controller keeps working) ----
CLIPS = {  # clip name -> (anim row, fps)
 "Knight_Walk_Down":("walk_S",8), "Knight_Walk_Up":("walk_N",8), "Knight_Walk_Right":("walk_E",8), "Knight_Walk_Left":("walk_W",8),
 "Knight_Idle_Down":("idle_S",3), "Knight_Idle_Up":("idle_N",3), "Knight_Idle_Right":("idle_E",3), "Knight_Idle_Left":("idle_W",3),
}
for clip,(anim,fps) in CLIPS.items():
    refs=[f"{{fileID: {iid(f'knight_{anim}_{c}')}, guid: {TEX_GUID}, type: 3}}" for c in range(4)]
    keys="".join(f"    - time: {c/fps:.6g}\n      value: {refs[c]}\n" for c in range(4))
    yaml=f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {clip}
  serializedVersion: 7
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves: []
  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves: []
  m_ScaleCurves: []
  m_FloatCurves: []
  m_PPtrCurves:
  - serializedVersion: 2
    curve:
{keys}    attribute: m_Sprite
    path: 
    classID: 212
    script: {{fileID: 0}}
    flags: 2
  m_SampleRate: {fps}
  m_WrapMode: 0
  m_Bounds:
    m_Center: {{x: 0, y: 0, z: 0}}
    m_Extent: {{x: 0, y: 0, z: 0}}
  m_ClipBindingConstant:
    genericBindings:
    - serializedVersion: 2
      path: 0
      attribute: 0
      script: {{fileID: 0}}
      typeID: 212
      customType: 23
      isPPtrCurve: 1
      isIntCurve: 0
      isSerializeReferenceCurve: 0
    pptrCurveMapping:
{''.join(f"    - {r}" + chr(10) for r in refs)}  m_AnimationClipSettings:
    serializedVersion: 2
    m_AdditiveReferencePoseClip: {{fileID: 0}}
    m_AdditiveReferencePoseTime: 0
    m_StartTime: 0
    m_StopTime: {4/fps:.6g}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: 1
    m_LoopBlend: 0
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 0
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 0
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves: []
  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events: []
"""
    open(os.path.join(PROJ,"Assets/Animations/Knight/Clips",clip+".anim"),"w",newline="\n").write(yaml)
print(TEX_GUID, iid("knight_idle_S_0"))
