"""SCENE 8｜最後の声 (5:15〜6:00)"""

import math
import random

import bpy
from mathutils import Vector

from lib import (MB, Cams, Crow, collection, ease, frames, key_tr, lerp, mat, reflect, ripple, shake, visible,
                 vlerp)
from sc7 import GATE_S, GATE_Y, STAND, build_world, drop_tile, make_pair, run_pair
from sets import HIGAN_SKY

TITLE = "最後の声"
SHOTS = [
    dict(id="8-1", dur=5, size="大ロング / 28mm", move="FIX",
         desc="夜明けが近づく。最後の鳥居が崩れ始める", lines=[], sfx=[(1.0, "crash")]),
    dict(id="8-2", dur=6, size="2S 横顔 / 50mm", move="FIX", desc="向かい合う二人",
         lines=[(0.5, "蓮", "澪……"), (2.0, "澪", "……うん"), (3.6, "蓮", "愛してる")]),
    dict(id="8-3", dur=4, size="蓮ナメ澪 / 50mm", move="FIX", desc="", lines=[(0.6, "澪", "私も、愛してる")]),
    dict(id="8-4", dur=6, size="ミディアム→見上げ / 35mm", move="ティルトアップ",
         desc="蓮の声が金色の光となって口元から流れ出し、小さな鳥の形になって巨大なカラスのくちばしへ吸い込まれる",
         lines=[], sfx=[(0.3, "chime")]),
    dict(id="8-5", dur=4, size="蓮のアップ / 50mm", move="FIX", desc="蓮は声を失う（無音）", lines=[], silent=True),
    dict(id="8-6", dur=5, size="ロング / 24mm", move="FIX",
         desc="番人が翼を広げ、道をふさいでいた建築物を押し退ける。門が開く", lines=[], sfx=[(0.5, "rumble")]),
    dict(id="8-7", dur=5, size="蓮ナメ澪 / 35mm", move="FIX",
         desc="足元の道は崩れ続けている。澪が振り返ると、蓮が立ち止まっている", lines=[(1.0, "澪", "蓮！ こっち！")],
         sfx=[(0.2, "crash")]),
    dict(id="8-8", dur=5, size="ロー 横 / 28mm", move="FIX",
         desc="叫ぼうとしても声が出ない。代わりに水面を二回たたく。二つの波紋が澪へ届く", lines=[],
         sfx=[(2.5, "tap"), (3.0, "tap")]),
    dict(id="8-9", dur=5, size="背中 / 24mm", move="追従→光へ",
         desc="差し出された手を握り、二人は最後の鳥居へ。光の中へ飛び込む", lines=[], fade="white"),
]

DAWN = (0.42, 0.3, 0.42)


def gold_bird(coll):
    g = mat("voice_gold", (1.0, 0.82, 0.3))
    root = MB().sphere(0.05, (0, 0, 0), g, scale=(0.8, 1.6, 0.8), sub=2).obj("VoiceBird", coll)
    wings = []
    for x in (-1, 1):
        w = MB().box((0.14, 0.07, 0.006), (0.07 * x, 0, 0), g).obj(f"VoiceWing{x}", coll, root)
        w.rotation_mode = "XYZ"
        wings.append((w, x))
    trail = [MB().sphere(0.025, (0, 0, 0), g).obj(f"Spark{i}", coll) for i in range(10)]
    return root, wings, trail


def build(tl):
    coll = collection("SC8")
    ctx = build_world(tl, coll)
    world = ctx["world"]
    F = tl.f
    cams = Cams(tl, coll)
    ren, mio = make_pair(coll, world)
    crow = Crow("Crow", coll)
    reflect(crow.root, world["mirror"], coll)
    sc = bpy.context.scene

    # 夜明け: 背景色を少しずつ明るく
    for f, c in ((1, HIGAN_SKY), (tl.end_frame, DAWN)):
        sc.world.color = c
        sc.world.keyframe_insert("color", frame=f)

    crow_pos = Vector((0, GATE_Y + 3, 22))
    crow.key(1, loc=crow_pos, yaw=math.pi, scale=40, flap=0.1)
    ren.key(1, loc=(-0.4, 96, 0), yaw=-math.pi / 2, **STAND)
    mio.key(1, loc=(0.4, 96, 0), yaw=math.pi / 2, **STAND)

    # 8-1: 鳥居が崩れ始める
    rng = random.Random(3)
    for i in range(10):
        x = rng.uniform(-8, 8)
        d = MB().box((rng.uniform(0.6, 1.4), 0.8, 0.5), (0, 0, 0), mat("debris", (0.7, 0.14, 0.1))).obj(
            f"Debris{i}", coll, loc=(x, GATE_Y, GATE_S * 2.7))
        f0 = F("8-1", 0.6 + i * 0.25) if i < 6 else F("8-6", 0.3 + (i - 6) * 0.3)
        key_tr(d, 1, loc=(x, GATE_Y, GATE_S * 2.7), rot=(0, 0, 0))
        key_tr(d, f0, loc=(x, GATE_Y, GATE_S * 2.7), rot=(0, 0, 0))
        key_tr(d, f0 + 30, loc=(x + rng.uniform(-1, 1), GATE_Y - rng.uniform(0, 3), -4),
               rot=(rng.uniform(-2, 2), rng.uniform(-2, 2), 0))
    cams.static("8-1", (16, 80, 4), (0, GATE_Y - 4, 8), 28)

    # 8-2〜8-3: 愛してる
    cams.static("8-2", (0, 93.4, 1.5), (0, 96, 1.45), 50)
    mio.key(F("8-2", 2.0), head=0.15)
    mio.key(F("8-2", 2.6), head=0.0)
    ren.key(F("8-2", 3.4), lean=0.05)
    cams.static("8-3", (-1.3, 96.8, 1.6), (0.4, 96, 1.42), 50)

    # 8-4: 声が金色の鳥になる
    s4, e4 = tl.range("8-4")
    bird, wings, trail = gold_bird(coll)
    mouth = Vector((-0.27, 96.0, 1.55))
    beak = crow_pos + Vector((0, -0.25 * 40, 0.22 * 40))
    p_mid = Vector((1.5, 98, 8))
    path = lambda k: mouth.lerp(p_mid, k * 2) if k < 0.5 else p_mid.lerp(beak, (k - 0.5) * 2)
    for f in frames(s4, e4):
        k = ease((f - s4) / (e4 - s4 - 12)) if f < e4 - 12 else 1.0
        p = path(k)
        key_tr(bird, f, loc=p, scale=lerp(1.0, 4.5, min(1, k * 3)))
        for w, x in wings:
            key_tr(w, f, rot=(0, -x * 0.8 * math.sin(f * 0.9), 0))
        for i, sp in enumerate(trail):
            kk = max(0.0, k - 0.025 * (i + 1))
            key_tr(sp, f, loc=path(kk) + shake(0.08, f + i), scale=2.5 * (1 - i * 0.08))
    for o in [bird] + trail:
        visible(o, s4, e4 - 6)
    ren.key(F("8-4", 0.3), head=-0.25, lean=-0.05)
    crow.key(F("8-4", 4.6), peck=0.0)
    crow.key(F("8-4", 5.2), peck=0.3)
    crow.key(F("8-4", 5.8), peck=0.0)
    cams.track("8-4", lambda f, k: (Vector((2.2, 92.6, 1.0)), vlerp((-0.3, 96, 1.5), path(ease(min(1, k * 1.15))), ease(k))),
               35)

    # 8-5: 喉に手を当てる
    ren.key(F("8-5", 0.3), head=0.0)
    ren.key(F("8-5", 1.2), head=0.2)
    throat = ren.head_at(F("8-5", 1.2)) + Vector((0.12, 0, -0.13))
    ren.reach(F("8-5", 1.2), "R", throat)
    hd = ren.head_at(F("8-5", 2.0)) - Vector((0, 0, 0.1))
    cams.static("8-5", (0.85, 96.5, hd.z + 0.15), hd, 50)  # 澪の肩越し

    # 8-6: 翼を広げ、門が開く
    s6, e6 = tl.range("8-6")
    crow.key(s6, flap=0.1)
    crow.key(F("8-6", 1.5), flap=0.7)
    crow.key(F("8-6", 3.0), flap=0.2)
    door = ctx["door"]
    key_tr(door, 1, scale=(1, 1, 1))
    key_tr(door, F("8-6", 1.8), scale=(1, 1, 1))
    key_tr(door, F("8-6", 3.8), scale=(1, 1, 0.001))
    ren.key(s6, armR=(0, 0.08), head=-0.2, yaw=0)
    mio.key(s6, head=-0.2, yaw=0)
    cams.static("8-6", (9, 82, 2.5), (0, GATE_Y, 9), 24)

    # 8-7: 崩れる道。澪が振り返る
    s7, e7 = tl.range("8-7")
    mio.move(s7, F("8-7", 0.9), [(0.4, 96), (0.3, 100.5)], "run")
    mio.key(F("8-7", 1.1), yaw=math.pi, armR=(1.0, 0.3), head=0)
    ren.key(F("8-7", 0.5), head=0.1)
    for y, o in ctx["tiles"].items():
        if 84 <= y <= 94:
            drop_tile(o, F("8-7", 0.2 + (94 - y) * 0.1), seed=y)
    cams.static("8-7", (-1.6, 93.6, 1.75), (0.3, 100.5, 1.3), 35)

    # 8-8: 声が出ない → 水面をトン、トン
    ren.key(F("8-8", 0.2), head=-0.3, lean=-0.1)
    ren.key(F("8-8", 1.2), head=-0.3, lean=-0.1)
    # 水面に膝をつき (すねは水面下)、手で水面をトン、トン
    ren.key(F("8-8", 1.9), loc=(-0.4, 96, 0), rootz=-0.45, legL=0, legR=0, lean=0.55, head=0.25, blend=10)
    water = Vector((0.1, 96.1, 0.02))
    ren.reach(F("8-8", 1.9), "R", water + Vector((0, 0, 0.15)))
    for t in (2.5, 3.0):
        ren.reach(F("8-8", t - 0.15), "R", water + Vector((0, 0, 0.18)))
        ren.reach(F("8-8", t), "R", water)
        ripple(coll, water, F("8-8", t), 1.6, 5.0, width=0.08)
    mio.key(F("8-8", 3.8), head=0.2)
    cams.static("8-8", (2.1, 94.0, 0.9), (-0.2, 97.2, 0.45), 28)

    # 8-9: 手を取り、光へ
    s9, e9 = tl.range("8-9")
    mio.key(s9, armR=(1.4, 0.0), head=0)
    ren.key(s9, **STAND)
    ren.move(F("8-9", 0.3), F("8-9", 1.5), [(-0.4, 96), (0.0, 100.2)], "run")
    mio.key(F("8-9", 1.6), yaw=0)
    run = run_pair(ren, mio, F("8-9", 1.7), F("8-9", 4.2), [(0.15, 100.4), (0.15, GATE_Y + 1.5)], "sprint")
    for a in (ren, mio):
        visible(a.root, None, F("8-9", 4.3))
    cams.track("8-9", lambda f, k: (Vector((0.6, 95.0 + 4 * ease(k), 1.4)) + shake(0.02, f), Vector((0, GATE_Y, 3.5))),
               24)
