"""SCENE 2｜突然の別れ (0:35〜1:20) 夜の部屋 → 病院"""

import math

from mathutils import Vector

from lib import (MB, Actor, Cams, collection, ease, frames, key_tr, mat, reset_scene, set_sun, shake, vlerp)
from sc1 import HAIR, MIO_C, REN_C
from sets import room

TITLE = "突然の別れ"
SHOTS = [
    dict(id="2-1", dur=5, size="ロング / 28mm", move="FIX",
         desc="その夜。部屋の座卓に置いたスマホが震える。見知らぬ番号", lines=[], sfx=[(1.0, "ring")]),
    dict(id="2-2", dur=6, size="バストショット / 50mm", move="FIX",
         desc="蓮が電話に出る",
         lines=[(0.6, "蓮", "はい……？"), (2.0, "電話", "突然のお電話失礼します。〇〇病院の者ですが……")]),
    dict(id="2-3", dur=3, size="顔アップ / 85mm", move="ゆっくり寄り",
         desc="表情が凍りつく", lines=[(0.0, "電話", "澪さんが交通事故に遭われまして……")]),
    dict(id="2-4", dur=5, size="フルショット / 35mm", move="正面から後退追従・手持ち",
         desc="夜の病院。雨に濡れた蓮が長い廊下を駆けてくる", lines=[], sfx=[(0.0, "rain")]),
    dict(id="2-5", dur=6, size="ロング / 28mm", move="FIX",
         desc="病室に飛び込み、ベッドの澪の手を握る",
         lines=[(1.4, "蓮", "澪！ 澪、聞こえる!?"), (3.6, "蓮", "お願いだ……目を開けてくれ……！")]),
    dict(id="2-6", dur=5, size="手元アップ / 85mm", move="FIX",
         desc="澪が残された力で、蓮の手を二回たたく", lines=[], sfx=[(2.0, "tap"), (2.5, "tap")]),
    dict(id="2-7", dur=3, size="顔アップ / 85mm", move="FIX", desc="蓮", lines=[(0.6, "蓮", "……澪？")]),
    dict(id="2-8", dur=4, size="手元 / 50mm", move="FIX", desc="澪の手から力が抜け、ベッドの外へ落ちる", lines=[]),
    dict(id="2-9", dur=5, size="俯瞰ロング / 24mm", move="FIX",
         desc="医師たちが処置。蓮は引き離される。やがて医師が首を振る", lines=[]),
    dict(id="2-10", dur=3, size="俯瞰 / 28mm", move="クレーンアップ",
         desc="崩れ落ちて泣く蓮。声が廊下に響く → 暗転", lines=[]),
]

HX = 60  # 病室の位置
STAFF_C = (0.45, 0.62, 0.58)


def hospital(coll):
    wall = mat("hosp_wall", (0.78, 0.8, 0.8))
    floor = mat("hosp_floor", (0.55, 0.58, 0.6))
    light = mat("hosp_light", (1, 1, 1))
    mb = MB()
    # 廊下 (x=40, +Y 方向)
    mb.box((3, 40, 0.1), (40, 10, -0.05), floor)
    mb.box((3, 40, 0.1), (40, 10, 2.85), wall)
    for x in (-1.5, 1.5):
        mb.box((0.1, 40, 2.9), (40 + x, 10, 1.45), wall)
        for y in range(-5, 30, 5):
            mb.box((0.06, 1.0, 2.1), (40 + x * 0.98, y, 1.05), mat("door", (0.55, 0.62, 0.7)))
    for y in range(-6, 30, 3):
        mb.box((0.6, 1.2, 0.04), (40, y, 2.78), light)
    # 病室
    mb.box((7, 7, 0.1), (HX, 0, -0.05), floor)
    mb.box((7, 0.1, 2.9), (HX, -3.5, 1.45), wall)
    mb.box((0.1, 7, 2.9), (HX - 3.5, 0, 1.45), wall)
    mb.box((1.05, 2.1, 0.55), (HX, 0, 0.28), mat("bed", (0.8, 0.82, 0.85)))
    mb.box((1.0, 2.0, 0.12), (HX, 0.05, 0.6), mat("sheet", (0.92, 0.93, 0.95)))
    mb.box((0.6, 0.35, 0.12), (HX, -0.82, 0.72), mat("pillow", (0.97, 0.97, 0.97)))
    mb.cyl(0.03, 1.8, (HX - 0.8, -0.9, 0.9), mat("iv", (0.7, 0.7, 0.72)))
    mb.box((0.25, 0.1, 0.35), (HX - 0.8, -0.9, 1.85), mat("ivbag", (0.85, 0.9, 0.95)))
    mb.box((0.5, 0.35, 0.4), (HX - 1.0, -1.4, 1.3), mat("monitor", (0.12, 0.14, 0.15)))
    mb.box((0.42, 0.02, 0.3), (HX - 1.0, -1.22, 1.3), mat("screen", (0.2, 0.8, 0.5)))
    mb.cyl(0.04, 1.1, (HX - 1.0, -1.4, 0.55), mat("iv", (0.7, 0.7, 0.72)))
    return mb.obj("Hospital", coll)


def build(tl):
    reset_scene((0.05, 0.06, 0.12))
    set_sun((0.3, -0.4, 0.85))
    coll = collection("SC2")
    room(coll)
    hospital(coll)
    F = tl.f
    cams = Cams(tl, coll)
    ren = Actor("Ren", coll, REN_C)
    mio = Actor("Mio", coll, MIO_C, height=0.92, hair=HAIR, skirt=True)

    # --- 部屋: 座って電話
    sit = dict(hipz=-0.55, legL=1.45, legR=1.45, lean=-0.05, armL=(0.6, 0.1), armR=(0.6, 0.1))
    ren.key(1, loc=(0, -0.45, 0), yaw=0, **sit)
    phone = MB().box((0.08, 0.16, 0.015), (0, 0, 0), mat("phone", (0.05, 0.05, 0.06))) \
        .box((0.07, 0.14, 0.004), (0, 0, 0.009), mat("phone_screen", (0.6, 0.85, 1.0))).obj("Phone", coll)
    base = Vector((0.25, 0.35, 0.42))
    for f in frames(1, F("2-2", 0.3)):
        key_tr(phone, f, loc=base + (Vector((0.01 * math.sin(f * 2.3), 0, 0)) if f > F("2-1", 1.0) else Vector()))
    ren.key(F("2-2", 0.0), armR=(0.6, 0.1))
    ren.key(F("2-2", 0.5), armR=(1.0, 0.1), elbowR=0.2, lean=0.15)
    key_tr(phone, F("2-2", 0.5), loc=base, rot=(0, 0, 0))
    ren.key(F("2-2", 1.0), armR=(1.0, 0.6), elbowR=2.2, lean=0.0, head=0.05)
    ren.key(F("2-3", 2.9), head=0.0)
    # 電話は手に持たせる (手の位置を毎フレーム追う)
    for f in frames(F("2-2", 0.5) + 2, F("2-3", 2.9)):
        key_tr(phone, f, loc=ren.hand("R", f) + Vector((0, 0.02, 0.06)), rot=(1.3, 0, 0.4))
    cams.move("2-1", (2.5, -2.4, 1.7), (0.1, 0.25, 0.45), (1.7, -1.5, 1.3), (0.2, 0.35, 0.42), 28)
    cams.static("2-2", (-0.45, 1.1, 1.2), (0.0, -0.45, 1.0), 50)
    cams.move("2-3", (-0.3, 0.75, 1.15), (0, -0.45, 1.1), (-0.2, 0.4, 1.13), (0, -0.45, 1.1), 85)

    # --- 廊下を走る
    s, e = tl.range("2-4")
    run = ren.move(s, e, [(40, 26), (40.2, 6)], "sprint")
    cams.track("2-4", lambda f, k: (run(f) + Vector((0.3, -4.2 + 0.6 * k, 1.1)) + shake(0.04, f),
                                    run(f) + Vector((0, 0, 1.2))), 35)

    # --- 病室
    head_y = -0.85
    mio.key(1, loc=(HX, head_y + 1.5, 0.82), yaw=0, pitch=math.pi / 2, armL=(-0.05, 0.3), armR=(-0.05, 0.35))
    s, _ = tl.range("2-5")
    ren.key(s, loc=(HX + 2.6, 3.2, 0), **dict(hipz=0, legL=0, legR=0, lean=0, armL=(0, 0.08), armR=(0, 0.08), head=0))
    ren.move(s, F("2-5", 1.2), [(HX + 2.6, 3.2), (HX + 0.95, -0.2)], "run")
    bed_side = dict(lean=0.5, hipz=-0.12, head=0.35)
    hand_m = mio.hand("R", F("2-5", 1.5))  # 澪の手 (シーツの上)

    def hold_hand(f, **pose):  # 蓮が両手で澪の手を包む
        ren.key(f, **pose)
        ren.reach(f, "R", hand_m + Vector((0.09, -0.03, 0.0)))
        ren.reach(f, "L", hand_m + Vector((0.07, 0.07, 0.06)))

    hold_hand(F("2-5", 1.5), yaw=math.pi / 2, **bed_side)
    for t in (2.0, 2.4, 3.6, 4.0):  # 呼びかけで身を乗り出す
        hold_hand(F("2-5", t), lean=0.62 if t in (2.0, 3.6) else 0.5)
    cams.static("2-5", (HX - 2.6, 2.9, 1.9), (HX + 0.4, -0.2, 0.8), 28)

    # 手を二回たたく
    for t in (2.0, 2.5):
        mio.key(F("2-6", t - 0.15), armR=(0.3, 0.35))
        mio.key(F("2-6", t), armR=(-0.05, 0.35))
    h = hand_m
    cams.static("2-6", h + Vector((0.15, -1.0, 0.45)), h, 85)
    ren.key(F("2-7", 0.4), head=0.15)
    hd = ren.head_at(F("2-7", 1.0))
    cams.static("2-7", hd + Vector((-1.2, -0.25, -0.35)), hd, 85)

    # 手が落ちる
    mio.key(F("2-8", 1.0), armR=(-0.05, 0.35))
    mio.key(F("2-8", 1.8), armR=(-0.9, 1.57))
    cams.static("2-8", h + Vector((0.35, -1.6, 0.5)), h + Vector((0.05, 0, -0.12)), 50)

    # 医師たち
    s, e = tl.range("2-9")
    staff = [Actor(f"Staff{i}", coll, STAFF_C) for i in range(2)]
    for i, st in enumerate(staff):
        st.key(1, loc=(HX + 3.0 + i, 3.4, 0))
        st.move(s, F("2-9", 1.2), [(HX + 3.0 + i, 3.4), (HX - 0.85, -0.5 + i * 0.9)], "run")
        st.key(F("2-9", 1.6), yaw=-math.pi / 2, lean=0.4, armL=(1.0, 0), armR=(1.0, 0))
        st.key(F("2-9", 3.6), lean=0.2)
        st.key(F("2-9", 4.0), lean=0.05, head=0.3, armL=(0, 0.08), armR=(0, 0.08))
    ren.move(F("2-9", 1.0), F("2-9", 2.4), [(HX + 0.95, -0.2), (HX + 1.9, 1.2)], "walk", face=False, swing=0.15,
             extra=lambda f: dict(armR=(1.0, 0.0), armL=(0.8, 0.0), lean=0.2))
    ren.key(F("2-9", 2.6), yaw=math.pi / 2 + 0.3, lean=0.1)
    for t in (3.8, 4.2, 4.6):  # 医師が首を振る
        staff[0].key(F("2-9", t), yaw=-math.pi / 2 + (0.3 if t != 4.2 else -0.3))
    cams.static("2-9", (HX + 3.2, -2.6, 2.6), (HX + 0.4, 0.3, 0.8), 24)

    # 崩れ落ちる
    ren.key(F("2-10", 0.3), hipz=-0.55, legL=1.45, legR=1.45, lean=0.6, head=0.6, armL=(0.9, 0.3), armR=(0.9, 0.3))
    for t in (0.9, 1.4, 1.9, 2.4):
        ren.key(F("2-10", t), lean=0.75 if int(t * 10) % 2 else 0.6)
    cams.move("2-10", (HX + 3.0, 2.4, 1.6), (HX + 1.9, 1.2, 0.6), (HX + 3.6, 3.2, 4.5), (HX + 1.9, 1.2, 0.4), 28)
