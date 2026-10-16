"""SCENE 9｜もう一度、君と (6:00〜6:30) 朝の神社"""

import math

from mathutils import Vector

from lib import MB, Actor, Cams, collection, ease, mat, reset_scene, set_sun, vlerp
from sc1 import HAIR, MIO_C, REN_C
from sets import shrine_night

TITLE = "もう一度、君と"
SHOTS = [
    dict(id="9-1", dur=4, size="ロング / 28mm", move="FIX",
         desc="朝。静かな京都の神社。鳥居の向こうから朝日。倒れている二人", lines=[], fade_in="white"),
    dict(id="9-2", dur=4, size="ミディアム / 35mm", move="FIX",
         desc="蓮が目を覚まし、隣に倒れている澪に慌てて駆け寄る", lines=[]),
    dict(id="9-3", dur=4, size="澪の顔 俯瞰 / 50mm", move="ゆっくり寄り",
         desc="胸が上下している。澪はゆっくり目を開ける", lines=[(2.8, "澪", "……蓮？")]),
    dict(id="9-4", dur=5, size="2S / 35mm", move="ゆっくり回り込み",
         desc="抱きしめる。泣きながら微笑む二人", lines=[(1.6, "澪", "本当に……帰ってこられたんだね")]),
    dict(id="9-5", dur=4, size="蓮のアップ / 85mm", move="FIX", desc="蓮が口を開く。しかし、声は出ない", lines=[],
         silent=True),
    dict(id="9-6", dur=5, size="手元アップ / 85mm", move="FIX",
         desc="澪は理解し、蓮の手をそっと握って二回たたく", lines=[(3.4, "澪", "……聞こえてるよ")],
         sfx=[(1.8, "tap"), (2.3, "tap")]),
    dict(id="9-7", dur=4, size="ロング / 24mm", move="クレーンアップ",
         desc="蓮が微笑む。二人は手をつなぎ、朝日の中を歩き始める", lines=[], card="END"),
]

SX = 100
STAND = dict(hipz=0, legL=0, legR=0, lean=0, head=0, armL=(0, 0.08), armR=(0, 0.08), elbowL=0.15, elbowR=0.15,
             pitch=0, rootz=0)
SIT = dict(hipz=-0.55, legL=1.45, legR=1.45, lean=0.1, pitch=0, rootz=0)


def build(tl):
    reset_scene((1.0, 0.86, 0.66))
    set_sun((0.15, 0.9, 0.4))
    coll = collection("SC9")
    shrine_night(coll, origin=(SX, 0, 0), day=True)
    sun = MB().cyl(6, 1, (SX, 120, 8), mat("sun9", (1.0, 0.97, 0.85)), rot=(math.pi / 2, 0, 0), seg=32)
    sun.obj("Sun", coll)
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)
    mio = Actor("Mio", coll, MIO_C, height=0.92, hair=HAIR, skirt=True)

    lie = dict(pitch=math.pi / 2, rootz=0.17)
    ren.key(1, loc=(SX - 0.7, 11.6, 0), yaw=0, **lie, armL=(0, 0.3), armR=(0, 0.3))
    mio.key(1, loc=(SX + 0.6, 11.3, 0), yaw=0.2, **lie, armL=(0, 0.3), armR=(0, 0.3))
    cams.static("9-1", (SX + 3.0, 6.6, 2.7), (SX, 10.9, 0.2), 28)

    # 9-2: 目を覚ます → 澪のもとへ
    ren.key(F("9-2", 0.3), head=0.0)
    ren.key(F("9-2", 1.3), loc=(SX - 0.7, 10.3, 0), yaw=0.4, **SIT)
    ren.key(F("9-2", 2.2), loc=(SX - 0.3, 10.4, 0), yaw=-1.2, lean=0.5, hipz=-0.45, legL=-1.4, legR=-1.4,
            armL=(1.3, 0.1), armR=(1.3, 0.1), head=0.4)
    ren.key(F("9-2", 3.4), loc=(SX - 0.05, 10.2, 0))
    cams.static("9-2", (SX - 3.2, 8.2, 1.2), (SX, 10.4, 0.4), 35)

    # 9-3: 澪が目を開ける
    for i, t in enumerate((0.3, 1.0, 1.7, 2.4)):
        mio.key(F("9-3", t), lean=0.04 if i % 2 else 0.0)
    mio.key(F("9-3", 2.6), head=-0.35)
    mh = Vector((SX + 0.6 + 1.45 * math.sin(0.2), 11.3 - 1.45 * math.cos(0.2), 0.3))
    cams.move("9-3", mh + Vector((0.3, -0.6, 1.4)), mh, mh + Vector((0.2, -0.4, 1.0)), mh, 50)

    # 9-4: 抱きしめる
    mio.key(F("9-4", 0.2), loc=(SX + 0.6, 10.3, 0), yaw=math.pi / 2 + 0.3, **SIT, head=0)
    ren.key(F("9-4", 0.2), loc=(SX - 0.15, 10.3, 0), yaw=-math.pi / 2 + 0.3, **SIT, head=0)
    hug = dict(armL=(1.2, -0.3), armR=(1.2, -0.3), elbowL=0.9, elbowR=0.9, lean=0.25)
    mio.key(F("9-4", 1.0), loc=(SX + 0.45, 10.3, 0), **hug)
    ren.key(F("9-4", 1.0), loc=(SX - 0.0, 10.3, 0), **hug)
    cams.track("9-4", lambda f, k: (Vector((SX + 0.22 + 2.2 * math.sin(-0.6 + k * 0.8),
                                             10.3 - 2.2 * math.cos(-0.6 + k * 0.8), 1.2)),
                                    Vector((SX + 0.22, 10.3, 0.85))), 35)

    # 9-5: 声が出ない (二人は並んで座り、朝日の方を向く)
    side = dict(SIT, lean=0.1, head=0, armL=(0.2, 0.15), armR=(0.2, 0.15), elbowL=0.3, elbowR=0.3)
    ren.key(F("9-5", 0.0), loc=(SX - 0.3, 10.3, 0), yaw=0, **side)
    mio.key(F("9-5", 0.0), loc=(SX + 0.32, 10.3, 0), yaw=0, **side)
    ren.key(F("9-5", 1.0), head=-0.2)
    ren.key(F("9-5", 2.5), head=-0.1)
    ren.key(F("9-5", 3.5), head=0.25)
    hd = ren.head_at(F("9-5", 1.5))
    cams.static("9-5", hd + Vector((0.35, 1.2, -0.1)), hd, 85)

    # 9-6: 地面についた蓮の手を、澪がトン、トン
    p = Vector((SX + 0.01, 10.45, 0.05))
    ren.reach(F("9-6", 0.3), "R", p)
    mio.reach(F("9-6", 0.6), "L", p + Vector((0, 0, 0.07)))
    for t in (1.8, 2.3):
        mio.reach(F("9-6", t - 0.15), "L", p + Vector((0, 0, 0.2)))
        mio.reach(F("9-6", t), "L", p + Vector((0, 0, 0.07)))
    mio.key(F("9-6", 3.2), head=0.15)
    cams.static("9-6", p + Vector((0.05, 0.85, 0.75)), p + Vector((0, 0, 0.05)), 50)

    # 9-7: 手をつないで朝日の中へ
    s7, e7 = tl.range("9-7")
    ren.key(s7, loc=(SX - 0.35, 10.3, 0), yaw=0, **STAND)
    mio.key(s7, loc=(SX + 0.35, 10.1, 0), yaw=0, **STAND)
    ren.move(F("9-7", 0.8), e7, [(SX - 0.35, 10.3), (SX - 0.35, 16)], "walk", extra=lambda f: dict(armR=(0.3, 0.45)))
    mio.move(F("9-7", 0.8), e7, [(SX + 0.35, 10.1), (SX + 0.35, 15.8)], "walk", extra=lambda f: dict(armL=(0.2, 0.45)))
    cams.move("9-7", (SX + 0.4, 5.5, 1.3), (SX, 14, 1.4), (SX + 0.4, 4.0, 6.5), (SX, 20, 3), 24)
