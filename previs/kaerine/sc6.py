"""SCENE 6｜奇跡の再会 (3:20〜4:10)"""

import math

from mathutils import Vector

from lib import Actor, Cams, Crow, collection, ease, reflect, reset_scene, ripple, set_sun, vlerp
from sc1 import HAIR, MIO_C, REN_C
from sets import HIGAN_SKY, higan

TITLE = "奇跡の再会"
SHOTS = [
    dict(id="6-1", dur=5, size="大ロング / 35mm", move="FIX",
         desc="無数の灯籠が浮かぶ静かな水面。澪が一人で立っている。遠くから蓮が近づく", lines=[]),
    dict(id="6-2", dur=5, size="水面アップ / 28mm", move="ゆっくりパン",
         desc="最初は水面に映る二人の姿だけ（実体は映さない）。波紋で像が揺らぐ", lines=[(3.0, "蓮", "澪……！")]),
    dict(id="6-3", dur=4, size="澪のアップ / 50mm", move="FIX", desc="澪が振り返る",
         lines=[(0.8, "澪", "……蓮？ どうしてここに……？")]),
    dict(id="6-4", dur=5, size="2S / 28mm", move="回り込み",
         desc="蓮が駆け寄り、抱きしめる", lines=[(3.0, "蓮", "迎えに来た。一緒に帰ろう")]),
    dict(id="6-5", dur=4, size="蓮ナメ澪 / 50mm", move="FIX", desc="澪の表情が曇る",
         lines=[(0.8, "澪", "でも……私はもう……")]),
    dict(id="6-6", dur=6, size="3S ロング / 28mm", move="FIX",
         desc="カラスが現れ、二人は離れて向き直る",
         lines=[(0.6, "返り烏", "死者を返す道は、誰にでも開かれるわけではない。"),
                (3.2, "返り烏", "呼び声に応えた魂だけに、一度だけ機会が与えられる")]),
    dict(id="6-7", dur=5, size="カラス→澪 / 50mm", move="パン",
         desc="帰還の代償が告げられる",
         lines=[(0.3, "返り烏", "死者が生へ帰るならば、生者は自らの声を彼岸へ残さねばならぬ"),
                (3.2, "澪", "そんな……蓮の声が、なくなるってこと？")]),
    dict(id="6-8", dur=5, size="蓮ナメ澪 / 50mm", move="FIX", desc="澪が一歩下がる。沈黙",
         lines=[(0.4, "澪", "それなら私は帰らない。あなたにそんなことをさせたくない")]),
    dict(id="6-9", dur=6, size="蓮のアップ / 50mm", move="ゆっくり寄り", desc="",
         lines=[(0.6, "蓮", "澪……それでも、もう一度一緒に生きたい"), (3.8, "蓮", "澪は、どうしたい？")]),
    dict(id="6-10", dur=5, size="2S 横 / 35mm", move="FIX",
         desc="涙を流しながら、澪が自分の意思で蓮の手を取る", lines=[(0.8, "澪", "……私も、生きたい")]),
]

def yaw_to(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0]) - math.pi / 2


STAND = dict(hipz=0, legL=0, legR=0, lean=0, head=0, armL=(0, 0.08), armR=(0, 0.08), elbowL=0.15, elbowR=0.15)


def build(tl):
    reset_scene(HIGAN_SKY)
    set_sun((0.3, -0.6, 0.75))
    coll = collection("SC6")
    world = higan(coll, seed=33)
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)
    mio = Actor("Mio", coll, MIO_C, height=0.92, hair=HAIR, skirt=True)
    crow = Crow("Crow", coll)
    for o in (ren.root, mio.root, crow.root):
        reflect(o, world["mirror"], coll)

    mio.key(1, loc=(0, 0, 0), yaw=0, head=-0.1, **{k: v for k, v in STAND.items() if k != "head"})
    s1, _ = tl.range("6-1")
    walk = ren.move(s1, F("6-2", 3.0), [(0.4, -16), (0.2, -3.2)], "walk")
    cams.static("6-1", (9, -24, 3.2), (0, -4, 1.0), 35)

    # 6-2: 水面の映り込みだけ
    cams.move("6-2", (2.3, -6.2, 0.35), (0.1, -1.8, -0.7), (2.2, -5.6, 0.35), (0.05, -1.2, -0.7), 28)
    ripple(coll, (0.2, -2.0, 0), F("6-2", 3.2), 2.0, 3.0)

    # 6-3: 振り返る
    mio.key(F("6-3", 0.2), yaw=0)
    mio.key(F("6-3", 1.0), yaw=math.pi, head=0)
    cams.static("6-3", (-0.6, -1.6, 1.45), (0, 0, 1.4), 50)

    # 6-4: 駆け寄って抱きしめる
    s4, _ = tl.range("6-4")
    ren.move(s4, F("6-4", 1.2), [(0.2, -3.2), (0.05, -0.55)], "run")
    hug = dict(armL=(1.25, -0.3), armR=(1.25, -0.3), elbowL=0.9, elbowR=0.9, lean=0.08)
    ren.key(F("6-4", 1.5), yaw=0, **hug)
    mio.key(F("6-4", 1.5), **hug, head=-0.15)
    cams.track("6-4", lambda f, k: (Vector((3.2 * math.sin(1.2 + k * 1.2), -0.3 - 3.2 * math.cos(1.2 + k * 1.2), 1.6)),
                                    Vector((0, -0.3, 1.35))), 28)
    cams.static("6-5", (1.0, -1.55, 1.65), (0, -0.02, 1.42), 50)
    mio.key(F("6-5", 0.6), head=0.3)

    # 6-6: カラス登場 → 二人が離れる
    s6, _ = tl.range("6-6")
    crow.key(1, loc=(8, 6, 6), scale=1.6)
    crow.fly(s6, F("6-6", 1.6), [(8, 6, 6), (4, 2, 2), (2.2, -0.3, 0)], scale=1.6)
    crow.key(F("6-6", 1.7), yaw=math.pi / 2, flap=-1.2)
    ripple(coll, (2.2, -0.3, 0), F("6-6", 1.6), 1.5, 2.0)
    ren.key(F("6-6", 1.4), **STAND)
    crow_p = (2.2, -0.3)
    ren.key(F("6-6", 1.9), loc=(-0.25, -0.9, 0), yaw=yaw_to((-0.25, -0.9), crow_p), armL=(0.3, 0.35))
    mio.key(F("6-6", 1.4), **STAND)
    mio.key(F("6-6", 1.9), loc=(-0.1, 0.1, 0), yaw=yaw_to((-0.1, 0.1), crow_p), armR=(0.3, 0.35))
    cams.static("6-6", (-4.0, -3.4, 1.3), (0.8, -0.3, 0.8), 28)

    # 6-7: 代償を告げる
    crow.key(F("6-7", 0.3), peck=0.25)
    crow.key(F("6-7", 1.5), peck=0.0)
    mio.key(F("6-7", 3.0), head=0.1, lean=0.08)
    cams.move("6-7", (3.4, -1.6, 0.4), (2.2, -0.3, 0.3), (3.0, -2.2, 1.0), (0, 0.1, 1.4), 50)

    # 6-8: 下がる澪
    mio.key(F("6-8", 0.3), lean=0, yaw=yaw_to((-0.1, 0.1), (-0.25, -0.9)))
    mio.key(F("6-8", 1.2), loc=(0.05, 0.6, 0), head=0.35, armR=(0, 0.08))
    ren.key(F("6-8", 0.5), yaw=yaw_to((-0.25, -0.9), (0.05, 0.6)), armL=(0, 0.08))
    cams.static("6-8", (-0.85, -1.6, 1.75), (0.05, 0.6, 1.35), 50)

    # 6-9: 蓮
    ren.key(F("6-9", 3.6), loc=(-0.15, -0.5, 0), lean=0.06, yaw=yaw_to((-0.15, -0.5), (0.05, 0.6)))
    cams.move("6-9", (0.6, 0.9, 1.6), (-0.2, -0.7, 1.55), (0.4, 0.5, 1.6), (-0.18, -0.6, 1.55), 50)

    # 6-10: 手を取る
    mio.key(F("6-10", 0.6), head=0.25, loc=(0.05, 0.3, 0))
    mio.key(F("6-10", 2.0), head=0.0, armR=(0.75, -0.15), elbowR=0.3, yaw=yaw_to((0.05, 0.3), (-0.15, -0.5)))
    ren.key(F("6-10", 2.2), armL=(0.65, -0.1), elbowL=0.3, yaw=yaw_to((-0.15, -0.5), (0.05, 0.3)))
    cams.static("6-10", (3.1, -0.2, 1.3), (0, -0.1, 1.1), 35)
