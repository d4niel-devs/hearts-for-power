"""Boss sprites (64x64, same pixel size as everything else) drawn from shaded shapes plus an
automatic dark outline, and exported to Unity with their animations:
    Assets/Animations/Bosses/Boss.controller           Idle / Walk / Attack (windup) / Slam / Charge states
    Assets/Animations/Bosses/<Boss>/<Boss>_Sheet.png    sprite sheet (+ sliced .meta)
    Assets/Animations/Bosses/<Boss>/*.anim              one clip per animation and view (Down/Up/Side)
    Assets/Animations/Bosses/<Boss>/<Boss>.overrideController
Bosses: King Slime (crowned giant slime) and Orc Warlord (armoured orc with a huge axe).
Run: python bosses.py"""
import math
import os
from PIL import Image
import unity_export as ux

SIZE = 64
K = (24, 18, 26)
VIEWS = ("Down", "Up", "Side")
ANIMS = ("Idle", "Walk", "Attack", "Slam", "Charge")   # Charge: Orc Warlord only, others reuse Walk
ROOT = os.path.join(ux.PROJ, "Assets", "Animations", "Bosses")


# ---------------------------------------------------------------- drawing helpers
class Canvas:
    def __init__(self):
        self.im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.im.putpixel((x, y), tuple(c[:3]) + ((c[3],) if len(c) == 4 else (255,)))

    def get(self, x, y):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            return self.im.getpixel((x, y))
        return (0, 0, 0, 0)

    def blob(self, cx, cy, rx, ry_top, ry_bottom, colors, light=(-0.6, -0.8)):
        """Filled ellipse (different top/bottom heights) shaded light->dark from the light direction."""
        lx, ly = light
        for y in range(SIZE):
            for x in range(SIZE):
                ry = ry_top if y < cy else ry_bottom
                if ry <= 0 or rx <= 0:
                    continue
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if nx * nx + ny * ny > 1:
                    continue
                t = nx * lx + ny * ly          # > 0 = facing the light
                self.px(x, y, colors[0] if t > 0.45 else colors[1] if t > -0.15 else colors[2] if t > -0.6 else colors[3])

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def poly(self, points, c):
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if point_in_poly(x + 0.5, y + 0.5, points):
                    self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c, width=1):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(width):
                for dy in range(width):
                    self.px(x + dx - width // 2, y + dy - width // 2, c)

    def shadow(self, cx, cy, rx, ry=3):
        for y in range(SIZE):
            for x in range(SIZE):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1 and self.get(x, y)[3] == 0:
                    self.px(x, y, (20, 16, 24, 110))

    def outlined(self):
        out = self.im.copy()
        for y in range(SIZE):
            for x in range(SIZE):
                if self.get(x, y)[3] == 255:
                    continue
                if any(self.get(x + dx, y + dy)[3] == 255 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out.putpixel((x, y), K + (255,))
        return out


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


# ---------------------------------------------------------------- King Slime
SLIME = [(206, 236, 255), (110, 178, 250), (66, 124, 220), (40, 80, 168)]
GOLD = [(255, 230, 120), (240, 188, 64), (186, 128, 44)]


def king_slime(view, squash=1.0, lift=0, shadow_scale=1.0, tremble=0):
    """squash > 1 = wider and flatter, < 1 = taller and thinner. lift raises the body off the ground."""
    c = Canvas()
    ground = 61
    rx = 25 * squash
    ry_top, ry_bottom = 19 / squash, 12 / squash
    cx = 32 + tremble
    cy = ground - ry_bottom - lift
    c.shadow(32, ground, 22 * shadow_scale, 3)
    c.blob(cx, cy, rx, ry_top, ry_bottom, SLIME)
    top = cy - ry_top

    # glossy shine
    for dy in range(3):
        for dx in range(5 - dy):
            c.px(cx - rx * 0.45 + dx, top + 5 + dy, (235, 248, 255))
    face_y = cy - 3
    if view == "Down":
        for side, ex in ((-1, cx - 9 * squash), (1, cx + 9 * squash)):
            c.rect(ex - 4, face_y - 4, ex + 3, face_y + 3, (255, 255, 255))
            c.rect(ex - 1, face_y - 1, ex + 2, face_y + 3, K)
            for i in range(7):                                             # angry brows
                c.px(ex - 4 + i, face_y - 6 + (i // 2 if side < 0 else 3 - i // 2), K)
                c.px(ex - 4 + i, face_y - 5 + (i // 2 if side < 0 else 3 - i // 2), K)
        c.rect(cx - 4, face_y + 6, cx + 3, face_y + 7, (24, 40, 80))      # wide grin
        c.px(cx - 5, face_y + 5, (24, 40, 80))
        c.px(cx + 4, face_y + 5, (24, 40, 80))
    elif view == "Side":
        ex = cx + rx * 0.55
        c.rect(ex - 4, face_y - 4, ex + 3, face_y + 3, (255, 255, 255))
        c.rect(ex, face_y - 1, ex + 3, face_y + 3, K)
        for i in range(7):
            c.px(ex - 4 + i, face_y - 6 + i // 2, K)
            c.px(ex - 4 + i, face_y - 5 + i // 2, K)
        c.rect(ex - 2, face_y + 6, ex + 4, face_y + 7, (24, 40, 80))

    # crown
    crown_cx = cx + (6 if view == "Side" else 1)       # the crown art is 1px left-heavy, so nudge it to sit centred
    base_y = top + 1
    c.rect(crown_cx - 11, base_y - 3, crown_cx + 8, base_y, GOLD[1])
    c.rect(crown_cx - 11, base_y - 3, crown_cx + 8, base_y - 3, GOLD[0])
    for px_ in (-10, -3, 4):                    # a spike at each end and one in the middle, mirrored
        c.poly([(crown_cx + px_ - 1, base_y - 3), (crown_cx + px_ + 2.5, base_y - 11), (crown_cx + px_ + 5, base_y - 3)], GOLD[1])
        c.px(crown_cx + px_ + 2, base_y - 9, GOLD[0])
    if view != "Up":
        c.rect(crown_cx - 2, base_y - 2, crown_cx, base_y - 1, (226, 44, 66))     # ruby
        c.px(crown_cx - 7, base_y - 2, (90, 190, 240))
        c.px(crown_cx + 6, base_y - 2, (90, 190, 240))
    return c.outlined()


def king_slime_frames(view):
    idle = [king_slime(view), king_slime(view), king_slime(view, squash=1.05), king_slime(view, squash=1.05)]
    walk = [king_slime(view, squash=1.25, shadow_scale=1.1),                     # crouch
            king_slime(view, squash=0.82, shadow_scale=0.9),                     # launch
            king_slime(view, squash=0.92, lift=8, shadow_scale=0.7),             # rising
            king_slime(view, squash=1.0, lift=12, shadow_scale=0.6),             # apex
            king_slime(view, squash=0.88, lift=5, shadow_scale=0.75),            # falling
            king_slime(view, squash=1.3, shadow_scale=1.15)]                     # splat
    attack = [king_slime(view, squash=1.18, tremble=-1), king_slime(view, squash=1.2, tremble=1)]
    slam = [king_slime(view, squash=1.35, shadow_scale=1.2), king_slime(view, squash=1.12)]
    return {"Idle": idle, "Walk": walk, "Attack": attack, "Slam": slam}


# ---------------------------------------------------------------- Orc Warlord
# Drawn in orc_warlord.py (layered, detailed body and a hand-drawn battle axe)
import orc_warlord


def orc_frames(view):
    return orc_warlord.frames(view)


# The Ancient Lich (floor 2 boss): drawn in ancient_lich.py
import ancient_lich

# name -> (frame maker, fps per animation, animations that play once instead of looping)
BOSSES = {
    "KingSlime": (king_slime_frames, {"Idle": 4, "Walk": 11, "Attack": 10, "Slam": 8}, {"Slam"}),
    "AncientLich": (ancient_lich.frames, {"Idle": 4, "Walk": 7, "Attack": 7, "Slam": 10}, {"Attack", "Slam"}),
    "OrcWarlord": (orc_frames, {"Idle": 4, "Walk": 9, "Attack": 8, "Slam": 14, "Charge": 12}, {"Attack", "Slam"}),
}
CLIPS = [f"{a}_{v}" for a in ANIMS for v in VIEWS]


# ---------------------------------------------------------------- Unity export
def clip_ref(boss, clip):
    return f"{{fileID: 7400000, guid: {ux.guid(f'bossclip_{boss}_{clip}')}, type: 2}}"


def controller(default):
    def tree(fid, anim):
        kids = ""
        for view, (x, y) in (("Down", (0, -1)), ("Up", (0, 1)), ("Side", (1, 0)), ("Side", (-1, 0))):
            kids += f"""  - serializedVersion: 2
    m_Motion: {clip_ref(default, f"{anim}_{view}")}
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

    def state(fid, name, motion, transitions, pos):
        trans = "".join(f"  - {{fileID: {t}}}\n" for t in transitions)
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
  m_Transitions:{(chr(10) + trans) if trans else ' []' + chr(10)}  m_StateMachineBehaviours: []
  m_Position: {pos}
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

    def transition(fid, conditions, dst, exit_time=None):
        conds = "".join(f"""  - m_ConditionMode: {mode}
    m_ConditionEvent: {param}
    m_EventTreshold: 0
""" for mode, param in conditions)
        return f"""--- !u!1101 &{fid}
AnimatorStateTransition:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name:
  m_Conditions:{(chr(10) + conds) if conds else ' []' + chr(10)}  m_DstStateMachine: {{fileID: 0}}
  m_DstState: {{fileID: {dst}}}
  m_Solo: 0
  m_Mute: 0
  m_IsExit: 0
  serializedVersion: 3
  m_TransitionDuration: 0
  m_TransitionOffset: 0
  m_ExitTime: {exit_time if exit_time is not None else 0}
  m_HasExitTime: {1 if exit_time is not None else 0}
  m_HasFixedDuration: 1
  m_InterruptionSource: 0
  m_OrderedInterruption: 1
  m_CanTransitionToSelf: 0
"""

    def param(n, t):
        return f"""  - m_Name: {n}
    m_Type: {t}
    m_DefaultFloat: 0
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}
"""
    IDLE, WALK, ATTACK, SLAM, CHARGE = 1102000001, 1102000002, 1102000003, 1102000004, 1102000005
    T_IDLE, T_WALK, T_ATTACK, T_SLAM, T_CHARGE = 206000001, 206000002, 206000003, 206000004, 206000005
    I2W, W2I, A2I, S2I, ANY2A, ANY2S = 1101000001, 1101000002, 1101000003, 1101000004, 1101000005, 1101000006
    C2I, ANY2C = 1101000007, 1101000008
    SM = 1107000001
    IF, IFNOT = 1, 2
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Boss
  serializedVersion: 5
  m_AnimatorParameters:
{param("MoveX", 1)}{param("MoveY", 1)}{param("IsMoving", 4)}{param("Attacking", 4)}{param("Slam", 9)}{param("Charging", 4)}  m_AnimatorLayers:
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
  - serializedVersion: 1
    m_State: {{fileID: {ATTACK}}}
    m_Position: {{x: 560, y: 100, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: {SLAM}}}
    m_Position: {{x: 560, y: 220, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: {CHARGE}}}
    m_Position: {{x: 560, y: 340, z: 0}}
  m_ChildStateMachines: []
  m_AnyStateTransitions:
  - {{fileID: {ANY2S}}}
  - {{fileID: {ANY2C}}}
  - {{fileID: {ANY2A}}}
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 50, y: 20, z: 0}}
  m_EntryPosition: {{x: 50, y: 110, z: 0}}
  m_ExitPosition: {{x: 800, y: 110, z: 0}}
  m_ParentStateMachinePosition: {{x: 800, y: 20, z: 0}}
  m_DefaultState: {{fileID: {IDLE}}}
{state(IDLE, "Idle", T_IDLE, [I2W], "{x: 0, y: 0, z: 0}")}{state(WALK, "Walk", T_WALK, [W2I], "{x: 0, y: 0, z: 0}")}{state(ATTACK, "Attack", T_ATTACK, [A2I], "{x: 0, y: 0, z: 0}")}{state(SLAM, "Slam", T_SLAM, [S2I], "{x: 0, y: 0, z: 0}")}{state(CHARGE, "Charge", T_CHARGE, [C2I], "{x: 0, y: 0, z: 0}")}{tree(T_IDLE, "Idle")}{tree(T_WALK, "Walk")}{tree(T_ATTACK, "Attack")}{tree(T_SLAM, "Slam")}{tree(T_CHARGE, "Charge")}{transition(I2W, [(IF, "IsMoving")], WALK)}{transition(W2I, [(IFNOT, "IsMoving")], IDLE)}{transition(A2I, [(IFNOT, "Attacking")], IDLE)}{transition(S2I, [], IDLE, exit_time=1)}{transition(ANY2A, [(IF, "Attacking")], ATTACK)}{transition(ANY2S, [(IF, "Slam")], SLAM)}{transition(ANY2C, [(IF, "Charging")], CHARGE)}{transition(C2I, [(IFNOT, "Charging")], IDLE)}"""


def override(name, default):
    clips = "".join(f"""  - m_OriginalClip: {clip_ref(default, c)}
    m_OverrideClip: {clip_ref(name, c)}
""" for c in CLIPS)
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!221 &22100000
AnimatorOverrideController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Controller: {{fileID: 9100000, guid: {ux.guid('boss_controller')}, type: 2}}
  m_Clips:
{clips}"""


def main():
    os.makedirs(ROOT, exist_ok=True)
    ux.folder_meta(ROOT)
    default = "KingSlime"
    preview_rows = []
    for name, (make, fps, once) in BOSSES.items():
        folder = os.path.join(ROOT, name)
        os.makedirs(folder, exist_ok=True)
        ux.folder_meta(folder)
        views = {v: make(v) for v in VIEWS}
        frame_lists = {f"{a}_{v}": views[v].get(a, views[v]["Walk"]) for a in ANIMS for v in VIEWS}
        cols = max(len(f) for f in frame_lists.values())
        sheet = Image.new("RGBA", (SIZE * cols, SIZE * len(CLIPS)), (0, 0, 0, 0))
        sprites = {}
        for row, clip in enumerate(CLIPS):
            sprites[clip] = []
            for col, im in enumerate(frame_lists[clip]):
                sheet.paste(im, (col * SIZE, row * SIZE))
                sprites[clip].append((f"{name}_{clip}_{col}", col * SIZE, sheet.height - SIZE * (row + 1)))
            preview_rows.append(frame_lists[clip])
        sheet_path = os.path.join(folder, f"{name}_Sheet.png")
        sheet.save(sheet_path)
        ux.sheet_meta(sheet_path, f"bosssheet_{name}", [s for c in CLIPS for s in sprites[c]], size=SIZE)
        for clip in CLIPS:
            anim = clip.split("_")[0]
            path = os.path.join(folder, f"{name}_{clip}.anim")
            ux.write(path, ux.clip_yaml(f"{name}_{clip}", ux.guid(f"bosssheet_{name}"),
                                        [n for n, _, _ in sprites[clip]], fps.get(anim, fps["Walk"]), loop=anim not in once))
            ux.native_meta(path, f"bossclip_{name}_{clip}", 7400000)
        path = os.path.join(folder, f"{name}.overrideController")
        ux.write(path, override(name, default))
        ux.native_meta(path, f"bossoverride_{name}", 22100000)

    path = os.path.join(ROOT, "Boss.controller")
    ux.write(path, controller(default))
    ux.native_meta(path, "boss_controller", 9100000)

    # preview: every animation row, frames side by side
    preview = Image.new("RGBA", (6 * 66, len(preview_rows) * 66), (70, 68, 78, 255))
    for r, frames in enumerate(preview_rows):
        for c, im in enumerate(frames):
            preview.alpha_composite(im, (c * 66, r * 66))
    preview.resize((preview.width * 2, preview.height * 2), Image.NEAREST).save(
        os.path.join(os.path.dirname(__file__), "bosses_preview.png"))
    print("Exported bosses to", ROOT)


if __name__ == "__main__":
    main()
