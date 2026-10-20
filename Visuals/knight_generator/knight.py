from PIL import Image

PAL = {
 '.': None,
 'K': (24,18,26), 'H': (247,200,108), 'h': (226,150,72), 'd': (168,98,52), 'L': (255,232,160),
 'S': (245,192,150), 's': (212,138,104), 'm': (226,128,110),
 'W': (230,226,214), 'G': (164,166,176), 'g': (104,106,120),
 'b': (92,62,48), 'Y': (240,188,64),
}
def mirror(half):  # 16-char left half -> 32 row
    assert len(half)==16, half
    return half + half[::-1]

# ---------- FRONT (south) ----------
FRONT_HEAD = [mirror(r) for r in [
"................","................","................",
"..........KKKKKK",
"........KKHHHHHH",
".......KHHLLHHHH",
"......KHHLLHHHHh",
".....KHHLHHHHHHh",
".....KHHHHHHHHhK",
"....KhHHHHHHHhKS",
"....KhHHHHHhKKSS",
"....KhHHHhKKSSSS",
"....KhHHhKSSSSSS",
"....KhhhKSSSSSSS",
"....KKhKSSSKKSSS",
"...KsKKSSSSKKSSS",
"...KsSKSSSSKKSSS",
"....KsKmSSSSSSSS",
".....KKSsSSSSSSS",
"......KKssSSSSSS",
]]
FRONT_HEAD_BLINK = list(FRONT_HEAD)
FRONT_HEAD_BLINK[14] = mirror("....KKhKSSSSSSSS")
FRONT_HEAD_BLINK[15] = mirror("...KsKKSSSSSSSSS")
FRONT_HEAD_BLINK[16] = mirror("...KsSKSSSKKKSSS")
FRONT_BODY = [mirror(r) for r in [
"........KKKKKKKK",
".......KGGWWWWWW",
"......KGGKGWWWWW",
"......KGgKGWWWWW",
"......KggKgGGGGG",
"......KKKKbbbbbY",
]]
def legs_sym(rows): return [mirror(r) for r in rows]
FRONT_LEGS_STAND = legs_sym([
".........KgGGGGG",
".........KgGGgKK",
".........KgggK..",
".........KKKKK..",
])
FRONT_LEGS_L = [  # viewer-left leg planted, right leg lifted
".........KgGGGGGGGGGGgK.........",
".........KgGGgKKKKgGGgK.........",
".........KgggK....KKKKK.........",
".........KKKKK..................",
]
FRONT_LEGS_R = [r[::-1] for r in FRONT_LEGS_L]

# ---------- BACK (north) ----------
BACK_HEAD = [mirror(r) for r in [
"................","................","................",
"..........KKKKKK",
"........KKHHHHHH",
".......KHHLLHHHH",
"......KHHLLHHHHH",
".....KHHLHHHHHHH",
".....KHHHHHHHHHH",
"....KhHHHHHHHHHH",
"....KhHHHHHHHHHH",
"....KhHHHHHHHHHH",
"....KhhHHHHHHHHH",
"....KhhHHHHHHhHH",
"....KKhhHHHHHhHH",
"...KsKhhHHHHhHHH",
"...KsKhhhHHHhHHH",
"....KKhhhhHhhHHh",
".....KKhhhhhhhhh",
"......KKdddddddd",
]]
BACK_BODY = [mirror(r) for r in [
"........KKKKKKKK",
".......KGGWWGGGG",
"......KGGKGWGGGg",
"......KGgKgGGGGg",
"......KggKggGGGg",
"......KKKKbbbbbb",
]]

# ---------- SIDE (east, facing right) ----------
SIDE_HEAD = [
"................................",
"................................",
"................................",
"..........KKKKKKKKKK............",
"........KKHHHHHHHHHHKK..........",
".......KHHHHHHHHHLLHHHK.........",
"......KHHHHHHHHHHHLLHHHK........",
".....KHHHHHHHHHHHHHHLHHHK.......",
".....KHHHHHHHHHHHHHHHHHHHK......",
"....KhHHHHHHHHHHHHHHHHHhhK......",
"....KhHHHHHHHHHHHHHHHhhhdK......",
"....KhHHHHHHHHHHHhhddSSSSK......",
"....KhHHHHHHHHHHhdSSSSSSSK......",
"....KhhHHHHHHHHhdSSSSSSSSK......",
"....KhhHHHhKKhdSSSSSSKKSSK......",
"....KhhhHKssSKSSSSSSSKKSSSK.....",
"....KKhhhKsSSKSSSSSSSKKSSSK.....",
".....KhhhhKKSSSSSSSSSSSSmK......",
"......KKhhhhKsSSSSSSSSSSK.......",
".......KKddddKssSSSSSssK........",
]
SIDE_BODY = [
"..........KKKKKKKKKKKK..........",
"..........KgGGGWWWWWGK..........",
".........KgGGGKKWWWWGK..........",
".........KgGGKSSKWWWGK..........",
".........KgGGKSSKGGGgK..........",
"..........KbbbKKbbbbYK..........",
]
SIDE_BODY_ARM_BACK = list(SIDE_BODY)
SIDE_BODY_ARM_BACK[2] = ".........KgGGKKWWWWWGK.........."[:32]
SIDE_BODY_ARM_BACK[3] = "........KSSKgGWWWWWGK..........."
SIDE_BODY_ARM_BACK[4] = "........KSSKgGGGGGGgK..........."
SIDE_BODY_ARM_FWD = list(SIDE_BODY)
SIDE_BODY_ARM_FWD[2] = ".........KgGGGGWWWWKK..........."
SIDE_BODY_ARM_FWD[3] = ".........KgGGGWWWWKSSK.........."
SIDE_BODY_ARM_FWD[4] = ".........KgGGGGGGgKSSK.........."
SIDE_LEGS_STAND = [
"...........KgGGGGGgK............",
"...........KgGgKgGGK............",
"...........KggKKggGK............",
"...........KKKKKKKKK............",
]
SIDE_LEGS_STRIDE = [
"...........KgGGGGGgK............",
"..........KgGKKKKgGGK...........",
".........KggK....KggGK..........",
".........KKKK....KKKKK..........",
]

HAND = ["KSK","KsK",".K."]
def compose(head, body, legs, dy=0, head_dy=0, hands=(0,0), hand_cols=(6,23)):
    g = _compose(head, body, legs, dy, head_dy)
    if hands is not None:
        for col,hy in zip(hand_cols, hands):
            for j,r in enumerate(HAND):
                for i,c in enumerate(r):
                    if c!='.': g[24+dy+hy+j][col+i]=c
    return g

def _compose(head, body, legs, dy=0, head_dy=0):
    grid = [['.']*32 for _ in range(32)]
    def stamp(rows, top):
        for j,r in enumerate(rows):
            y=top+j
            if 0<=y<32:
                for i,c in enumerate(r):
                    if c!='.': grid[y][i]=c
    stamp(legs, 26)
    stamp(body, 20+dy)
    stamp(head, 0+dy+head_dy)
    return grid

def to_img(grid):
    im = Image.new("RGBA",(32,32),(0,0,0,0))
    for y,row in enumerate(grid):
        for x,c in enumerate(row):
            if PAL[c]: im.putpixel((x,y),PAL[c]+(255,))
    return im

def hflip(grid): return [list(reversed(r)) for r in grid]

frames = {}
# walk: contact, passing(up), contact other, passing(up)
frames['walk_S'] = [compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_L,hands=(-1,1)),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND,dy=-1),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_R,hands=(1,-1)),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND,dy=-1)]
frames['walk_N'] = [compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_R,hands=(1,-1)),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND,dy=-1),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_L,hands=(-1,1)),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND,dy=-1)]
frames['walk_E'] = [compose(SIDE_HEAD,SIDE_BODY_ARM_BACK,SIDE_LEGS_STRIDE,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,dy=-1,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY_ARM_FWD,SIDE_LEGS_STRIDE,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,dy=-1,hands=None)]
frames['walk_W'] = [hflip(f) for f in frames['walk_E']]
# idle: breathe (head dips 1px on frames 2-3)
frames['idle_S'] = [compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND,head_dy=1),
                    compose(FRONT_HEAD,FRONT_BODY,FRONT_LEGS_STAND,head_dy=1)]
frames['idle_N'] = [compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND,head_dy=1),
                    compose(BACK_HEAD,BACK_BODY,FRONT_LEGS_STAND,head_dy=1)]
frames['idle_E'] = [compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,head_dy=1,hands=None),
                    compose(SIDE_HEAD,SIDE_BODY,SIDE_LEGS_STAND,head_dy=1,hands=None)]
frames['idle_W'] = [hflip(f) for f in frames['idle_E']]

ORDER = ['walk_S','walk_N','walk_E','walk_W','idle_S','idle_N','idle_E','idle_W']
sheet = Image.new("RGBA",(32*4,32*len(ORDER)),(0,0,0,0))
for r,name in enumerate(ORDER):
    for c,g in enumerate(frames[name]):
        sheet.paste(to_img(g),(c*32,r*32))
sheet.save("knight_sheet.png")
prev = Image.new("RGBA",sheet.size,(40,40,48,255)); prev.alpha_composite(sheet)
prev.resize((sheet.width*5,sheet.height*5),Image.NEAREST).save("knight_sheet_preview.png")
import pickle; pickle.dump((ORDER,frames),open("frames.pkl","wb"))
