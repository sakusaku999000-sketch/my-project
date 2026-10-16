"""SCENE 3｜四十九日目の使者 (1:20〜1:55) 部屋 → 夜の神社"""

import math

from mathutils import Vector

from lib import (MB, Actor, Cams, Crow, collection, ease, frames, key_tr, reset_scene, set_sun, torii, vlerp)
from sc1 import REN_C
from sets import room, shrine_night

TITLE = "四十九日目の使者"
SHOTS = [
    dict(id="3-1", dur=4, size="ロング / 28mm", move="FIX",
         desc="「四十九日後」。静かな部屋。遺影と白い花、二つの湯のみ。祭壇の前に座る蓮", lines=[], card="四十九日後"),
    dict(id="3-2", dur=5, size="寄り / 50mm", move="ゆっくりドリーイン",
         desc="澪の遺影", lines=[]),
    dict(id="3-3", dur=4, size="蓮の背中ナメ / 35mm", move="FIX",
         desc="写真を見つめる蓮。窓の外から奇妙な音", lines=[], sfx=[(2.5, "tap"), (3.0, "tap")]),
    dict(id="3-4", dur=5, size="ミディアム / 50mm", move="FIX",
         desc="窓辺に金色の目のカラス。くちばしで窓を二回たたく ── 二人だけの合図", lines=[],
         sfx=[(2.0, "tap"), (2.5, "tap")]),
    dict(id="3-5", dur=3, size="顔アップ / 50mm", move="FIX", desc="驚いて振り向く蓮", lines=[]),
    dict(id="3-6", dur=4, size="ロング / 24mm", move="FIX",
         desc="カラスが夜の町へ飛び去る。蓮が立ち上がり後を追う", lines=[]),
    dict(id="3-7", dur=5, size="フルショット / 35mm", move="横移動で並走",
         desc="人気のない神社。カラスを追って参道を走る蓮", lines=[]),
    dict(id="3-8", dur=5, size="ローアングル / 24mm", move="ゆっくり上昇",
         desc="霧の中、存在しないはずの千本鳥居が地面から立ち上がる。鳥居の向こうから澪の声",
         lines=[(1.8, "澪の声", "……蓮……"), (3.3, "蓮", "澪!?")]),
]

SX = 100  # 神社の位置


def build(tl):
    reset_scene((0.05, 0.06, 0.13))
    set_sun((-0.6, -0.3, 0.75))
    coll = collection("SC3")
    room(coll, altar=True)
    shrine_night(coll, origin=(SX, 0, 0))
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)
    crow = Crow("Crow", coll)

    sit = dict(hipz=-0.55, legL=1.45, legR=1.45, lean=0.1, head=0.15, armL=(0.4, 0.1), armR=(0.4, 0.1))
    ren.key(1, loc=(0.6, 0.75, 0), yaw=0, **sit)
    cams.static("3-1", (2.6, -2.3, 1.9), (0.4, 1.2, 0.7), 28)
    cams.move("3-2", (0.75, 0.95, 1.15), (0.6, 2.25, 1.0), (0.68, 1.35, 1.08), (0.6, 2.25, 1.0), 50)
    cams.static("3-3", (1.1, -0.7, 1.35), (0.5, 2.2, 0.85), 35)

    # 窓辺のカラス
    sill = Vector((-3.15, 0.6, 0.91))
    crow.key(1, loc=sill + Vector((-8, 0, 3)), yaw=-math.pi / 2, scale=1.3)
    crow.fly(F("3-3", 1.0), F("3-3", 2.2), [sill + Vector((-8, 0, 3)), sill + Vector((-1, 0, 0.4)), sill], scale=1.3)
    crow.key(F("3-3", 2.3), yaw=-math.pi / 2, flap=-1.2)
    crow.tap(F("3-3", 2.5), gap=12)
    crow.tap(F("3-4", 2.0), gap=12)
    crow.key(F("3-4", 3.6), peck=0.0)
    crow.key(F("3-4", 4.2), peck=-0.3)  # 首をかしげて部屋をのぞく
    cams.static("3-4", (-1.7, -0.1, 1.25), (-3.1, 0.6, 1.05), 50)

    # 振り向く
    ren.key(F("3-5", 0.2), yaw=0)
    ren.key(F("3-5", 0.8), yaw=math.pi / 2 - 0.2, lean=-0.05, head=-0.05)
    cams.static("3-5", (-0.8, 1.05, 1.1), (0.6, 0.75, 1.05), 50)

    # 飛び去る → 追う
    crow.fly(F("3-6", 0.3), F("3-6", 2.0), [sill, sill + Vector((-2, 0.5, 1)), sill + Vector((-14, 3, 5))], scale=1.3)
    ren.key(F("3-6", 0.9), hipz=0, legL=0, legR=0, lean=0, head=0, armL=(0, 0.08), armR=(0, 0.08))
    ren.move(F("3-6", 1.2), F("3-6", 3.9), [(0.6, 0.75), (-1.2, -0.6), (-1.5, -3.5)], "run")
    cams.static("3-6", (2.7, -2.2, 1.8), (-1.3, 0.4, 1.0), 24)

    # 夜の神社を走る
    s, e = tl.range("3-7")
    run = ren.move(s, e, [(SX - 0.3, -6), (SX, 9.5)], "run")
    crow.fly(s, e, [(SX + 0.5, -1, 3.5), (SX, 14, 3.0)], scale=1.3)
    cams.track("3-7", lambda f, k: (run(f) + Vector((4.5, -1.0, 2.6)), run(f) + Vector((0, 1.0, 1.0))), 35)

    # 千本鳥居が現れる
    s, e = tl.range("3-8")
    ren.key(s, loc=(SX, 9.5, 0), yaw=0)
    ren.key(F("3-8", 0.4), lean=-0.05)
    ren.key(F("3-8", 3.4), lean=0.15, armR=(0.5, 0.1))
    ren.move(F("3-8", 3.8), e, [(SX, 9.5), (SX, 14.5)], "run")
    crow.fly(s, F("3-8", 2.0), [(SX, 14, 3.0), (SX, 30, 4.5)], scale=1.3)
    for i in range(36):
        y = 15 + i * 1.6
        o = MB()
        torii(o, (0, 0, 0), 0)
        ob = o.obj(f"ToriiRise{i}", coll, loc=(SX, y, 0))
        t0 = 0.3 + i * 0.07
        key_tr(ob, 1, scale=(1, 1, 0.001))
        key_tr(ob, F("3-8", t0), scale=(1, 1, 0.001))
        key_tr(ob, F("3-8", t0 + 0.8), scale=(1, 1, 1))
    cams.move("3-8", (SX + 0.6, 4.8, 0.5), (SX, 20, 2.2), (SX + 0.5, 5.5, 1.4), (SX, 22, 2.0), 24)
