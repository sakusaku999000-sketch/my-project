"""SCENE 4｜彼岸への疾走 (1:55〜2:30) 千本鳥居"""

import math
import random

from mathutils import Euler, Vector

from lib import (MB, Actor, Cams, collection, ease, frames, key_tr, lerp, mat, reset_scene, set_sun, shake, torii,
                 visible, vlerp)
from sc1 import REN_C

TITLE = "彼岸への疾走"
SHOTS = [
    dict(id="4-1", dur=4, size="背中 / 24mm", move="ローポジションで追従",
         desc="緩やかな上り坂の千本鳥居を全力で駆け上がる蓮。朱色が濃い", lines=[]),
    dict(id="4-2", dur=5, size="真横 / 85mm", move="横移動で並走",
         desc="鳥居の外から並走。手前を赤い彼岸花のボケが流れる", lines=[]),
    dict(id="4-3", dur=5, size="正面 / 16mm", move="後退しながら追従",
         desc="背後の鳥居がねじれ始める。石畳に水が広がる。彼岸花が白く変わる", lines=[]),
    dict(id="4-4", dur=5, size="主観 / 24→16mm", move="前進・加速",
         desc="ねじれた鳥居のトンネル。足元は水面", lines=[]),
    dict(id="4-5", dur=5, size="俯瞰 / 24mm", move="急上昇",
         desc="緩やかな坂を上っていく、ねじれた鳥居の列を見下ろす。坂の上に神社の境内が見える。彼岸花は青に", lines=[]),
    dict(id="4-6", dur=5, size="ロング / 24mm", move="FIX→わずかに寄り",
         desc="鳥居のトンネルを抜けると神社の境内。目の前の大鳥居が崩れ落ち、拝殿の前に巨大な光の門が開く", lines=[],
         sfx=[(2.2, "crash")]),
    dict(id="4-7", dur=6, size="背中 / 24mm", move="追従→光へ",
         desc="境内を駆け抜け、蓮が光へ飛び込む。音が消え、視界が真っ白に開ける", lines=[], fade="white"),
]

AMP, WAVE = 2.5, 80.0
U0, U1, SPACING = 4.0, 156.0, 1.5  # 鳥居は U0〜U1。U1 から先は神社の境内
GRADE = 0.05  # 参道の勾配 (緩やかな上り坂: 100m で 5m 上る)
KEIDAI = 12.0  # 鳥居を抜けてから境内の大鳥居までの距離
GATE_U = U1 + 27.0  # 光の門 (拝殿の前)


def H(u):
    """参道の高さ。U1 から先 (境内) は平ら"""
    return GRADE * max(0.0, min(u, U1))


def _curve(u):
    return Vector((AMP * math.sin(2 * math.pi * u / WAVE), u, 0.0))


def _curve_t(u):
    d = AMP * 2 * math.pi / WAVE * math.cos(2 * math.pi * u / WAVE)
    return Vector((d, 1, 0)).normalized()


def P(u, z=0.0):
    if u <= U1:
        p = _curve(u)
    else:
        p = _curve(U1) + _curve_t(U1) * (u - U1)
    return p + Vector((0, 0, H(u) + z))


def T(u):
    return _curve_t(min(u, U1))


def N(u):
    t = T(u)
    return Vector((t.y, -t.x, 0))


def yaw_at(u):
    t = T(u)
    return math.atan2(t.y, t.x) - math.pi / 2


def twist(u):
    k = max(0.0, (u - 55) / 90)
    return 0.55 * k * math.sin((u - 55) / 9)


def mix(a, b, k):
    return tuple(lerp(x, y, k) for x, y in zip(a, b))


RED, WHITE, BLUE = (0.82, 0.1, 0.03), (0.95, 0.95, 0.93), (0.25, 0.5, 1.0)


def phase_color(u, a=60, b=110):
    if u < a:
        return RED
    if u < b:
        return mix(RED, WHITE, ease((u - a) / 25))
    return mix(WHITE, BLUE, ease((u - b) / 25))


def precinct(coll, tl):
    """鳥居を抜けた先の神社の境内 (ローカル座標: x=横, y=奥。原点は鳥居の出口)"""
    gravel = mat("gravel", (0.66, 0.63, 0.57))
    stone = mat("keidai_stone", (0.55, 0.54, 0.52))
    wood = mat("keidai_wood", (0.62, 0.2, 0.1))
    white = mat("keidai_white", (0.9, 0.88, 0.82))
    roof = mat("keidai_roof", (0.16, 0.18, 0.2))
    green = mat("keidai_tree", (0.14, 0.22, 0.13))
    bark = mat("keidai_bark", (0.3, 0.2, 0.12))
    rope = mat("shimenawa", (0.85, 0.78, 0.55))
    mb = MB()
    mb.box((70, 75, 0.3), (0, 33, -0.15), gravel)
    mb.box((3.2, 32, 0.06), (0, 16, 0.03), stone)  # 参道の石畳
    for x in (-1, 1):
        # 狛犬
        mb.box((0.9, 0.9, 1.0), (2.4 * x, 7, 0.5), stone)
        mb.sphere(0.4, (2.4 * x, 7.05, 1.35), stone, scale=(0.9, 1.2, 1.0))
        mb.sphere(0.28, (2.4 * x, 7.35, 1.85), stone)
        # 石灯籠
        for y in (15, 21):
            mb.box((0.35, 0.35, 1.3), (2.6 * x, y, 0.65), stone)
            mb.box((0.6, 0.6, 0.4), (2.6 * x, y, 1.5), mat("keidai_lamp", (0.95, 0.75, 0.4)))
            mb.box((0.85, 0.85, 0.15), (2.6 * x, y, 1.78), stone)
    # 拝殿
    mb.box((15, 10, 1.0), (0, 34, 0.5), stone)
    mb.box((4.5, 2.4, 0.5), (0, 28.0, 0.25), stone)  # 階段
    for x in (-5.5, -2, 2, 5.5):
        mb.cyl(0.25, 4.2, (x, 30.2, 3.1), wood)
    mb.box((13, 7.5, 4.2), (0, 34.5, 3.1), white)
    mb.box((17, 12, 0.6), (0, 34.2, 5.5), roof)
    mb.box((13, 8.5, 1.4), (0, 34.2, 6.4), roof)
    mb.box((14, 1.0, 0.8), (0, 34.2, 7.4), roof)
    mb.cyl(0.18, 9, (0, 30.0, 4.6), rope, rot=(0, math.pi / 2, 0), seg=8)  # しめ縄
    mb.box((1.6, 0.8, 0.8), (0, 30.4, 1.4), mat("saisen", (0.35, 0.22, 0.12)))  # 賽銭箱
    # 本殿
    mb.box((9, 7, 1.0), (0, 48, 0.5), stone)
    mb.box((7, 5, 3.5), (0, 48, 2.75), white)
    mb.box((10, 8, 0.5), (0, 48, 4.7), roof)
    mb.box((6, 5, 1.3), (0, 48, 5.5), roof)
    # 手水舎
    for x in (-10.5, -7.5):
        for y in (11, 14):
            mb.cyl(0.15, 2.6, (x, y, 1.3), wood)
    mb.box((4.5, 4.5, 0.4), (-9, 12.5, 2.8), roof)
    mb.box((1.8, 1.0, 0.7), (-9, 12.5, 0.35), stone)
    # 御神木
    mb.cyl(1.2, 26, (10, 21, 13), bark, seg=12)
    mb.torus(1.25, 0.15, (10, 21, 3.2), rope)
    mb.sphere(7, (10, 21, 24), green, scale=(1, 1, 1.4))
    # 玉垣と周りの杉
    mb.box((60, 0.3, 0.9), (0, 60, 0.45), stone)  # 玉垣
    rng = random.Random(12)
    for _ in range(70):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(26, 40)
        x, y = r * math.cos(a), 30 + r * math.sin(a)
        if y < 3:
            continue
        h = rng.uniform(14, 22)
        mb.cyl(rng.uniform(0.3, 0.5), h, (x, y, h / 2), mat("cedar4", (0.1, 0.14, 0.1)), seg=7)
    ob = mb.obj("Keidai", coll, loc=P(U1))
    ob.rotation_euler = (0, 0, yaw_at(U1))

    # 境内の大鳥居 (崩れ落ちる)
    tm = MB()
    torii(tm, (0, 0, 0), 0, scale=2.4, red=(0.8, 0.12, 0.05))
    big = tm.obj("KeidaiTorii", coll, loc=P(U1 + KEIDAI))
    big.rotation_euler = (0, 0, yaw_at(U1))
    loc0, rot0 = big.location.copy(), big.rotation_euler.copy()
    key_tr(big, 1, loc=loc0, rot=rot0)
    key_tr(big, tl.f("4-6", 2.0), loc=loc0, rot=rot0)
    key_tr(big, tl.f("4-6", 3.2), loc=loc0 + N(U1) * 1.5 + Vector((0, 0, -0.4)),
           rot=(rot0.x + 0.15, 1.45, rot0.z + 0.1))  # 横倒しに崩れ、参道は空く
    return big


def build_set(coll, tl):
    rng = random.Random(4)
    mb = MB()
    stone = mat("stone4", (0.45, 0.43, 0.4))
    water = mat("water4", (0.35, 0.45, 0.62))
    slope = math.atan(GRADE)
    for y0 in range(-20, int(U1), 10):  # 緩やかな上り坂の地面
        yc = y0 + 5
        mb.box((90, 10.3, 0.2), (0, yc, H(yc) - 0.12), mat("ground4", (0.2, 0.2, 0.2)), rot=(slope, 0, 0))
    for u in range(0, int(U1) + 2, 2):
        tt = T(u + 1)
        m = stone if u < 70 else water
        mb.box((1.7 if u < 70 else 8, 2.05, 0.05), P(u + 1), m,
               rot=(slope, 0, math.atan2(tt.y, tt.x) - math.pi / 2))
    # 杉林 (坂の両側)
    for _ in range(130):
        u = rng.uniform(-10, U1 - 2)
        side = rng.choice((-1, 1))
        lat = side * rng.uniform(4, 16) if side < 0 else rng.uniform(10, 18)
        h = rng.uniform(12, 20)
        mb.cyl(rng.uniform(0.2, 0.35), h, P(u) + N(u) * lat + Vector((0, 0, h / 2 - 0.3)),
               mat("cedar4", (0.1, 0.14, 0.1)), seg=7)
    # 彼岸花 (赤 → 白 → 青)
    u = 1.0
    while u < U1 - 1:
        for side, dens in ((1, 3), (-1, 1)):
            for _ in range(dens):
                lat = side * rng.uniform(1.4, 4.0)
                h = rng.uniform(0.35, 0.6)
                b = P(u) + N(u) * lat
                mb.cyl(0.008, h, b + Vector((0, 0, h / 2)), mat("stem4", (0.15, 0.3, 0.1)), seg=4)
                mb.sphere(rng.uniform(0.06, 0.09), b + Vector((0, 0, h)), mat("lily", phase_color(u)))
        u += rng.uniform(0.4, 0.8)
    mb.obj("Sando4", coll)

    # 鳥居: 坂を上るほど白く褪せ、ねじれる
    i = 0
    u = U0
    while u < U1:
        c = phase_color(u, 70, 130)
        tm = MB()
        torii(tm, (0, 0, 0), 0, red=c, roll=twist(u))
        ob = tm.obj(f"Torii4_{i:03d}", coll, loc=P(u))
        ob.rotation_euler = (0, 0, yaw_at(u))
        u += SPACING
        i += 1
    precinct(coll, tl)
    # 光の門 (拝殿の前)
    gate = MB().torus(4.0, 0.35, (0, 0, 0), mat("gate_ring", (1.0, 0.92, 0.65)), rot=(math.pi / 2, 0, 0), seg=48) \
        .cyl(3.7, 0.05, (0, 0, 0), mat("gate_light", (1, 1, 1)), rot=(math.pi / 2, 0, 0), seg=48) \
        .obj("LightGate", coll, loc=P(GATE_U, 4.3))
    gate.rotation_euler = (0, 0, yaw_at(GATE_U))
    key_tr(gate, 1, scale=0.001)
    key_tr(gate, tl.f("4-6", 3.0), scale=0.001)
    key_tr(gate, tl.f("4-6", 4.6), scale=1.0)
    key_tr(gate, tl.f("4-7", 6.0), scale=1.4)
    return gate


def build(tl):
    reset_scene((0.55, 0.42, 0.45))
    set_sun((0.5, -0.4, 0.75))
    coll = collection("SC4")
    build_set(coll, tl)
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)

    def path_pts(u0, u1, n=40):
        return [P(lerp(u0, u1, i / n)) for i in range(n + 1)]

    s, _ = tl.range("4-1")
    e = tl.range("4-5")[1]
    run = ren.move(s, e, path_pts(0, 146), "sprint")

    def u_of(f):
        return run(f).y

    cams.track("4-1", lambda f, k: (run(f) - T(u_of(f)) * (4 - 1.2 * ease(k)) + Vector((0, 0, 0.5)),
                                    run(f) + T(u_of(f)) * 3 + Vector((0, 0, 1.3))), 24)
    cams.track("4-2", lambda f, k: (run(f) + N(u_of(f)) * 9 + Vector((0, 0, 0.9)), run(f) + Vector((0, 0, 1.0))), 85)
    cams.track("4-3", lambda f, k: (run(f) + T(u_of(f)) * 2.3 + Vector((0, 0, 1.35)), run(f) + Vector((0, 0, 1.45)),
                                    16, twist(u_of(f)) * 0.5), 16)
    cams.track("4-4", lambda f, k: (run(f) + T(u_of(f)) * 0.9 + Vector((0, 0, 1.65 + 0.04 * math.sin(f))),
                                    P(u_of(f) + 25, 1.5), lerp(24, 16, ease(k)), twist(u_of(f) + 5)), 24)
    cams.track("4-5", lambda f, k: (run(f) - T(u_of(f)) * (3 - ease(k)) + Vector((0, 0, 3.8 + 15 * ease(k))),
                                    P(u_of(f) + 6 + 14 * ease(k))), 24)

    # 4-6: トンネルを抜けて境内へ → 大鳥居が崩れる → 光の門
    s6, e6 = tl.range("4-6")
    ren.move(s6, F("4-6", 1.8), path_pts(146, U1 + 6, 10), "run")
    ren.key(F("4-6", 2.3), lean=-0.15, armL=(0.6, 0.4), armR=(0.6, 0.4), head=-0.2)  # のけぞる
    ren.key(F("4-6", 4.2), lean=0.0, armL=(0, 0.1), armR=(0, 0.1), head=-0.1)
    side = N(U1)
    cams.move("4-6", P(U1 + 2) + side * 13 + Vector((0, 0, 4.5)), P(U1 + 12, 2.5),
              P(U1 + 3) + side * 12 + Vector((0, 0, 4.3)), P(U1 + 16, 3.0), 24)

    # 4-7: 境内を駆け抜け、光へ飛び込む
    s7, e7 = tl.range("4-7")
    run2 = ren.move(s7, F("4-7", 3.0), path_pts(U1 + 6, GATE_U - 1.5, 10), "sprint")
    jump = ren.move(F("4-7", 3.0), F("4-7", 4.2),
                    [P(GATE_U - 1.5), P(GATE_U - 0.5, 1.6), P(GATE_U + 0.5, 3.0)], "sprint",
                    extra=lambda f: dict(legL=1.0, legR=-0.6, armL=(2.6, 0.2), armR=(2.6, 0.2), lean=0.4))
    visible(ren.root, None, F("4-7", 4.3))
    t = T(U1)

    def cam7(f, k):
        p = run2(f) if f < F("4-7", 3.0) else jump(f)
        return (p - t * (4.0 - k * 1.5) + Vector((0, 0, 1.0)) + shake(0.03, f), p + t * 4 + Vector((0, 0, 1.4)))
    cams.track("4-7", cam7, 24)
