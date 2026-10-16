"""『返り音』プリビズ共通ライブラリ (Blender 4.2+ / 5.x)

ショット表・マネキン・カラス・カメラ・波紋などの部品。
各シーン (sc1.py 〜 sc9.py) はこれを使ってセットと動きを組み立てる。
"""

import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

FPS = 24
STEP = 2  # キーを打つ間隔 (レンダーも 2 フレームおき = 12fps)


# ---------------------------------------------------------------- ショット表
class Timeline:
    """shots: [{"id", "dur", "size", "move", "desc", "lines", "sfx"}]"""

    def __init__(self, shots):
        self.shots = shots
        self.start = {}
        f = 1
        for s in shots:
            self.start[s["id"]] = f
            f += round(s["dur"] * FPS)
        self.end_frame = f - 1
        CUTS[:] = sorted(self.start.values())

    def f(self, sid, t=0.0):
        return self.start[sid] + round(t * FPS)

    def range(self, sid):
        s = self.start[sid]
        dur = next(x["dur"] for x in self.shots if x["id"] == sid)
        return s, s + round(dur * FPS) - 1


CUTS = []  # 各ショットの開始フレーム。ポーズの保持キーがカットをまたがないようにする


def hold_frame(f, blend):
    """f の blend フレーム前。ただし直前のカットより前には戻さない"""
    h = f - blend
    cut = max([c for c in CUTS if c <= f], default=None)
    if cut is not None and h < cut:
        h = cut if cut < f else f - 1
    return h


def frames(f0, f1, step=STEP):
    f = f0
    while f < f1:
        yield f
        f += step
    yield f1


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def vlerp(a, b, k):
    return Vector(a).lerp(Vector(b), k)


# ---------------------------------------------------------------- シーン
def reset_scene(world_rgb, sky_rgb=None):
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.actions):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)
    sc = bpy.context.scene
    sc.timeline_markers.clear()
    sc.render.fps = FPS
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    world.color = world_rgb
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = True
    sh.shadow_intensity = 0.3
    sh.show_cavity = False
    sc.display.light_direction = (0.45, -0.35, 0.82)
    return sc


def set_sun(direction):
    bpy.context.scene.display.light_direction = Vector(direction).normalized()


_MATS = {}


def mat(name, rgb):
    key = (name, tuple(round(c, 3) for c in rgb))
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    _MATS[key] = m
    return m


def collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def empty(name, coll, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    coll.objects.link(e)
    e.parent = parent
    e.location = loc
    e.empty_display_size = 0.2
    return e


# ---------------------------------------------------------------- メッシュ組み立て
def _faces(verts):
    return {f for v in verts for f in v.link_faces}


class MB:
    """bmesh を使って 1 オブジェクトに部品を積んでいくビルダー"""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _finish(self, verts, m, loc, rot, scale=None):
        if scale is not None:
            bmesh.ops.scale(self.bm, vec=Vector(scale), verts=verts)
        mtx = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=mtx, verts=verts)
        self.last = list(verts)
        idx = self._mi(m)
        for f in _faces(verts):
            f.material_index = idx

    def box(self, size, loc, m, rot=(0, 0, 0)):
        v = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        self._finish(v, m, loc, rot, size)
        return self

    def cyl(self, r, h, loc, m, rot=(0, 0, 0), r2=None, seg=10):
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r,
                                  radius2=r if r2 is None else r2, depth=h)["verts"]
        self._finish(v, m, loc, rot)
        return self

    def sphere(self, r, loc, m, scale=(1, 1, 1), rot=(0, 0, 0), sub=1):
        v = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)["verts"]
        self._finish(v, m, loc, rot, scale)
        return self

    def torus(self, R, r, loc, m, rot=(0, 0, 0), seg=24, rseg=6):
        bm = self.bm
        rings = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring = []
            for j in range(rseg):
                b = 2 * math.pi * j / rseg
                p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
                ring.append(bm.verts.new(p))
            rings.append(ring)
        for i in range(seg):
            for j in range(rseg):
                a, b = rings[i], rings[(i + 1) % seg]
                bm.faces.new((a[j], b[j], b[(j + 1) % rseg], a[(j + 1) % rseg]))
        self._finish([v for ring in rings for v in ring], m, loc, rot)
        return self

    def obj(self, name, coll, parent=None, loc=(0, 0, 0)):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        o.parent = parent
        o.location = loc
        return o


# ---------------------------------------------------------------- 表示切り替え
def _all(obj):
    yield obj
    for c in obj.children_recursive:
        yield c


def visible(obj, f_on=None, f_off=None):
    """f_on から表示、f_off から非表示 (None は端まで)"""
    for o in _all(obj):
        keys = []
        if f_on is not None and f_on > 1:
            keys += [(1, True), (f_on, False)]
        else:
            keys += [(1, False)]
        if f_off is not None:
            keys += [(f_off, True)]
        for f, hide in keys:
            o.hide_render = hide
            o.hide_viewport = hide
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)
        _constant(o)


def _constant(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        if fc.data_path.startswith("hide"):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def _fcurves(action):
    if hasattr(action, "fcurves") and len(getattr(action, "fcurves", [])):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def wpos(obj, f, local=(0, 0, 0)):
    bpy.context.scene.frame_set(f)
    return obj.matrix_world @ Vector(local)


def key_tr(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
        o.keyframe_insert("scale", frame=f)


# ---------------------------------------------------------------- 人物 (マネキン)
LIMBS = ("armL", "armR", "legL", "legR")


class Actor:
    """前方 = ローカル +Y。ポーズは各関節の回転 (ラジアン)。

    armL/armR = (前後振り x [+で前へ], 横上げ y [+で外側へ])、elbowL/elbowR = 肘の曲げ (+で前腕が前/上へ)
    legL/legR = 前後振り x、lean = 上体の前傾、hipz = 腰の高さオフセット、pitch/roll = 全身の傾き (寝る等)
    head = うなずき (+ で下を向く)

    key() は前のキーから blend フレーム以上空いていると、直前の姿勢を blend フレーム前に保持してから
    動かす (キーの間でポーズがじわじわ動き出すのを防ぐ)。ゆっくり動かしたいときは blend=0。
    """

    UPPER, FORE = 0.31, 0.31

    def __init__(self, name, coll, color, height=1.0, hair=None, skirt=False):
        self.name = name
        body = mat(f"{name}_body", color)
        dark = mat(f"{name}_dark", tuple(c * 0.45 for c in color))
        self.root = empty(name, coll)
        self.root.scale = (height,) * 3
        self.hips = empty(f"{name}_hips", coll, self.root, (0, 0, 0.95))
        MB().cyl(0.17, 0.58, (0, 0, 0.29), body, r2=0.15).obj(f"{name}_torso", coll, self.hips)
        self.neck = empty(f"{name}_neck", coll, self.hips, (0, 0, 0.6))
        mb = MB().sphere(0.12, (0, 0, 0.13), body, scale=(1, 1.05, 1.15), sub=2)
        mb.box((0.11, 0.04, 0.045), (0, 0.105, 0.12), mat("face", (0.93, 0.8, 0.68)))  # 顔の向きがわかる目印
        if hair:
            mb.sphere(0.13, (0, -0.04, 0.16), mat(f"{name}_hair", hair), scale=(1.05, 1.0, 1.05), sub=2)
            mb.sphere(0.07, (0, -0.13, 0.17), mat(f"{name}_hair", hair), sub=1)
        mb.obj(f"{name}_head", coll, self.neck)
        if skirt:
            MB().cyl(0.26, 0.4, (0, 0, -0.12), body, r2=0.16, seg=12).obj(f"{name}_skirt", coll, self.hips)
        self.j = {}
        U, Fo = self.UPPER, self.FORE
        for side, x in (("L", -1), ("R", 1)):
            sh = empty(f"{name}_arm{side}", coll, self.hips, (0.22 * x, 0, 0.52))
            MB().cyl(0.052, U, (0, 0, -U / 2), body, seg=8).sphere(0.05, (0, 0, -U), body).obj(
                f"{name}_armmesh{side}", coll, sh)
            el = empty(f"{name}_elbow{side}", coll, sh, (0, 0, -U))
            MB().cyl(0.045, Fo, (0, 0, -Fo / 2), body, seg=8).sphere(0.055, (0, 0, -Fo - 0.03), dark).obj(
                f"{name}_forearm{side}", coll, el)
            hp = empty(f"{name}_leg{side}", coll, self.hips, (0.1 * x, 0, 0.02))
            MB().cyl(0.07, 0.92, (0, 0, -0.46), dark, r2=0.055, seg=8).obj(f"{name}_legmesh{side}", coll, hp)
            sh.rotation_mode = hp.rotation_mode = el.rotation_mode = "XYZ"
            self.j[f"arm{side}"] = sh
            self.j[f"elbow{side}"] = el
            self.j[f"leg{side}"] = hp
        self.loc = Vector((0, 0, 0))
        self.yaw = 0.0
        self.last_f = None
        self.pose = dict(armL=(0, 0.08), armR=(0, 0.08), elbowL=0.15, elbowR=0.15, legL=0.0, legR=0.0,
                         lean=0.0, hipz=0.0, pitch=0.0, roll=0.0, head=0.0, rootz=0.0)

    def _write(self, f):
        p = self.pose
        self.root.location = self.loc + Vector((0, 0, p["rootz"]))
        self.root.rotation_euler = (p["pitch"], p["roll"], self.yaw)
        self.root.keyframe_insert("location", frame=f)
        self.root.keyframe_insert("rotation_euler", frame=f)
        self.hips.location = (0, 0, 0.95 + p["hipz"])
        self.hips.rotation_euler = (-p["lean"], 0, 0)
        self.hips.keyframe_insert("location", frame=f)
        self.hips.keyframe_insert("rotation_euler", frame=f)
        self.neck.rotation_euler = (-p["head"], 0, 0)
        self.neck.keyframe_insert("rotation_euler", frame=f)
        for side in "LR":
            ax, ay = p[f"arm{side}"]
            self.j[f"arm{side}"].rotation_euler = (ax, ay if side == "L" else -ay, 0)
            self.j[f"arm{side}"].keyframe_insert("rotation_euler", frame=f)
            self.j[f"elbow{side}"].rotation_euler = (p[f"elbow{side}"], 0, 0)
            self.j[f"elbow{side}"].keyframe_insert("rotation_euler", frame=f)
            self.j[f"leg{side}"].rotation_euler = (p[f"leg{side}"], 0, 0)
            self.j[f"leg{side}"].keyframe_insert("rotation_euler", frame=f)

    # 1 フレームに全関節のキーを打つ
    def key(self, f, loc=None, yaw=None, blend=8, **pose):
        if loc is not None:
            new = Vector(loc) if len(loc) == 3 else Vector((loc[0], loc[1], 0))
            if (new - self.loc).length > 1.5:  # 別の場所への移動はカット扱い (間を補間しない)
                blend = 1
        if blend and self.last_f is not None and f - self.last_f > blend:
            self._write(hold_frame(f, blend))
        if loc is not None:
            self.loc = new
        if yaw is not None:
            self.yaw = yaw
        self.pose.update(pose)
        self._write(f)
        self.last_f = f if self.last_f is None else max(self.last_f, f)

    def hold(self, f0, f1, **pose):
        self.key(f0, **pose)
        self.key(f1)

    def face(self, target):
        t = Vector((target[0], target[1], 0))
        d = t - Vector((self.loc.x, self.loc.y, 0))
        return math.atan2(d.y, d.x) - math.pi / 2

    def move(self, f0, f1, pts, style="walk", ease_in=False, face=True, swing=None, extra=None):
        """pts を通る折れ線を f0→f1 で移動。歩き/走りの手足の振りを自動で付ける"""
        pts = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0)) for p in pts]
        seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
        total = sum(seg) or 1e-6
        amp, cadence, lean, bob, elbow = {
            "walk": (0.35, 14, 0.04, 0.025, 0.3),
            "run": (0.95, 8, 0.22, 0.06, 1.4),
            "sprint": (1.1, 7, 0.32, 0.07, 1.5),
        }[style]
        if swing is not None:
            amp = swing

        def at(f):
            k = (f - f0) / max(1, f1 - f0)
            k = ease(k) if ease_in else max(0.0, min(1.0, k))
            d = k * total
            for i, L in enumerate(seg):
                if d <= L or i == len(seg) - 1:
                    t = d / L if L else 0
                    return pts[i].lerp(pts[i + 1], min(1, t)), (pts[i + 1] - pts[i])
                d -= L

        for f in frames(f0, f1):
            p, dirv = at(f)
            ph = 2 * math.pi * (f - f0) / (cadence * 2)
            s = math.sin(ph)
            pose = dict(armL=(-amp * s * 0.8, 0.1), armR=(amp * s * 0.8, 0.1), elbowL=elbow, elbowR=elbow,
                        legL=amp * s * 0.8, legR=-amp * s * 0.8, lean=lean,
                        hipz=bob * abs(math.sin(ph)))
            if extra:
                pose.update(extra(f))
            yaw = math.atan2(dirv.y, dirv.x) - math.pi / 2 if face and dirv.length > 1e-4 else None
            self.key(f, loc=p, yaw=yaw, **pose)
        self.key(f1 + 1, armL=(0, 0.08), armR=(0, 0.08), elbowL=0.15, elbowR=0.15, legL=0, legR=0, lean=0, hipz=0)
        return lambda f: at(min(max(f, f0), f1))[0]

    def pos(self):
        return self.loc.copy()

    def hand(self, side, f):
        """f フレームでの手の位置 (ワールド座標)"""
        return wpos(bpy.data.objects[f"{self.name}_forearm{side}"], f, (0, 0, -self.FORE - 0.03))

    def reach(self, f, side, target, **pose):
        """f フレームで side の手が target (ワールド座標) に届くよう肩と肘を決めてキーを打つ (簡易 2 ボーン IK)。
        体の他の部分のポーズは pose で先に指定できる"""
        if pose:
            self.key(f, **pose)
        wpos(self.hips, f)
        hips = self.hips.matrix_world.copy()
        t = hips.inverted() @ Vector(target) - Vector((0.22 * (1 if side == "R" else -1), 0, 0.52))
        U, Fo = self.UPPER, self.FORE + 0.03
        d = min(t.length, U + Fo - 1e-4)
        e = math.acos(max(-1.0, min(1.0, (d * d - U * U - Fo * Fo) / (2 * U * Fo))))
        v0 = Vector((0, Fo * math.sin(e), -U - Fo * math.cos(e)))
        best = None
        for i in range(73):
            ax = -1.2 + i * (4.4 / 72)
            for j in range(49):
                ay = -1.6 + j * (3.2 / 48)
                v = Euler((ax, ay, 0)).to_matrix() @ v0
                err = (v - t).length_squared
                if best is None or err < best[0]:
                    best = (err, ax, ay)
        _, ax, ay = best
        user_ay = ay if side == "L" else -ay
        self.key(f, **{f"arm{side}": (ax, user_ay), f"elbow{side}": e})
        return wpos(bpy.data.objects[f"{self.name}_forearm{side}"], f, (0, 0, -Fo))

    def head_at(self, f):
        return wpos(bpy.data.objects[f"{self.name}_head"], f, (0, 0.05, 0.12))

    def head_pos(self, height=1.0):
        return self.loc + Vector((0, 0, 1.62 * height + self.pose["hipz"]))


# ---------------------------------------------------------------- カラス
class Crow:
    def __init__(self, name, coll, eye=(1.0, 0.75, 0.1)):
        black = mat("crow_black", (0.03, 0.03, 0.04))
        beak = mat("crow_beak", (0.12, 0.12, 0.13))
        gold = mat("crow_eye", eye)
        self.root = empty(name, coll)
        MB().sphere(0.1, (0, 0, 0.12), black, scale=(0.8, 1.5, 0.85), sub=2) \
            .box((0.08, 0.16, 0.02), (0, -0.2, 0.12), black, rot=(0.3, 0, 0)) \
            .cyl(0.008, 0.1, (-0.03, 0.02, 0.04), beak).cyl(0.008, 0.1, (0.03, 0.02, 0.04), beak) \
            .obj(f"{name}_body", coll, self.root)
        self.head = empty(f"{name}_neck", coll, self.root, (0, 0.12, 0.2))
        MB().sphere(0.065, (0, 0.03, 0.02), black, sub=2) \
            .cyl(0.025, 0.08, (0, 0.11, 0.015), beak, rot=(-math.pi / 2, 0, 0), r2=0.002, seg=6) \
            .sphere(0.014, (-0.04, 0.06, 0.04), gold).sphere(0.014, (0.04, 0.06, 0.04), gold) \
            .obj(f"{name}_head", coll, self.head)
        self.wings = []
        for x in (-1, 1):
            w = empty(f"{name}_wing{x}", coll, self.root, (0.06 * x, 0.0, 0.16))
            MB().box((0.26, 0.16, 0.012), (0.13 * x, -0.02, 0), black).obj(f"{name}_wingmesh{x}", coll, w)
            w.rotation_mode = "XYZ"
            self.wings.append((w, x))
        self.loc, self.yaw, self.scale, self.flap, self.peck = Vector(), 0.0, 1.0, -1.2, 0.0
        self.root.rotation_mode = "XYZ"

    def key(self, f, loc=None, yaw=None, scale=None, flap=None, peck=None, blend=8):
        last = getattr(self, "last_f", None)
        if loc is not None and (Vector(loc) - self.loc).length > 3.0:
            blend = 1
        if blend and last is not None and f - last > blend:
            self._write(hold_frame(f, blend))
        self.last_f = f if last is None else max(last, f)
        if loc is not None:
            self.loc = Vector(loc)
        if yaw is not None:
            self.yaw = yaw
        if scale is not None:
            self.scale = scale
        if flap is not None:
            self.flap = flap
        if peck is not None:
            self.peck = peck
        self._write(f)

    def _write(self, f):
        key_tr(self.root, f, loc=self.loc, rot=(0, 0, self.yaw), scale=self.scale)
        for w, x in self.wings:
            w.rotation_euler = (0, -x * self.flap, 0)  # flap: +上 / -1.2 畳む
            w.keyframe_insert("rotation_euler", frame=f)
        self.head.rotation_euler = (-self.peck, 0, 0)
        self.head.keyframe_insert("rotation_euler", frame=f)

    def fly(self, f0, f1, pts, scale=None, beat=6, amp=0.9):
        pts = [Vector(p) for p in pts]
        n = len(pts) - 1
        for f in frames(f0, f1):
            k = (f - f0) / max(1, f1 - f0) * n
            i = min(int(k), n - 1)
            p = pts[i].lerp(pts[i + 1], k - i)
            d = pts[i + 1] - pts[i]
            yaw = math.atan2(d.y, d.x) - math.pi / 2
            flap = amp * math.sin(2 * math.pi * (f - f0) / (beat * 2))
            self.key(f, loc=p, yaw=yaw, flap=flap, scale=scale)
        self.key(f1 + 1, flap=-1.2)

    def bells(self, coll, f_on, f_end, ring=()):
        """翼の羽根の隙間から古い鐘が現れ、ring のフレームで揺れる"""
        gold = mat("bell", (0.75, 0.58, 0.22))
        for w, x in self.wings:
            for i, off in enumerate((0.08, 0.15, 0.22)):
                b = MB().cyl(0.012, 0.035, (0, 0, -0.018), gold, r2=0.022, seg=10) \
                    .sphere(0.006, (0, 0, -0.04), gold).obj(f"Bell{x}_{i}", coll, w, (off * x, -0.02, -0.01))
                b.rotation_mode = "XYZ"
                key_tr(b, 1, scale=0.001)
                key_tr(b, f_on + i * 4, scale=0.001)
                key_tr(b, f_on + i * 4 + 12, scale=1.0)
                for f in ring:
                    for k, ang in ((0, 0), (4, 0.5), (10, -0.4), (16, 0.25), (24, 0)):
                        key_tr(b, f + k + i, rot=(ang * (1 if x > 0 else -1), 0, 0))

    def tap(self, f, gap=8):
        """くちばしでトン、トン"""
        for k, v in ((f - 4, 0.0), (f, 0.7), (f + 3, 0.1), (f + gap, 0.7), (f + gap + 3, 0.1), (f + gap + 8, 0.0)):
            self.key(k, peck=v)


# ---------------------------------------------------------------- エフェクト
def ripple(coll, center, f0, dur=1.5, radius=3.0, color=(0.75, 0.85, 1.0), width=0.06):
    """水面の波紋。width は最大半径に広がったときの輪の太さ (m)"""
    o = MB().torus(1.0, width / radius, (0, 0, 0), mat("ripple", color), seg=48, rseg=4).obj("Ripple", coll, loc=center)
    o.scale = (1, 1, 0.3)
    f1 = f0 + round(dur * FPS)
    key_tr(o, f0, scale=(0.05, 0.05, 0.3))
    key_tr(o, f1, scale=(radius, radius, 0.3))
    visible(o, f0, f1)
    return o


def butterflies(coll, center, f0, n=30, dur=2.5, spread=4.0, color=(0.55, 0.8, 1.0), seed=1, size=1.0):
    rng = random.Random(seed)
    m = mat("butterfly", color)
    for i in range(n):
        w, d = 0.14 * size, 0.08 * size
        b = MB().box((w, d, 0.005), (w / 2, 0, 0), m).box((w, d, 0.005), (-w / 2, 0, 0), m) \
            .obj("Butterfly", coll, loc=center)
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.3, 1.5))).normalized()
        end = Vector(center) + d * spread * rng.uniform(0.5, 1.0)
        f1 = f0 + round(dur * FPS * rng.uniform(0.7, 1.0))
        for f in frames(f0, f1):
            k = (f - f0) / (f1 - f0)
            p = Vector(center).lerp(end, ease(k)) + Vector((0, 0, 0.3 * math.sin(k * 9 + i)))
            flap = 0.3 + 0.7 * abs(math.sin((f - f0) * 0.8 + i))
            key_tr(b, f, loc=p, rot=(0, 0, k * 3 + i), scale=(flap * (1 - k * 0.7), 1, 1))
        visible(b, f0, f1)


def mirror_root(coll):
    """z=0 で上下反転する親。ここに子を付けると水面の映り込みになる"""
    m = empty("MirrorRoot", coll)
    m.scale = (1, 1, -1)
    return m


WATER_TINT = (0.12, 0.2, 0.38)


def _tint_slots(d):
    """映り込み用に、マテリアルを水の色に寄せた暗い色に差し替える"""
    if not getattr(d, "material_slots", None):
        return
    for slot in d.material_slots:
        src = slot.material
        if src is None:
            continue
        c = src.diffuse_color
        slot.link = "OBJECT"
        slot.material = mat(src.name + "_refl", tuple(c[i] * 0.5 + WATER_TINT[i] * 0.5 for i in range(3)))


def reflect(obj, mirror, coll):
    """アニメーション付きのオブジェクト階層を水面に映す (Copy Transforms をローカル空間で)"""
    def dup(src, parent):
        d = bpy.data.objects.new(src.name + "_refl", src.data)
        coll.objects.link(d)
        _tint_slots(d)
        d.parent = parent
        c = d.constraints.new("COPY_TRANSFORMS")
        c.target = src
        c.owner_space = c.target_space = "LOCAL"
        for ch in src.children:
            dup(ch, d)
        return d
    return dup(obj, mirror)


def reflect_static(objs, mirror):
    for o in objs:
        d = o.copy()
        bpy.context.scene.collection.objects.link(d)
        d.parent = mirror
        d.animation_data_clear()
        _tint_slots(d)


# ---------------------------------------------------------------- カメラ
class Cams:
    def __init__(self, tl, coll):
        self.tl, self.coll, self.cams = tl, coll, {}

    def make(self, sid, lens=35):
        data = bpy.data.cameras.new(f"CAM_{sid}")
        data.lens = lens
        data.clip_start = 0.05
        data.clip_end = 8000
        cam = bpy.data.objects.new(f"CAM_{sid}", data)
        cam.rotation_mode = "QUATERNION"
        self.coll.objects.link(cam)
        mk = bpy.context.scene.timeline_markers.new(sid, frame=self.tl.start[sid])
        mk.camera = cam
        self.cams[sid] = cam
        cam["_prevq"] = [1, 0, 0, 0]
        return cam

    def key(self, cam, f, pos, target, lens=None, roll=0.0):
        q = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y")
        if roll:
            q = q @ Euler((0, 0, roll)).to_quaternion()
        prev = cam["_prevq"]
        if q.dot(type(q)(prev)) < 0:
            q.negate()
        cam["_prevq"] = list(q)
        cam.location = pos
        cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
        if lens is not None:
            cam.data.lens = lens
            cam.data.keyframe_insert("lens", frame=f)

    def static(self, sid, pos, target, lens=35):
        cam = self.make(sid, lens)
        s, e = self.tl.range(sid)
        self.key(cam, s, pos, target)
        return cam

    def move(self, sid, pos0, tgt0, pos1, tgt1, lens=35, lens1=None, smooth=True):
        cam = self.make(sid, lens)
        s, e = self.tl.range(sid)
        for f in frames(s, e):
            k = (f - s) / max(1, e - s)
            k = ease(k) if smooth else k
            ln = lerp(lens, lens1, k) if lens1 else None
            self.key(cam, f, vlerp(pos0, pos1, k), vlerp(tgt0, tgt1, k), lens=ln)
        return cam

    def track(self, sid, fn, lens=35):
        """fn(f, k) -> (pos, target[, lens[, roll]])"""
        cam = self.make(sid, lens)
        s, e = self.tl.range(sid)
        for f in frames(s, e):
            r = fn(f, (f - s) / max(1, e - s))
            self.key(cam, f, r[0], r[1], lens=r[2] if len(r) > 2 else None, roll=r[3] if len(r) > 3 else 0.0)
        return cam


def shake(amount, f, seed=0):
    rng = random.Random(f * 7919 + seed)
    return Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * amount


# ---------------------------------------------------------------- 共通セット
def ground(coll, size, rgb, loc=(0, 0, 0), name="Ground"):
    return MB().box((size[0], size[1], 0.1), (0, 0, -0.05), mat(name, rgb)).obj(name, coll, loc=loc)


def torii(mb, loc, yaw, scale=1.0, red=(0.8, 0.1, 0.03), black=(0.03, 0.03, 0.03), roll=0.0):
    """伏見稲荷型の鳥居を MB に追加 (柱間 1.8m * scale)"""
    r, b = mat("torii_red", red), mat("torii_black", black)
    rot = Euler((0, roll, yaw)).to_matrix().to_4x4()
    base = Matrix.Translation(Vector(loc)) @ rot @ Matrix.Scale(scale, 4)

    def part(kind, *args, m):
        getattr(mb, kind)(*args, m)
        bmesh.ops.transform(mb.bm, matrix=base, verts=mb.last)

    for x in (-0.9, 0.9):
        part("cyl", 0.12, 0.35, (x, 0, 0.175), m=b)
        part("cyl", 0.11, 2.3, (x, 0, 1.5), m=r)
    part("box", (2.3, 0.12, 0.15), (0, 0, 2.2), m=r)
    part("box", (2.8, 0.26, 0.2), (0, 0, 2.62), m=r)
    part("box", (3.0, 0.3, 0.1), (0, 0, 2.77), m=b)
    part("box", (0.14, 0.1, 0.4), (0, 0, 2.38), m=r)


def machiya(mb, loc, w, d, h, wall, roof_m, wood_m, facing=1):
    """京町家っぽい箱 (壁・格子・瓦屋根)"""
    x, y = loc[0], loc[1]
    mb.box((d, w, h), (x, y, h / 2), wall)
    mb.box((0.06, w * 0.9, h * 0.5), (x - facing * d / 2, y, h * 0.35), wood_m)  # 格子
    mb.box((d + 0.8, w + 0.2, 0.12), (x - facing * 0.2, y, h + 0.06), roof_m, rot=(0, facing * 0.35, 0))
    mb.box((1.1, w + 0.2, 0.08), (x - facing * (d / 2 + 0.45), y, h * 0.5), roof_m,
           rot=(0, -facing * 0.25, 0))  # 一文字庇


def pagoda(mb, loc, tiers, size, wall, roof_m, rot=(0, 0, 0), flip=False):
    """層塔 (flip=True で逆さま)。浮遊建築用"""
    x, y, z = loc
    s = -1 if flip else 1
    for i in range(tiers):
        w = size * (1 - i * 0.12)
        zz = z + s * i * size * 0.75
        mb.box((w * 0.6, w * 0.6, size * 0.45), (x, y, zz + s * size * 0.22), wall, rot=rot)
        mb.box((w * 1.1, w * 1.1, size * 0.08), (x, y, zz + s * size * 0.5), roof_m, rot=rot)
    mb.cyl(size * 0.04, size * 1.2, (x, y, z + s * (tiers * size * 0.75 + size * 0.4)), roof_m)


def temple(mb, loc, w, d, h, wall, roof_m, rot=(0, 0, 0), flip=False):
    x, y, z = loc
    s = -1 if flip else 1
    mb.box((w, d, h), (x, y, z + s * h / 2), wall, rot=rot)
    mb.box((w * 1.35, d * 1.35, h * 0.12), (x, y, z + s * h * 1.05), roof_m, rot=rot)
    mb.box((w * 0.9, d * 0.9, h * 0.35), (x, y, z + s * h * 1.25), roof_m, rot=rot)


def lanterns(coll, n, area, zrange, seed=3, color=(1.0, 0.72, 0.3), size=0.25, name="Lanterns", skip=None):
    """浮かぶ灯籠。skip(p) が True の位置には置かない (人物やカメラの通り道を空ける)"""
    rng = random.Random(seed)
    mb = MB()
    m = mat(name, color)
    for _ in range(n):
        p = (rng.uniform(*area[0]), rng.uniform(*area[1]), rng.uniform(*zrange))
        if skip and skip(p):
            continue
        s = size * rng.uniform(0.7, 1.3)
        mb.cyl(s * 0.5, s, p, m, seg=6)
    return mb.obj(name, coll)
