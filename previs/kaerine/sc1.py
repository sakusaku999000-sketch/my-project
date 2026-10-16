"""SCENE 1｜幸せな日常 (0:00〜0:35) 夕暮れの京都"""

import math
import random

from mathutils import Vector

from lib import (MB, Actor, Cams, collection, ease, frames, machiya, mat, reset_scene, set_sun, vlerp)

TITLE = "幸せな日常"
SHOTS = [
    dict(id="1-1", dur=5, size="大ロング / 24mm", move="クレーンダウン",
         desc="夕暮れの京都。瓦屋根の上から石畳の路地へ降りると、並んで歩く蓮と澪", lines=[]),
    dict(id="1-2", dur=6, size="2S ミディアム / 50mm", move="正面から後退追従",
         desc="他愛ない会話。澪が蓮の顔をのぞき込む",
         lines=[(1.5, "澪", "ねえ、ちゃんと聞いてる？"), (4.0, "蓮", "聞いてるよ")]),
    dict(id="1-3", dur=4, size="手元アップ / 85mm", move="FIX",
         desc="川沿いの手すり。蓮が指で手すりを二回たたく", lines=[], sfx=[(1.6, "tap"), (2.1, "tap")]),
    dict(id="1-4", dur=6, size="2S / 35mm", move="ゆっくり寄り",
         desc="川側から二人の正面。笑い合う",
         lines=[(0.5, "澪", "なにそれ（笑）"), (2.5, "蓮", "聞こえてるって合図")]),
    dict(id="1-5", dur=5, size="蓮ナメ澪 / 50mm", move="FIX",
         desc="別れ際。数歩先で澪が振り返り、手を振る",
         lines=[(1.2, "澪", "じゃあ、また明日ね！"), (3.3, "蓮", "うん、また明日")]),
    dict(id="1-6", dur=9, size="ロング / 35mm", move="ゆっくりプッシュイン",
         desc="蓮の背中越し。夕日の路地に澪の後ろ姿が小さくなって消えていく", lines=[]),
]

REN_C = (0.28, 0.33, 0.48)
MIO_C = (0.93, 0.86, 0.78)
HAIR = (0.16, 0.09, 0.06)
RAIL_X = 2.1


def build_set(coll):
    rng = random.Random(11)
    wall = mat("wall", (0.78, 0.62, 0.46))
    wall2 = mat("wall2", (0.7, 0.55, 0.42))
    wood = mat("wood", (0.27, 0.15, 0.08))
    roof = mat("roof", (0.2, 0.19, 0.21))
    stone = mat("stone", (0.55, 0.48, 0.42))
    lamp = mat("chochin", (1.0, 0.55, 0.2))
    water = mat("canal", (0.35, 0.38, 0.5))
    green = mat("tree", (0.25, 0.32, 0.16))

    mb = MB()
    mb.box((5, 120, 0.1), (0, 40, -0.05), stone)
    for i in range(60):  # 石畳の目地
        mb.box((4.6, 0.04, 0.02), (0, -10 + i * 2, 0.01), mat("joint", (0.42, 0.37, 0.33)))
    # 左側は町家が続く
    y = -12
    while y < 100:
        w = rng.uniform(5, 8)
        h = rng.uniform(4.5, 7)
        machiya(mb, (-2.5 - 3.5, y + w / 2), w - 0.3, 7, h, wall if rng.random() < 0.6 else wall2, roof, wood, facing=-1)
        mb.cyl(0.18, 0.4, (-2.7, y + w / 2, 3.1), lamp, seg=8)
        y += w
    # 右側: 前半は町家、20〜34m は川沿いの手すり、その先また町家
    y = -12
    while y < 100:
        w = rng.uniform(5, 8)
        if 16 < y + w and y < 36:
            y += w
            continue
        h = rng.uniform(4.5, 7)
        machiya(mb, (2.5 + 3.5, y + w / 2), w - 0.3, 7, h, wall2, roof, wood, facing=1)
        y += w
    mb.box((30, 22, 0.1), (RAIL_X + 15, 27, -1.2), water)  # 川
    mb.box((0.15, 16, 1.2), (RAIL_X + 0.1, 27, -0.55), stone)  # 護岸
    for yy in range(19, 36, 2):
        mb.box((0.1, 0.1, 0.95), (RAIL_X, yy, 0.47), wood)
    mb.box((0.12, 16, 0.08), (RAIL_X, 27, 0.95), wood)  # 手すり
    for yy in (21, 29, 33):  # 柳
        mb.cyl(0.15, 4, (RAIL_X + 1.2, yy, 1.3), wood)
        mb.sphere(1.6, (RAIL_X + 1.2, yy, 3.6), green, scale=(1, 1, 1.4))
    mb.box((300, 1, 300), (0, 230, 0), mat("sky_far", (1.0, 0.62, 0.32)))  # 夕空の背景
    mb.sphere(8, (6, 225, 18), mat("sun", (1.0, 0.9, 0.6)))
    return mb.obj("Kyoto", coll)


def build(tl):
    reset_scene((1.0, 0.68, 0.42))
    set_sun((0.2, 0.9, 0.35))
    coll = collection("SC1")
    build_set(coll)
    ren = Actor("Ren", coll, REN_C)
    mio = Actor("Mio", coll, MIO_C, height=0.92, hair=HAIR, skirt=True)
    cams = Cams(tl, coll)
    F = tl.f

    # --- 1-1〜1-2: 並んで歩く
    s, _ = tl.range("1-1")
    e = F("1-3", 0.6)
    ren_path = ren.move(s, e, [(0.55, 9), (0.75, 23.6)], "walk")
    mio_path = mio.move(s, e, [(-0.15, 9), (0.15, 23.9)], "walk",
                        extra=lambda f: dict(head=-0.1, armR=(0.4, 0.4)) if F("1-2", 1.2) < f < F("1-2", 3) else {})
    cams.track("1-1", lambda f, k: (vlerp((0.2, 2, 11), (0.4, 4.5, 1.8), ease(k)), ren_path(f) + Vector((-0.3, 3, 1.0 + 0.5 * (1 - k)))), 24)
    cams.track("1-2", lambda f, k: (ren_path(f) + Vector((-0.4, 3.6, 1.55)), ren_path(f) + Vector((-0.35, 0, 1.45))), 50)

    # --- 1-3: 手すりをトン、トン
    f0 = F("1-3", 0.7)
    ren.key(f0, loc=(1.5, 24), yaw=-math.pi / 2, armR=(0.3, 0.1))
    mio.key(f0, loc=(1.35, 24.9), yaw=-math.pi / 2)
    ren.key(F("1-3", 1.2), armR=(0.95, 0.15))
    for t in (1.6, 2.1):
        ren.key(F("1-3", t - 0.12), armR=(0.82, 0.15))
        ren.key(F("1-3", t), armR=(0.95, 0.15))
    cams.move("1-3", (3.1, 23.2, 1.2), (2.0, 24.0, 1.0), (3.0, 23.3, 1.17), (2.0, 24.0, 1.0), 50)

    # --- 1-4: 笑い合う (川側から)
    a = F("1-4", 0.4)
    mio.key(a, yaw=mio.face((1.5, 24)) * 0.5 + (-math.pi / 2) * 0.5, head=-0.1)
    for i, t in enumerate((0.6, 1.0, 1.4, 1.8)):
        mio.key(F("1-4", t), lean=-0.12 if i % 2 else -0.04, head=-0.25 if i % 2 else -0.1)
    ren.key(F("1-4", 2.3), armR=(0, 0.1), yaw=ren.face((1.35, 24.9)), head=0.1)
    ren.key(F("1-4", 3.3), lean=0.05)
    mio.key(F("1-4", 4.0), lean=0.0, head=0.0)
    cams.move("1-4", (5.4, 24.45, 1.9), (1.45, 24.45, 1.45), (4.5, 24.45, 1.85), (1.45, 24.45, 1.45), 35)

    # --- 1-5: 別れ際に振り返る
    a, b = F("1-5", 0.0), F("1-5", 1.0)
    mio.move(a, b, [(1.35, 24.9), (0.6, 27.5)], "walk")
    mio.key(F("1-5", 1.3), yaw=math.pi, armR=(0.4, 2.3), head=0)
    mio.key(F("1-5", 1.6), armR=(0.4, 2.7))
    mio.key(F("1-5", 1.9), armR=(0.4, 2.2))
    mio.key(F("1-5", 2.2), armR=(0.4, 2.7))
    mio.key(F("1-5", 2.8), armR=(0, 0.08))
    ren.key(F("1-5", 3.2), armR=(0.5, 1.2), yaw=ren.face((0.6, 27.5)))
    ren.key(F("1-5", 4.2), armR=(0, 0.08))
    cams.static("1-5", (0.85, 22.3, 1.75), (0.75, 27.5, 1.3), 50)

    # --- 1-6: 去っていく後ろ姿
    a, _ = tl.range("1-6")
    mio.move(a, F("1-6", 8.5), [(0.6, 27.5), (0.2, 31), (0.0, 42)], "walk")
    cams.move("1-6", (0.5, 19.0, 1.6), (0.3, 34, 1.2), (0.6, 20.8, 1.55), (0.2, 36, 1.2), 35)
