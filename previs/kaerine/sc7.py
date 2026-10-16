"""SCENE 7｜彼岸の番人 (4:10〜5:15) 巨大な番人との追走劇"""

import math
import random

import bpy
from mathutils import Vector

from lib import (MB, Actor, Cams, Crow, collection, ease, frames, key_tr, lerp, mat, reflect, reset_scene, ripple,
                 set_sun, shake, torii, visible, vlerp)
from sc1 import HAIR, MIO_C, REN_C
from sets import HIGAN_SKY, higan, temple

TITLE = "彼岸の番人"
SHOTS = [
    dict(id="7-1", dur=5, size="ロー / 24mm", move="FIX",
         desc="手をつなぎ門へ向かう二人。カラスが夜空へ飛び上がる", lines=[]),
    dict(id="7-2", dur=6, size="ロング / 24mm", move="ティルトアップ",
         desc="翼が巨大化して空を覆い、カラスは巨大な番人へと変貌する", lines=[], sfx=[(1.0, "rumble")]),
    dict(id="7-3", dur=5, size="翼のアップ / 50mm", move="FIX",
         desc="羽根の隙間から無数の古い鐘が現れ、鳴り響く", lines=[], sfx=[(1.6, "bell"), (2.6, "bell"), (3.6, "bell")]),
    dict(id="7-4", dur=6, size="二人ナメ番人 / 24mm", move="FIX",
         desc="", lines=[(0.4, "返り烏", "ならば示せ。夜明けまでに境界を越え、"), (3.0, "返り烏", "その覚悟を果たしてみせよ")]),
    dict(id="7-5", dur=5, size="空撮 / 28mm", move="ゆっくり旋回",
         desc="鐘が鳴るたび水面に巨大な波紋。頭上の建築が回転し、浮遊する神殿や橋が位置を変える", lines=[],
         sfx=[(0.5, "bell"), (2.5, "bell")]),
    dict(id="7-6", dur=5, size="フルショット / 35mm", move="横移動で並走",
         desc="足元の道が崩れ始める。蓮が澪の手を引き全力で走る", lines=[], sfx=[(0.5, "crash")]),
    dict(id="7-7", dur=5, size="正面 / 24mm", move="後退しながら追従・手持ち",
         desc="巨大な柱が落下。二人は避けて走る", lines=[], sfx=[(1.5, "crash")]),
    dict(id="7-8", dur=5, size="空撮 / 28mm", move="追従",
         desc="水面から次々と建築物が立ち上がり、進む道が分断される", lines=[], sfx=[(0.5, "rumble")]),
    dict(id="7-9", dur=6, size="ミディアム / 35mm", move="FIX",
         desc="裂け目に落ちかけた澪を、蓮が引き上げる", lines=[]),
    dict(id="7-10", dur=5, size="ミディアム / 35mm", move="FIX",
         desc="今度は蓮が足を滑らせ、澪が蓮を助ける", lines=[]),
    dict(id="7-11", dur=6, size="正面ロー / 24mm", move="後退しながら追従",
         desc="背後から番人の巨大な翼が迫る", lines=[], sfx=[(0.5, "wind")]),
    dict(id="7-12", dur=6, size="ロング / 28mm", move="ゆっくり寄り",
         desc="ついに最後の鳥居。しかし門は閉じたまま", lines=[(2.4, "返り烏", "最後の代償を差し出せ")]),
]

GATE_Y = 104.0
GATE_S = 6.0
STAND = dict(hipz=0, legL=0, legR=0, lean=0, head=0, armL=(0, 0.08), armR=(0, 0.08))


def build_world(tl, coll, sky=HIGAN_SKY):
    """SC7・SC8 共通: 彼岸 + 一本道 + 最後の鳥居 (閉じた門)"""
    reset_scene(sky)
    set_sun((0.25, -0.6, 0.75))
    world = higan(coll, seed=47, gate=False)
    mb = MB()
    torii(mb, (0, GATE_Y, 0), 0, scale=GATE_S, red=(0.7, 0.12, 0.08))
    gate = mb.obj("FinalTorii", coll)
    door = MB().box((9.6, 0.3, 12.0), (0, 0, 6.0), mat("gate_closed", (0.12, 0.08, 0.2))).obj("GateDoor", coll,
                                                                                              loc=(0, GATE_Y, 0))
    light = MB().box((9.6, 0.2, 12.0), (0, 0, 6.0), mat("gate_open", (1.0, 0.95, 0.8))).obj("GateLight", coll,
                                                                                          loc=(0, GATE_Y + 0.3, 0))
    for o in (gate, door, light):
        reflect(o, world["mirror"], coll)
    # 一本道の石
    tiles = {}
    stone = mat("path_stone", (0.62, 0.66, 0.78))
    y = -2.0
    while y < GATE_Y + 2:
        o = MB().box((2.4, 1.9, 0.12), (0, 0, -0.06), stone).obj(f"Path{y:.0f}", coll, loc=(0, y, 0))
        tiles[round(y)] = o
        y += 2.0
    city = bpy.data.objects["FloatingCity"]
    city_refl = [o for o in world["mirror"].children if o.name.startswith("FloatingCity")][0]
    return dict(world=world, gate=gate, door=door, light=light, tiles=tiles, city=(city, city_refl))


def drop_tile(o, f, depth=6.0, seed=0):
    rng = random.Random(seed)
    key_tr(o, f, loc=o.location.copy(), rot=(0, 0, 0))
    key_tr(o, f + 30, loc=o.location + Vector((rng.uniform(-0.5, 0.5), 0, -depth)),
           rot=(rng.uniform(-1, 1), rng.uniform(-1, 1), 0))


def make_pair(coll, world):
    ren = Actor("Ren", coll, REN_C)
    mio = Actor("Mio", coll, MIO_C, height=0.92, hair=HAIR, skirt=True)
    for o in (ren.root, mio.root):
        reflect(o, world["mirror"], coll)
    return ren, mio


def run_pair(ren, mio, f0, f1, pts, style="run", gap=0.38):
    """手をつないで並走 (蓮が左、澪が右)"""
    rp = [(p[0] - gap, p[1]) for p in pts]
    mp = [(p[0] + gap, p[1] - 0.25) for p in pts]
    a = ren.move(f0, f1, rp, style, extra=lambda f: dict(armR=(0.35, 0.45)))
    b = mio.move(f0, f1, mp, style, extra=lambda f: dict(armL=(0.25, 0.45)))
    return lambda f: (a(f) + b(f)) / 2


def build(tl):
    coll = collection("SC7")
    ctx = build_world(tl, coll)
    world = ctx["world"]
    F = tl.f
    cams = Cams(tl, coll)
    ren, mio = make_pair(coll, world)
    crow = Crow("Crow", coll)
    reflect(crow.root, world["mirror"], coll)

    # 7-1: 歩き出す / カラスが飛び上がる
    s1, _ = tl.range("7-1")
    walk = run_pair(ren, mio, s1, F("7-1", 5.0), [(0, 0), (0, 6)], "walk")
    crow.key(1, loc=(1.6, 1.0, 0), yaw=0, scale=1.6)
    crow.fly(F("7-1", 1.5), F("7-1", 5.0), [(1.6, 1.0, 0), (1, 8, 6), (0, 25, 18), (0, 45, 28)], scale=1.6)
    cams.static("7-1", (0.6, -4.5, 0.35), (0, 16, 6), 24)

    # 7-2: 巨大化
    s2, e2 = tl.range("7-2")
    for f in frames(s2, e2):
        k = ease((f - s2) / (e2 - s2))
        crow.key(f, loc=(0, 45, 28), yaw=math.pi, scale=lerp(1.6, 40, k), flap=lerp(-1.2, 0.15, k))
    ren.key(s2, **STAND, yaw=0)
    mio.key(s2, **STAND, yaw=0)
    ren.key(F("7-2", 2.0), head=-0.4, lean=-0.1, armR=(0.3, 0.45))
    mio.key(F("7-2", 2.0), head=-0.4, lean=-0.1, armL=(0.3, 0.45))
    cams.move("7-2", (2.2, -1.5, 1.2), (0, 20, 4), (2.6, -2.5, 0.8), (0, 45, 30), 24)

    # 7-3: 鐘
    crow.bells(coll, F("7-3", 0.3), F("7-5", 5.0), ring=[F("7-3", t) for t in (1.6, 2.6, 3.6)] +
               [F("7-5", t) for t in (0.5, 2.5)])
    cams.static("7-3", (14, 18, 22), (6, 45, 30), 50)

    # 7-4: 番人が語る
    crow.key(F("7-4", 0.4), peck=0.25)
    crow.key(F("7-4", 1.2), peck=0.0)
    crow.key(F("7-4", 3.0), peck=0.25)
    crow.key(F("7-4", 3.8), peck=0.0)
    cams.static("7-4", (1.2, 3.2, 1.0), (0, 38, 26), 35)

    # 7-5: 巨大な波紋と回転する建築
    for t in (0.5, 2.5):
        ripple(coll, (0, 45, 0), F("7-5", t), 3.0, 90, width=1.5)
    for o in ctx["city"]:
        key_tr(o, F("7-5", 0.0), rot=(0, 0, 0))
        key_tr(o, F("7-12", 6.0), rot=(0, 0, 0.9))
    cams.track("7-5", lambda f, k: (Vector((50 * math.cos(-1.3 + k * 0.4), 50 * math.sin(-1.3 + k * 0.4) + 20, 34)),
                                    Vector((0, 25, 4))), 28)

    # 7-6: 道が崩れる → 走り出す
    s6, e6 = tl.range("7-6")
    run = run_pair(ren, mio, F("7-6", 0.6), e6, [(0, 6), (0, 22)], "run")
    for y, o in ctx["tiles"].items():
        if 2 <= y <= 18:
            drop_tile(o, F("7-6", 0.4 + (y - 2) * 0.12), seed=y)
    cams.track("7-6", lambda f, k: (run(f) + Vector((6.5, 0.5, 1.4)), run(f) + Vector((0, 0.5, 1.0))), 35)

    # 7-7: 柱の落下
    s7, e7 = tl.range("7-7")
    run = run_pair(ren, mio, s7, e7, [(0, 22), (0, 27), (-2.2, 31), (-2.2, 36)], "run")
    pillar = MB().cyl(1.3, 26, (0, 0, 13), mat("pillar", (0.5, 0.45, 0.55)), seg=12).obj("Pillar", coll)
    key_tr(pillar, 1, loc=(4, 30, 60), rot=(0.1, 0, 0))
    key_tr(pillar, F("7-7", 0.4), loc=(4, 30, 60), rot=(0.1, 0, 0))
    key_tr(pillar, F("7-7", 1.5), loc=(2.0, 20, 1.3), rot=(-math.pi / 2, 0, 0.05))
    reflect(pillar, world["mirror"], coll)
    cams.track("7-7", lambda f, k: (run(f) + Vector((0.3, 5, 1.0)) + shake(0.05 if f > F("7-7", 1.5) else 0.01, f),
                                    run(f) + Vector((0, 0, 1.1))), 24)

    # 7-8: 建築がせり上がる
    s8, e8 = tl.range("7-8")
    run = run_pair(ren, mio, s8, e8, [(-2.2, 36), (-2.2, 42), (0, 46), (0, 50)], "run")
    for i, (x, y) in enumerate(((3.5, 40), (-6, 44), (4.5, 47), (-3.5, 50.5), (6, 52))):
        mb = MB()
        temple(mb, (0, 0, 0), 5, 4, 3, mat("hg_wall", (0.55, 0.5, 0.62)), mat("hg_roof", (0.15, 0.13, 0.22)))
        o = mb.obj(f"Rise{i}", coll, loc=(x, y, -8))
        key_tr(o, 1, loc=(x, y, -8))
        key_tr(o, F("7-8", 0.3 + i * 0.5), loc=(x, y, -8))
        key_tr(o, F("7-8", 1.3 + i * 0.5), loc=(x, y, 0))
        reflect(o, world["mirror"], coll)
    cams.track("7-8", lambda f, k: (run(f) + Vector((-10, -14, 16)), run(f) + Vector((0, 6, 0))), 28)

    # 7-9: 裂け目 (y=52) で澪を引き上げる
    for y in (52,):
        drop_tile(ctx["tiles"][y], F("7-8", 4.0), seed=99)
    s9, _ = tl.range("7-9")
    ren.key(s9, loc=(-0.2, 53.8, 0), yaw=math.pi, **STAND)
    ren.key(F("7-9", 0.3), hipz=-0.5, legL=-1.45, legR=-1.45, lean=0.9, armR=(2.6, 0.1), armL=(2.6, 0.1))
    mio.key(s9, loc=(0.0, 52.6, -1.25), yaw=0, **STAND)
    mio.key(F("7-9", 0.3), armL=(3.0, 0.1), armR=(3.0, 0.1), head=-0.3)
    mio.key(F("7-9", 1.5), loc=(0.0, 52.7, -1.1))
    mio.key(F("7-9", 3.0), loc=(0.0, 53.0, -0.2), lean=0.3)
    mio.key(F("7-9", 3.8), loc=(0.0, 53.3, 0), lean=0.2, armL=(0, 0.08), armR=(0, 0.08), head=0)
    ren.key(F("7-9", 3.8), lean=0.2, hipz=-0.2, armR=(0.6, 0.1), armL=(0.6, 0.1))
    ren.key(F("7-9", 4.6), **STAND)
    cams.static("7-9", (2.8, 55.6, 1.6), (0, 53.0, 0.1), 35)

    # 7-10: 次の裂け目 (y=58) で蓮が足を滑らせる
    for y in (58,):
        drop_tile(ctx["tiles"][y], F("7-9", 5.0), seed=98)
    s10, _ = tl.range("7-10")
    run_pair(ren, mio, s10, F("7-10", 1.2), [(0, 53.4), (0, 56.6)], "run")
    ren.key(F("7-10", 1.4), loc=(-0.38, 57.4, -0.3), lean=-0.35, armL=(2.2, 1.2), armR=(2.0, 1.0), legL=0.5)
    ren.key(F("7-10", 2.0), loc=(-0.38, 57.5, -0.7), lean=-0.45)
    mio.key(F("7-10", 1.6), loc=(0.2, 56.4, 0), yaw=-0.6, lean=-0.35, armL=(1.2, 0.6), armR=(1.0, 0.3))
    mio.key(F("7-10", 3.0), loc=(0.2, 56.2, 0), lean=-0.5)
    ren.key(F("7-10", 3.0), loc=(-0.3, 56.6, 0), lean=0.1, armL=(0, 0.08), armR=(1.0, 0.6), legL=0)
    ren.key(F("7-10", 4.0), **STAND)
    mio.key(F("7-10", 4.0), **STAND, yaw=0)
    cams.static("7-10", (-4.4, 56.0, 1.3), (0, 57.0, 0.5), 35)

    # 7-11: 翼が迫る
    s11, e11 = tl.range("7-11")
    run = run_pair(ren, mio, s11, e11, [(0, 59), (0, 86)], "sprint")
    for f in frames(s11, e11):
        k = (f - s11) / (e11 - s11)
        p = run(f)
        crow.key(f, loc=(0, p.y - lerp(30, 16, k), lerp(14, 9, k)), yaw=0, scale=40, flap=0.25 * math.sin(k * 6))
    cams.track("7-11", lambda f, k: (run(f) + Vector((0.6, 4.5, 0.5)) + shake(0.03, f), run(f) + Vector((0, -6, 3))),
               24)

    # 7-12: 閉じた門
    s12, _ = tl.range("7-12")
    run_pair(ren, mio, s12, F("7-12", 1.8), [(0, 86), (0, 96)], "run")
    ren.key(F("7-12", 2.1), **STAND, yaw=0)
    mio.key(F("7-12", 2.1), **STAND, yaw=0)
    crow.fly(s12, F("7-12", 2.0), [(0, 70, 12), (0, 90, 24), (0, GATE_Y + 3, 22)], scale=40, beat=10, amp=0.4)
    crow.key(F("7-12", 2.2), yaw=math.pi, flap=0.1)
    crow.key(F("7-12", 2.4), peck=0.25)
    crow.key(F("7-12", 3.4), peck=0.0)
    cams.move("7-12", (2.5, 87, 1.2), (0, GATE_Y, 4.0), (1.8, 90, 1.2), (0, GATE_Y, 4.5), 28)
