"""Exports the monsters from monsters.py into Unity:
Assets/Animations/Monsters/
    Monster.controller                      shared state machine: Idle/Walk blend trees on MoveX/MoveY,
                                            switched by IsMoving. Left and right both use the Side clip
                                            (MonsterAnimator.cs flips the sprite).
    <Name>/<Name>_Sheet.png (+ sliced .meta)
    <Name>/<Name>_Idle_Down/Up/Side.anim, <Name>_Walk_Down/Up/Side.anim
    <Name>/<Name>.overrideController         plug into an Animator to get that monster
GUIDs are derived from names, so re-running keeps every reference intact."""
import hashlib
import os
import shutil
from PIL import Image
from monsters import MONSTERS, ORDER, VIEWS, to_img

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(PROJ, "Assets", "Animations", "Monsters")
FPS = {"Idle": 3, "Walk": 8}
FPS_OVERRIDE = {("Slime", "Walk"): 12,    # 6-frame hop = 0.5 s, matching EnemyChase.Hop
                ("Mimic", "Walk"): 12,    # hops the same way
                ("Bat", "Idle"): 10, ("Bat", "Walk"): 12,   # always flapping
                ("Ghost", "Idle"): 4, ("Ghost", "Walk"): 6,
                ("Spirit", "Idle"): 10, ("Spirit", "Walk"): 10}   # flickering soul-fire
CLIPS = [f"{a}_{v}" for a in ("Idle", "Walk") for v in VIEWS]


def guid(key):
    return hashlib.md5(("hfp_" + key).encode()).hexdigest()


def iid(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:15], 16)


def write(path, text):
    with open(path, "w", newline="\n") as f:
        f.write(text)


def folder_meta(path):
    if not os.path.exists(path + ".meta"):
        write(path + ".meta", f"fileFormatVersion: 2\nguid: {guid('folder_' + os.path.relpath(path, PROJ))}\n"
                              "folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n"
                              "  assetBundleName: \n  assetBundleVariant: \n")


def native_meta(path, key, main_id):
    write(path + ".meta", f"fileFormatVersion: 2\nguid: {guid(key)}\nNativeFormatImporter:\n  externalObjects: {{}}\n"
                          f"  mainObjectFileID: {main_id}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")


def sheet_meta(path, key, sprite_names, size=32):
    """sprite_names: list of (name, x, y) with y measured from the bottom of the texture."""
    table = "".join(f"  - first:\n      213: {iid(n)}\n    second: {n}\n" for n, _, _ in sprite_names)
    sprites = "".join(f"""    - serializedVersion: 2
      name: {n}
      rect:
        serializedVersion: 2
        x: {x}
        y: {y}
        width: {size}
        height: {size}
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
""" for n, x, y in sprite_names)
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
    names = "".join(f"      {n}: {iid(n)}\n" for n, _, _ in sprite_names)
    write(path + ".meta", f"""fileFormatVersion: 2
guid: {guid(key)}
TextureImporter:
  internalIDToNameTable:
{table}  externalObjects: {{}}
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
{sprites}    outline: []
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
{names}  mipmapLimitGroupName:
  pSDRemoveMatte: 0
  userData:
  assetBundleName:
  assetBundleVariant:
""")


def clip_yaml(name, tex_guid, sprite_names, fps, loop=True):
    refs = [f"{{fileID: {iid(n)}, guid: {tex_guid}, type: 3}}" for n in sprite_names]
    keys = "".join(f"    - time: {i / fps:.6g}\n      value: {r}\n" for i, r in enumerate(refs))
    mapping = "".join(f"    - {r}\n" for r in refs)
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
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
{mapping}  m_AnimationClipSettings:
    serializedVersion: 2
    m_AdditiveReferencePoseClip: {{fileID: 0}}
    m_AdditiveReferencePoseTime: 0
    m_StartTime: 0
    m_StopTime: {len(refs) / fps:.6g}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: {1 if loop else 0}
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


def clip_ref(monster, anim):
    return f"{{fileID: 7400000, guid: {guid(f'clip_{monster}_{anim}')}, type: 2}}"


def base_controller(default_monster):
    def state(fid, name, motion, trans):
        return f"""--- !u!1102 &{fid}
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions:
  - {{fileID: {trans}}}
  m_StateMachineBehaviours: []
  m_Position: {{x: 0, y: 0, z: 0}}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {{fileID: {motion}}}
  m_Tag:
  m_SpeedParameter:
  m_MirrorParameter:
  m_CycleOffsetParameter:
  m_TimeParameter:
"""

    def transition(fid, mode, dst):
        return f"""--- !u!1101 &{fid}
AnimatorStateTransition:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name:
  m_Conditions:
  - m_ConditionMode: {mode}
    m_ConditionEvent: IsMoving
    m_EventTreshold: 0
  m_DstStateMachine: {{fileID: 0}}
  m_DstState: {{fileID: {dst}}}
  m_Solo: 0
  m_Mute: 0
  m_IsExit: 0
  serializedVersion: 3
  m_TransitionDuration: 0
  m_TransitionOffset: 0
  m_ExitTime: 0
  m_HasExitTime: 0
  m_HasFixedDuration: 1
  m_InterruptionSource: 0
  m_OrderedInterruption: 1
  m_CanTransitionToSelf: 0
"""
    def tree(fid, anim):
        # Down/Up get their own clip; right and left both use Side (MonsterAnimator flips the sprite)
        kids = ""
        for view, (x, y) in (("Down", (0, -1)), ("Up", (0, 1)), ("Side", (1, 0)), ("Side", (-1, 0))):
            kids += f"""  - serializedVersion: 2
    m_Motion: {clip_ref(default_monster, f"{anim}_{view}")}
    m_Threshold: 0
    m_Position: {{x: {x}, y: {y}}}
    m_TimeScale: 1
    m_CycleOffset: 0
    m_DirectBlendParameter: MoveX
    m_Mirror: 0
"""
        return f"""--- !u!206 &{fid}
BlendTree:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {anim}
  m_Childs:
{kids}  m_BlendParameter: MoveX
  m_BlendParameterY: MoveY
  m_MinThreshold: 0
  m_MaxThreshold: 3
  m_UseAutomaticThresholds: 1
  m_NormalizedBlendValues: 0
  m_BlendType: 1
"""

    def param(n, t):
        return f"""  - m_Name: {n}
    m_Type: {t}
    m_DefaultFloat: 0
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}
"""
    IDLE, WALK, TO_WALK, TO_IDLE, SM = 1102000001, 1102000002, 1101000001, 1101000002, 1107000001
    IDLE_T, WALK_T = 206000001, 206000002
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Monster
  serializedVersion: 5
  m_AnimatorParameters:
{param("MoveX", 1)}{param("MoveY", 1)}{param("IsMoving", 4)}  m_AnimatorLayers:
  - serializedVersion: 5
    m_Name: Base Layer
    m_StateMachine: {{fileID: {SM}}}
    m_Mask: {{fileID: 0}}
    m_Motions: []
    m_Behaviours: []
    m_BlendingMode: 0
    m_SyncedLayerIndex: -1
    m_DefaultWeight: 0
    m_IKPass: 0
    m_SyncedLayerAffectsTiming: 0
    m_Controller: {{fileID: 9100000}}
--- !u!1107 &{SM}
AnimatorStateMachine:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Base Layer
  m_ChildStates:
  - serializedVersion: 1
    m_State: {{fileID: {IDLE}}}
    m_Position: {{x: 300, y: 100, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: {WALK}}}
    m_Position: {{x: 300, y: 220, z: 0}}
  m_ChildStateMachines: []
  m_AnyStateTransitions: []
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 50, y: 20, z: 0}}
  m_EntryPosition: {{x: 50, y: 110, z: 0}}
  m_ExitPosition: {{x: 600, y: 110, z: 0}}
  m_ParentStateMachinePosition: {{x: 800, y: 20, z: 0}}
  m_DefaultState: {{fileID: {IDLE}}}
{state(IDLE, "Idle", IDLE_T, TO_WALK)}{state(WALK, "Walk", WALK_T, TO_IDLE)}{tree(IDLE_T, "Idle")}{tree(WALK_T, "Walk")}{transition(TO_WALK, 1, WALK)}{transition(TO_IDLE, 2, IDLE)}"""


def override_controller(name, default_monster):
    clips = "".join(f"""  - m_OriginalClip: {clip_ref(default_monster, a)}
    m_OverrideClip: {clip_ref(name, a)}
""" for a in CLIPS)
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!221 &22100000
AnimatorOverrideController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Controller: {{fileID: 9100000, guid: {guid('monster_controller')}, type: 2}}
  m_Clips:
{clips}"""


def remove_asset(path):
    for p in (path, path + ".meta"):
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)


def main():
    os.makedirs(ROOT, exist_ok=True)
    folder_meta(ROOT)
    default = ORDER[0]
    # drop monster folders that are no longer in the roster
    for entry in os.listdir(ROOT):
        if os.path.isdir(os.path.join(ROOT, entry)) and entry not in ORDER:
            remove_asset(os.path.join(ROOT, entry))

    for name in ORDER:
        pal, fn = MONSTERS[name]
        views = fn()
        folder = os.path.join(ROOT, name)
        os.makedirs(folder, exist_ok=True)
        folder_meta(folder)

        # sheet rows, top to bottom: Idle_Down, Idle_Up, Idle_Side, Walk_Down, Walk_Up, Walk_Side
        # (texture y counts from the bottom)
        frame_lists = {clip: views[clip.split("_")[1]][0 if clip.startswith("Idle") else 1] for clip in CLIPS}
        sheet = Image.new("RGBA", (32 * max(len(f) for f in frame_lists.values()), 32 * len(CLIPS)), (0, 0, 0, 0))
        sprite_rows = {}
        for row, clip in enumerate(CLIPS):
            frames = frame_lists[clip]
            sprite_rows[clip] = []
            for c, g in enumerate(frames):
                sheet.paste(to_img(g, pal), (c * 32, row * 32))
                sprite_rows[clip].append((f"{name}_{clip}_{c}", c * 32, sheet.height - 32 * (row + 1)))
        sheet_path = os.path.join(folder, f"{name}_Sheet.png")
        sheet.save(sheet_path)
        sheet_meta(sheet_path, f"sheet_{name}", [s for clip in CLIPS for s in sprite_rows[clip]])

        for old in ("Idle", "Walk"):   # clips from the earlier side-only export
            remove_asset(os.path.join(folder, f"{name}_{old}.anim"))
        for clip in CLIPS:
            anim = clip.split("_")[0]
            p = os.path.join(folder, f"{name}_{clip}.anim")
            fps = FPS_OVERRIDE.get((name, anim), FPS[anim])
            write(p, clip_yaml(f"{name}_{clip}", guid(f"sheet_{name}"), [n for n, _, _ in sprite_rows[clip]], fps))
            native_meta(p, f"clip_{name}_{clip}", 7400000)

        p = os.path.join(folder, f"{name}.overrideController")
        write(p, override_controller(name, default))
        native_meta(p, f"override_{name}", 22100000)

    p = os.path.join(ROOT, "Monster.controller")
    write(p, base_controller(default))
    native_meta(p, "monster_controller", 9100000)
    print("Exported", ", ".join(ORDER), "to", ROOT)


if __name__ == "__main__":
    main()
