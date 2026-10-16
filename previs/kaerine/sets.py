"""複数シーンで使うセット"""

import math
import random

from lib import MB, mat, torii


def room(coll, altar=False, night=(0.06, 0.08, 0.16)):
    """蓮の部屋 (6 x 5 m)。左壁 (x=-3) に窓。altar=True で遺影と白い花"""
    wall = mat("room_wall", (0.62, 0.6, 0.58))
    floor = mat("room_floor", (0.45, 0.36, 0.27))
    wood = mat("room_wood", (0.32, 0.22, 0.15))
    cloth = mat("room_cloth", (0.38, 0.4, 0.45))
    mb = MB()
    mb.box((6, 5, 0.1), (0, 0, -0.05), floor)
    mb.box((6, 5, 0.1), (0, 0, 2.55), wall)
    mb.box((6, 0.1, 2.6), (0, 2.5, 1.3), wall)  # 奥
    mb.box((0.1, 5, 2.6), (3, 0, 1.3), wall)  # 右
    # 左壁 (窓: y -0.2〜1.4 / z 0.9〜2.0)
    mb.box((0.1, 2.3, 2.6), (-3, -1.35, 1.3), wall)
    mb.box((0.1, 1.1, 2.6), (-3, 1.95, 1.3), wall)
    mb.box((0.1, 1.6, 0.9), (-3, 0.6, 0.45), wall)
    mb.box((0.1, 1.6, 0.6), (-3, 0.6, 2.3), wall)
    mb.box((0.35, 1.7, 0.06), (-2.9, 0.6, 0.88), wood)  # 窓台
    mb.box((0.05, 0.05, 1.1), (-3, 0.6, 1.45), wood)  # 窓枠
    mb.box((0.1, 40, 30), (-25, 0, 5), mat("night", night))  # 夜空
    for i in range(14):  # 外の街明かり
        rng = random.Random(i)
        mb.box((0.1, 0.4, 0.4), (-20, rng.uniform(-8, 8), rng.uniform(0, 3)), mat("citylight", (0.9, 0.75, 0.4)))
    mb.box((1.2, 0.7, 0.05), (0, 0.3, 0.38), wood)  # 座卓
    for x in (-0.5, 0.5):
        for y in (0.0, 0.6):
            mb.box((0.06, 0.06, 0.36), (x, y, 0.18), wood)
    mb.box((2.0, 1.0, 0.45), (2.2, 1.6, 0.22), cloth)  # ベッド
    mb.box((0.6, 0.45, 0.6), (-2.5, 2.1, 0.3), wood)  # 棚
    if altar:
        white = mat("flower", (0.97, 0.97, 0.95))
        mb.box((1.4, 0.5, 0.75), (0.6, 2.2, 0.37), wood)  # 祭壇台
        mb.box((0.36, 0.04, 0.46), (0.6, 2.25, 1.0), mat("frame", (0.1, 0.1, 0.1)))  # 遺影
        mb.box((0.28, 0.03, 0.36), (0.6, 2.22, 1.0), mat("photo", (0.85, 0.75, 0.68)))
        for x in (0.1, 1.1):
            mb.cyl(0.07, 0.3, (x, 2.2, 0.9), mat("vase", (0.3, 0.3, 0.35)))
            for k in range(5):
                a = k * 1.25
                mb.sphere(0.06, (x + 0.08 * math.cos(a), 2.2 + 0.08 * math.sin(a), 1.1 + 0.05 * (k % 2)), white)
        for x in (0.45, 0.75):  # 湯のみ二つ
            mb.cyl(0.035, 0.08, (x, 2.0, 0.79), mat("cup", (0.85, 0.83, 0.78)), seg=8)
    return mb.obj("Room", coll)


def shrine_night(coll, origin=(0, 0, 0), day=False):
    """神社の奥 (参道 +Y 方向)。day=True で朝の色"""
    ox, oy, _ = origin
    stone = mat("sando", (0.62, 0.6, 0.56) if day else (0.32, 0.32, 0.36))
    tree = mat("cedar_n", (0.22, 0.3, 0.18) if day else (0.06, 0.09, 0.08))
    mb = MB()
    mb.box((40, 80, 0.1), (ox, oy + 30, -0.05), mat("ground_n", (0.45, 0.42, 0.33) if day else (0.13, 0.14, 0.16)))
    mb.box((2.4, 80, 0.06), (ox, oy + 30, 0.0), stone)
    rng = random.Random(5)
    for i in range(70):
        side = 1 if i % 2 else -1
        x = ox + side * rng.uniform(3, 14)
        y = oy + rng.uniform(-5, 70)
        h = rng.uniform(10, 18)
        mb.cyl(rng.uniform(0.25, 0.4), h, (x, y, h / 2), tree, seg=8)
    for y in (2, 8):  # 石灯籠
        for x in (-1.8, 1.8):
            mb.box((0.3, 0.3, 1.0), (ox + x, oy + y, 0.5), stone)
            mb.box((0.5, 0.5, 0.3), (ox + x, oy + y, 1.15), mat("toro_light", (0.9, 0.7, 0.35)))
            mb.box((0.65, 0.65, 0.12), (ox + x, oy + y, 1.36), stone)
    torii(mb, (ox, oy + 12, 0), 0, scale=1.6)
    return mb.obj("ShrineNight", coll)


# ---------------------------------------------------------------- 彼岸 (水鏡の世界)
from lib import FPS, empty, key_tr, lanterns, mirror_root, pagoda, reflect, reflect_static, temple, visible  # noqa: E402

HIGAN_SKY = (0.04, 0.06, 0.16)


def higan(coll, center=(0, 0), seed=21, gate=True, n_buildings=26):
    """水鏡・逆さまの浮遊建築・灯籠・遠くの大鳥居と月。

    水面そのものは描かず、z=0 で上下反転した複製を置いて映り込みに見せる。
    戻り値: dict(mirror=反転親, static=[静的オブジェクト])
    """
    cx, cy = center
    rng = random.Random(seed)
    wall = mat("hg_wall", (0.55, 0.5, 0.62))
    roof = mat("hg_roof", (0.15, 0.13, 0.22))
    red = mat("hg_red", (0.65, 0.12, 0.12))
    line = mat("hg_line", (0.35, 0.45, 0.75))
    static = []

    mb = MB()
    for i in range(-30, 31):  # 水面の目安になる細い線
        mb.box((0.03, 600, 0.005), (cx + i * 8, cy + 150, 0.0), line)
    static.append(mb.obj("WaterLines", coll))

    mb = MB()
    for i in range(n_buildings):  # 逆さまに浮かぶ建築
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(25, 140)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) + 40
        z = rng.uniform(18, 60)
        if rng.random() < 0.5:
            pagoda(mb, (x, y, z), rng.randint(3, 5), rng.uniform(3, 6), wall, roof, flip=True)
        else:
            temple(mb, (x, y, z), rng.uniform(6, 14), rng.uniform(5, 10), rng.uniform(3, 6), wall, roof,
                   rot=(0, 0, rng.uniform(0, 3)), flip=True)
    static.append(mb.obj("FloatingCity", coll))
    static.append(lanterns(coll, 260, ((cx - 60, cx + 60), (cy - 20, cy + 120)), (1.5, 30), seed=seed))
    static.append(lanterns(coll, 80, ((cx - 15, cx + 15), (cy - 10, cy + 40)), (0.4, 3), seed=seed + 1, size=0.2,
                           name="LanternsLow"))
    # 青い彼岸花の群生
    mb = MB()
    blue = mat("lily_blue", (0.25, 0.5, 1.0))
    for _ in range(40):
        px, py = cx + rng.uniform(-40, 40), cy + rng.uniform(-10, 100)
        if abs(px - cx) < 4:
            continue
        for _ in range(rng.randint(5, 12)):
            mb.sphere(0.08, (px + rng.uniform(-1, 1), py + rng.uniform(-1, 1), rng.uniform(0.2, 0.45)), blue)
    static.append(mb.obj("BlueLilies", coll))
    if gate:
        mb = MB()
        torii(mb, (cx, cy + 260, 0), 0, scale=14, red=(0.6, 0.12, 0.1))
        static.append(mb.obj("GiantTorii", coll))
    moon = MB().cyl(30, 1, (cx, cy + 420, 70), mat("moon", (0.95, 0.93, 0.85)), rot=(math.pi / 2, 0, 0), seg=40) \
        .obj("Moon", coll)
    # 水平線より下を水の色にするための大きな器 (映り込みはこれより手前に描かれる)
    MB().cyl(4500, 10, (cx, cy, -125), mat("water_far", (0.09, 0.15, 0.3)), seg=64).obj("WaterFar", coll)
    mirror = mirror_root(coll)
    reflect_static(static, mirror)
    return dict(mirror=mirror, static=static, wall=wall, roof=roof, red=red)


def stepping_tiles(coll, pts, f_on, every=3, f_sink=None, color=(0.75, 0.85, 1.0), size=1.1, name="Tile"):
    """足元に現れる飛び石。pts[i] が f_on + i*every で現れ、f_sink 以降に沈む"""
    m = mat(name, color)
    objs = []
    for i, p in enumerate(pts):
        o = MB().box((size, size, 0.08), (0, 0, -0.04), m).obj(f"{name}{i}", coll, loc=(p[0], p[1], 0))
        f = f_on + i * every
        key_tr(o, 1, scale=0.001)
        key_tr(o, f, scale=0.001)
        key_tr(o, f + 4, scale=1.0)
        if f_sink is not None:
            fs = f_sink + i * 1
            key_tr(o, fs, loc=(p[0], p[1], 0))
            key_tr(o, fs + 20, loc=(p[0], p[1], -3), scale=0.3)
        objs.append(o)
    return objs
