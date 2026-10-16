"""SCENE 5｜死者の都 (2:30〜3:20) 水鏡の世界"""

import math

from mathutils import Vector

from lib import (Actor, Cams, Crow, butterflies, collection, ease, frames, reflect, reset_scene, ripple, set_sun,
                 vlerp)
from sc1 import REN_C
from sets import HIGAN_SKY, higan, stepping_tiles

TITLE = "死者の都"
SHOTS = [
    dict(id="5-1", dur=7, size="蓮の頭越し→大ロング / 24mm", move="クレーンアップ＋後退",
         desc="鏡のような無限の水面。頭上に逆さまの町並みと神殿、無数の灯籠。月を背にした巨大な鳥居", lines=[]),
    dict(id="5-2", dur=5, size="ローアングル / 24mm", move="FIX",
         desc="圧倒的な景色に立ち尽くす蓮", lines=[]),
    dict(id="5-3", dur=5, size="蓮ナメ / 35mm", move="FIX",
         desc="金色の目のカラスが舞い降り、水面に波紋", lines=[]),
    dict(id="5-4", dur=6, size="2S ロー / 35mm", move="FIX",
         desc="カラスが初めて人の声で話す",
         lines=[(0.5, "返り烏", "ここは彼岸。死者の記憶が眠る場所"), (3.6, "蓮", "澪はどこにいる!?")]),
    dict(id="5-5", dur=5, size="カラスのアップ / 50mm", move="FIX", desc="",
         lines=[(0.3, "返り烏", "声をたどれ。ただし、お前の求める声だけが響くとは限らぬ")]),
    dict(id="5-6", dur=7, size="ミディアム / 28mm", move="蓮の周りを回り込む",
         desc="四方八方から澪に似た声。浮遊する建築がゆっくり入れ替わる",
         lines=[(0.8, "声", "……蓮……"), (2.6, "声", "……れん……"), (4.4, "声", "……こっち……")], sfx=[(0.5, "voices")]),
    dict(id="5-7", dur=5, size="ロング / 28mm", move="横移動",
         desc="声を追うと水面に道が生まれる。間違った声──道が消え、暗い水へ沈みかける。触れた灯籠が蝶になって散る",
         lines=[]),
    dict(id="5-8", dur=5, size="顔アップ ロー / 50mm", move="FIX",
         desc="遠くから、二回の小さな音。顔を上げる蓮", lines=[(3.5, "蓮", "……澪！")],
         sfx=[(2.0, "tap"), (2.5, "tap")]),
    dict(id="5-9", dur=5, size="俯瞰ロング / 24mm", move="並走して上昇",
         desc="その音を頼りに、新しく生まれる道を走って迷宮を突破する", lines=[]),
]


def build(tl):
    reset_scene(HIGAN_SKY)
    set_sun((0.2, -0.5, 0.85))
    coll = collection("SC5")
    world = higan(coll)
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)
    crow = Crow("Crow", coll)
    reflect(ren.root, world["mirror"], coll)
    reflect(crow.root, world["mirror"], coll)

    # 5-1〜5-2: 立ち尽くす
    ren.key(1, loc=(0, 0, 0), yaw=0, head=-0.25)
    ren.key(F("5-1", 6.0), head=-0.4, lean=-0.08)
    cams.track("5-1", lambda f, k: (vlerp((0.1, -0.7, 1.75), (2, -16, 10), ease(k)),
                                    vlerp((0, 10, 2.5), (0, 60, 14), ease(k))), 24)
    ren.key(F("5-2", 0.5), yaw=0.0)
    ren.key(F("5-2", 4.5), yaw=0.5)
    cams.static("5-2", (1.3, 2.2, 0.35), (0, 0, 1.4), 24)

    # 5-3: カラスが舞い降りる
    land = Vector((0, 3.2, 0))
    crow.key(1, loc=(6, 15, 9), scale=1.6)
    crow.fly(F("5-3", 0.3), F("5-3", 3.0), [(6, 15, 9), (3, 8, 4), (1, 4.5, 1.2), land], scale=1.6)
    crow.key(F("5-3", 3.1), yaw=math.pi, flap=-1.2)
    ripple(coll, land, F("5-3", 3.0), 1.6, 2.5)
    ren.key(F("5-3", 2.5), yaw=0.15, head=0.1, lean=0)
    cams.static("5-3", (1.5, -2.8, 1.8), (0, 2.6, 0.5), 35)

    # 5-4〜5-5: 会話
    crow.key(F("5-4", 0.5), peck=0.2)
    crow.key(F("5-4", 1.0), peck=0.0)
    ren.key(F("5-4", 3.4), lean=0.15, armL=(0.4, 0.3), armR=(0.4, 0.3))
    ren.key(F("5-4", 4.4), lean=0.05, armL=(0, 0.08), armR=(0, 0.08))
    cams.static("5-4", (4.2, 1.0, 0.45), (0, 1.6, 0.8), 28)
    crow.key(F("5-5", 0.3), peck=0.15)
    crow.key(F("5-5", 1.2), peck=-0.1)
    crow.key(F("5-5", 2.5), peck=0.1)
    cams.static("5-5", (0.35, 2.15, 0.32), (0, 3.2, 0.3), 50)

    # 5-6: 四方から声。回り込み
    crow.fly(F("5-6", 0.2), F("5-6", 2.0), [land, (2, 6, 4), (5, 14, 10)], scale=1.6)
    for i, t in enumerate((0.8, 2.6, 4.4, 6.2)):
        ren.key(F("5-6", t), yaw=[0.9, -1.2, 2.4, 1.4][i], head=-0.05)
    cams.track("5-6", lambda f, k: (Vector((3.6 * math.sin(k * 5.6), -3.6 * math.cos(k * 5.6), 1.5)),
                                    Vector((0, 0, 1.3))), 28)

    # 5-7: 声を追う → 道が沈む → 灯籠の蝶
    s7, e7 = tl.range("5-7")
    path = [(1 + i * 1.2, 0.3 * i, 0) for i in range(7)]
    stepping_tiles(coll, path, s7, every=4, f_sink=F("5-7", 2.4), name="WrongTile")
    ren.move(s7, F("5-7", 2.6), [(0, 0), (6.5, 1.8)], "run")
    ren.key(F("5-7", 3.0), loc=(6.6, 1.9, -0.25), hipz=-0.55, legL=1.4, legR=1.4, lean=0.5, head=0.4,
            armL=(1.2, 0.2), armR=(1.2, 0.2))
    butterflies(coll, (7.6, 2.8, 1.2), F("5-7", 3.2), n=40, dur=1.8, spread=5)
    cams.track("5-7", lambda f, k: (vlerp((1, -8, 2.5), (5, -6.5, 2.2), ease(k)), vlerp((2, 1, 0.8), (6.5, 2, 0.6), k)),
               28)

    # 5-8: トン、トン
    ren.key(F("5-8", 0.0), loc=(6.6, 1.9, 0), head=0.5)
    ren.key(F("5-8", 2.2), head=0.2)
    ren.key(F("5-8", 3.0), head=-0.15, yaw=-0.25)
    for t in (2.0, 2.5):
        ripple(coll, (4, 22, 0), F("5-8", t), 2.5, 18, width=0.25)
    cams.static("5-8", (8.1, 1.5, 0.75), (6.75, 1.9, 1.05), 50)

    # 5-9: 新しい道を走る
    s9, e9 = tl.range("5-9")
    good = [(6.6 - i * 0.15, 3 + i * 1.6, 0) for i in range(16)]
    stepping_tiles(coll, good, s9 - 6, every=3, color=(1.0, 0.9, 0.6), name="GoodTile")
    ren.key(s9, hipz=0, legL=0, legR=0, lean=0, head=0, armL=(0, 0.08), armR=(0, 0.08))
    run = ren.move(s9 + 2, e9, [(6.6, 1.9), (4.4, 26)], "sprint")
    cams.track("5-9", lambda f, k: (run(f) + Vector((7 + 3 * k, -6, 3 + 8 * ease(k))), run(f) + Vector((0, 4, 0))), 24)
