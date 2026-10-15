"""
ECHO プリビズ  S4「千本鳥居の疾走」 (Shot 4-1 〜 4-5 / 18秒 / 24fps)

使い方 (GUI):
  1. Blender で「新規 > 全般」ファイルを開く
  2. Scripting タブでこのファイルを開き「スクリプト実行」
  3. タイムラインのマーカーでカメラが自動で切り替わる (4-1〜4-5)
  4. 書き出したい場合は下の RENDER_MODE を変えて再実行し、
     レンダー > アニメーションをレンダリング (Ctrl+F12)

使い方 (コマンドライン):
  blender -b -P s4_torii_run.py -- --mode grey --render
  blender -b -P s4_torii_run.py -- --mode depth --render

RENDER_MODE:
  "GREY"  : Workbench のグレー表示 (AI の動画→動画/モーション参照用)
  "DEPTH" : 深度マップ (手前=白, 奥=黒)。ControlNet 等の depth 入力用
  "COLOR" : EEVEE の簡易カラー (朱→白のグラデーション確認用)

Blender 5.1 で動作確認済み。4.2 以降でも動く想定 (未確認)。
"""

import math
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- 設定
RENDER_MODE = "GREY"
RENDER_NOW = False          # True にすると実行後そのままレンダリング
OUTPUT_DIR = "//render/"    # .blend ファイルからの相対パス
CLEAR_SCENE = True          # 実行時にシーン内のオブジェクトを全削除する

FPS = 24
RES = (1920, 1080)          # 16:9 で作り、編集で 2.39:1 の黒帯を入れる

# 鳥居
TORII_START = 10.0          # 最初の鳥居の位置 (m)
TORII_END = 150.0
TORII_SPACING = 1.5
VERMILION = (0.80, 0.10, 0.03)
WHITE = (0.95, 0.95, 0.93)
FADE_FROM, FADE_TO = 0.35, 0.90   # 全体の何割から白に褪せ始め、どこで真っ白か

# 参道のうねり
CURVE_AMP = 3.0
CURVE_WAVELENGTH = 90.0

# 走り
RUN_START = 4.0             # 主人公の開始位置 (m)
SPEED_START = 5.5           # m/s
SPEED_END = 9.0             # m/s (後半に向けて加速)
STEP_FRAMES = 8             # 片足1歩のフレーム数

# ショット: (名前, 開始, 終了, レンズmm)
SHOTS = [
    ("4-1_back_low", 1, 72, 24),
    ("4-2_side_lily", 73, 168, 85),
    ("4-3_front_retreat", 169, 264, 16),
    ("4-4_pov", 265, 360, 24),
    ("4-5_crane_up", 361, 432, 24),
]
FRAME_END = SHOTS[-1][2]

SEED = 7


# ---------------------------------------------------------------- 参道
def path_point(u):
    x = CURVE_AMP * math.sin(2 * math.pi * u / CURVE_WAVELENGTH)
    return Vector((x, u, 0.0))


def path_tangent(u):
    dx = CURVE_AMP * 2 * math.pi / CURVE_WAVELENGTH * math.cos(2 * math.pi * u / CURVE_WAVELENGTH)
    return Vector((dx, 1.0, 0.0)).normalized()


def path_right(u):
    t = path_tangent(u)
    return Vector((t.y, -t.x, 0.0))


def runner_distance(frame):
    t = (frame - 1) / FPS
    accel = (SPEED_END - SPEED_START) / (FRAME_END / FPS)
    return RUN_START + SPEED_START * t + 0.5 * accel * t * t


def smoothstep(a, b, x):
    x = max(0.0, min(1.0, (x - a) / (b - a)))
    return x * x * (3 - 2 * x)


def ease(x):
    return smoothstep(0.0, 1.0, x)


# ---------------------------------------------------------------- 基本ユーティリティ
def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)
    bpy.context.scene.timeline_markers.clear()


def get_collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def make_material(name, color, emission=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)  # Workbench 用
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.6
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def faces_of(verts):
    return {f for v in verts for f in v.link_faces}


def bm_cyl(bm, radius, depth, center, mat_index=0, segments=12):
    res = bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius,
        depth=depth, matrix=Matrix.Translation(center))
    for f in faces_of(res["verts"]):
        f.material_index = mat_index


def bm_box(bm, size, center, mat_index=0, rot_z=0.0):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=res["verts"])
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ Matrix.Rotation(rot_z, 4, "Z"), verts=res["verts"])
    for f in faces_of(res["verts"]):
        f.material_index = mat_index


def bm_sphere(bm, radius, center, mat_index=0):
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius, matrix=Matrix.Translation(center))
    for f in faces_of(res["verts"]):
        f.material_index = mat_index


def mesh_object(name, bm, materials, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def place(obj, u, lateral=0.0, height=0.0):
    obj.location = path_point(u) + path_right(u) * lateral + Vector((0, 0, height))
    t = path_tangent(u)
    obj.rotation_euler = (0.0, 0.0, math.atan2(t.y, t.x) - math.pi / 2)


# ---------------------------------------------------------------- 鳥居
def torii_bmesh():
    """伏見稲荷の小さめの鳥居 (柱間 1.8m / 高さ 2.8m)。0=朱, 1=黒"""
    bm = bmesh.new()
    for x in (-0.9, 0.9):
        bm_cyl(bm, 0.12, 0.35, (x, 0, 0.175), 1)        # 根巻 (黒)
        bm_cyl(bm, 0.11, 2.30, (x, 0, 0.35 + 1.15), 0)  # 柱
    bm_box(bm, (2.30, 0.12, 0.15), (0, 0, 2.20), 0)     # 貫
    bm_box(bm, (2.80, 0.26, 0.20), (0, 0, 2.62), 0)     # 島木
    bm_box(bm, (3.00, 0.30, 0.10), (0, 0, 2.77), 1)     # 笠木 (黒)
    bm_box(bm, (0.14, 0.10, 0.40), (0, 0, 2.38), 0)     # 額束
    return bm


def build_torii(coll):
    black = make_material("M_Torii_Black", (0.02, 0.02, 0.02))
    count = int((TORII_END - TORII_START) / TORII_SPACING) + 1
    for i in range(count):
        u = TORII_START + i * TORII_SPACING
        p = (u - TORII_START) / (TORII_END - TORII_START)
        k = smoothstep(FADE_FROM, FADE_TO, p)
        color = tuple(a + (b - a) * k for a, b in zip(VERMILION, WHITE))
        mat = make_material(f"M_Torii_{i:03d}", color)
        obj = mesh_object(f"Torii_{i:03d}", torii_bmesh(), [mat, black], coll)
        place(obj, u)


# ---------------------------------------------------------------- 環境
def build_environment(coll):
    rng = random.Random(SEED)

    # 地面
    bm = bmesh.new()
    bm_box(bm, (60, 200, 0.1), (0, 90, -0.05))
    mesh_object("Ground", bm, [make_material("M_Ground", (0.25, 0.22, 0.18))], coll)

    # 石畳の参道
    bm = bmesh.new()
    for u in range(0, 160, 2):
        t = path_tangent(u + 1)
        bm_box(bm, (1.6, 1.9, 0.04), path_point(u + 1), rot_z=math.atan2(t.y, t.x) - math.pi / 2)
    mesh_object("Sando", bm, [make_material("M_Stone", (0.45, 0.43, 0.40))], coll)

    # 彼岸花 (手前ボケ用。主に 4-2 のカメラ側 = 右側に多めに配置)
    red = make_material("M_Higanbana", (0.85, 0.03, 0.02))
    stem = make_material("M_Stem", (0.15, 0.30, 0.10))
    bm = bmesh.new()
    u = 2.0
    while u < TORII_END:
        for side, density in ((1, 3), (-1, 1)):
            for _ in range(density):
                lat = side * rng.uniform(1.4, 4.0)
                h = rng.uniform(0.35, 0.6)
                base = path_point(u) + path_right(u) * lat
                bm_cyl(bm, 0.008, h, base + Vector((0, 0, h / 2)), 1, segments=4)
                bm_sphere(bm, rng.uniform(0.06, 0.09), base + Vector((0, 0, h)), 0)
        u += rng.uniform(0.4, 0.8)
    mesh_object("Higanbana", bm, [red, stem], coll)

    # 杉林 (背景の奥行き。右側は 4-2 のカメラ (9m) より外側に置く)
    bm = bmesh.new()
    u = 0.0
    while u < 170:
        for lat in (rng.uniform(-14, -3.5), rng.uniform(11, 18)):
            h = rng.uniform(12, 20)
            base = path_point(u) + path_right(u) * lat
            bm_cyl(bm, rng.uniform(0.2, 0.35), h, base + Vector((0, 0, h / 2)), 0, segments=8)
        u += rng.uniform(1.5, 3.0)
    mesh_object("Forest", bm, [make_material("M_Cedar", (0.12, 0.16, 0.10))], coll)

    # 出口の白い光 (4-4 で鳥居の奥に見える)
    bm = bmesh.new()
    bm_box(bm, (10, 0.1, 10), (0, 0, 4))
    exit_obj = mesh_object("Exit_Light", bm, [make_material("M_ExitLight", (1, 1, 1), emission=30.0)], coll)
    place(exit_obj, TORII_END + 12)

    # ライト
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(55), 0, math.radians(30))
    coll.objects.link(sun)


# ---------------------------------------------------------------- 主人公 (マネキン)
def key_loc_rot(obj, frame):
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_euler", frame=frame)


def build_runner(coll):
    mat = make_material("M_Runner", (0.85, 0.85, 0.85))
    root = bpy.data.objects.new("Runner", None)
    coll.objects.link(root)

    def part(name, bm, parent, loc):
        obj = mesh_object(name, bm, [mat], coll)
        obj.parent = parent
        obj.location = loc
        return obj

    bm = bmesh.new()
    bm_cyl(bm, 0.17, 0.65, (0, 0, 0))
    bm_sphere(bm, 0.12, (0, 0, 0.48))
    body = part("Runner_Body", bm, root, (0, 0, 1.15))

    limbs = []
    for side, x in (("L", -0.1), ("R", 0.1)):
        bm = bmesh.new()
        bm_cyl(bm, 0.06, 0.85, (0, 0, -0.42), segments=8)
        limbs.append((part(f"Runner_Leg{side}", bm, root, (x, 0, 0.88)), 1 if side == "L" else -1, 0.7))
        bm = bmesh.new()
        bm_cyl(bm, 0.045, 0.6, (0, 0, -0.3), segments=8)
        limbs.append((part(f"Runner_Arm{side}", bm, body, (x * 2.2, 0, 0.25)), -1 if side == "L" else 1, 0.9))

    for f in range(1, FRAME_END + 1, 2):
        place(root, runner_distance(f))
        root.rotation_euler.x = math.radians(-12)  # 前傾
        key_loc_rot(root, f)

        phase = 2 * math.pi * (f - 1) / (STEP_FRAMES * 2)
        body.location.z = 1.15 + 0.05 * abs(math.sin(phase))
        body.keyframe_insert("location", frame=f)
        for limb, sign, amp in limbs:
            limb.rotation_euler.x = sign * amp * math.sin(phase)
            limb.keyframe_insert("rotation_euler", frame=f)
    return body


# ---------------------------------------------------------------- カメラ
def look_quat(cam_pos, target):
    return (target - cam_pos).to_track_quat("-Z", "Y")


def runner_pos(f, height=0.0):
    u = runner_distance(f)
    return path_point(u) + Vector((0, 0, height)), u


def shot_pose(name, f, s0, s1):
    k = (f - s0) / max(1, s1 - s0)
    r, u = runner_pos(f)
    t, n, up = path_tangent(u), path_right(u), Vector((0, 0, 1))

    if name.startswith("4-1"):    # 低い位置から背中を追い、少しずつ追いつく
        back = 4.0 - 1.2 * ease(k)
        return r - t * back + up * 0.5, r + t * 3 + up * 1.3, None
    if name.startswith("4-2"):    # 鳥居の外から真横で並走、手前を彼岸花が流れる
        return r + n * 9.0 + up * 0.9, r + up * 1.0, None
    if name.startswith("4-3"):    # 正面から後退しながら表情を撮る
        return r + t * (2.4 - 0.4 * ease(k)) + up * 1.35, r + up * 1.45, None
    if name.startswith("4-4"):    # 主観。加速感のため 24mm → 16mm
        bob = 0.04 * math.sin(2 * math.pi * (f - 1) / STEP_FRAMES)
        ahead = path_point(u + 25) + up * 1.5
        return r + t * 0.9 + up * (1.65 + bob), ahead, 24 - 8 * ease(k)
    if name.startswith("4-5"):    # 急上昇して鳥居の列を見下ろす
        e = ease(k)
        pos = r - t * (3 - e) + up * (2.5 + 16 * e)
        target = path_point(u + 6 + 14 * e)
        return pos, target, None
    raise ValueError(name)


def build_cameras(coll, focus_obj):
    scene = bpy.context.scene
    cams = []
    for name, s0, s1, lens in SHOTS:
        cam_data = bpy.data.cameras.new(f"CAM_{name}")
        cam_data.lens = lens
        cam_data.clip_start = 0.05
        cam_data.clip_end = 400
        cam_data.dof.use_dof = name.startswith(("4-2", "4-3"))
        cam_data.dof.focus_object = focus_obj
        cam_data.dof.aperture_fstop = 1.8
        cam = bpy.data.objects.new(f"CAM_{name}", cam_data)
        cam.rotation_mode = "QUATERNION"
        coll.objects.link(cam)

        prev = None
        for f in range(max(1, s0 - 2), min(FRAME_END, s1 + 2) + 1):
            pos, target, f_lens = shot_pose(name, f, s0, s1)
            q = look_quat(pos, target)
            if prev is not None and prev.dot(q) < 0:
                q.negate()
            prev = q
            cam.location = pos
            cam.rotation_quaternion = q
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_quaternion", frame=f)
            if f_lens is not None:
                cam_data.lens = f_lens
                cam_data.keyframe_insert("lens", frame=f)

        marker = scene.timeline_markers.new(name, frame=s0)
        marker.camera = cam
        cams.append(cam)
    scene.camera = cams[0]


# ---------------------------------------------------------------- レンダー設定
def set_engine(scene, *names):
    for n in names:
        try:
            scene.render.engine = n
            return
        except TypeError:
            continue


def set_video_output(scene, path):
    s = scene.render.image_settings
    try:
        if hasattr(s, "media_type"):
            s.media_type = "VIDEO"
        s.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "HIGH"
        scene.render.filepath = path + "_"
    except (TypeError, AttributeError):
        s.file_format = "PNG"   # 動画出力できない環境では連番 PNG
        scene.render.filepath = path + "/frame_"


def depth_material():
    """カメラからの距離を白黒で出す (手前=白, 60m 先=黒)"""
    mat = bpy.data.materials.get("M_DepthOverride") or bpy.data.materials.new("M_DepthOverride")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    cam = nt.nodes.new("ShaderNodeCameraData")
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = 0.5
    rng.inputs["From Max"].default_value = 60.0
    rng.inputs["To Min"].default_value = 1.0
    rng.inputs["To Max"].default_value = 0.0
    emit = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cam.outputs[1], rng.inputs["Value"])   # View Z Depth
    nt.links.new(rng.outputs["Result"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def setup_world(color, strength=1.0):
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*color, 1.0)
        bg.inputs["Strength"].default_value = strength
    world.color = color


def setup_render(mode):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.frame_start, scene.frame_end = 1, FRAME_END
    view_layer = bpy.context.view_layer
    view_layer.material_override = None

    if mode == "GREY":
        set_engine(scene, "BLENDER_WORKBENCH")
        sh = scene.display.shading
        sh.light = "STUDIO"
        sh.color_type = "MATERIAL"
        sh.show_shadows = True
        sh.show_cavity = True
        if hasattr(sh, "use_dof"):
            sh.use_dof = True
        setup_world((0.55, 0.55, 0.58))
        set_video_output(scene, OUTPUT_DIR + "S4_grey")
    elif mode == "DEPTH":
        set_engine(scene, "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")
        view_layer.material_override = depth_material()
        setup_world((0, 0, 0))
        set_video_output(scene, OUTPUT_DIR + "S4_depth")
    elif mode == "COLOR":
        set_engine(scene, "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")
        setup_world((0.55, 0.42, 0.35), 0.8)  # 夕暮れ
        set_video_output(scene, OUTPUT_DIR + "S4_color")
    else:
        raise ValueError(f"unknown RENDER_MODE: {mode}")


# ---------------------------------------------------------------- 実行
def parse_cli():
    mode, render = RENDER_MODE, RENDER_NOW
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if "--mode" in args:
            mode = args[args.index("--mode") + 1].upper()
        render = render or "--render" in args
    return mode, render


def main():
    mode, render = parse_cli()
    if CLEAR_SCENE:
        clear_scene()
    coll = get_collection("S4_Previs")
    build_torii(coll)
    build_environment(coll)
    focus = build_runner(coll)
    build_cameras(coll, focus)
    setup_render(mode)
    bpy.context.scene.frame_set(1)
    print(f"[ECHO previs] S4 built: {len(SHOTS)} shots, {FRAME_END} frames, mode={mode}")
    if render:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
