"""『返り音』プリビズのビルド/レンダー入口

GUI: Blender の Scripting タブで開き、SCENE を書き換えて実行 → タイムラインで確認
CLI: blender -b -P build.py -- --scene 1 [--render OUTDIR] [--stills OUTDIR] [--res 854]

  --render  : 2 フレームおき (12fps) の PNG 連番を書き出す
  --stills  : 各ショットの中間フレームを 1 枚ずつ書き出す (絵コンテ用)
"""

import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import lib  # noqa: E402

SCENE = 1


def build(n):
    for name in ["lib", f"sc{n}"]:
        if name in sys.modules:
            importlib.reload(sys.modules[name])
    mod = importlib.import_module(f"sc{n}")
    tl = lib.Timeline(mod.SHOTS)
    mod.build(tl)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, tl.end_frame
    sc.render.engine = "BLENDER_WORKBENCH"
    first = sc.timeline_markers[0] if len(sc.timeline_markers) else None
    if first:
        sc.camera = min(sc.timeline_markers, key=lambda m: m.frame).camera
    sc.frame_set(1)
    return mod, tl


def setup_output(res):
    sc = bpy.context.scene
    sc.render.resolution_x = res
    sc.render.resolution_y = round(res * 9 / 16 / 2) * 2
    sc.render.resolution_percentage = 100
    s = sc.render.image_settings
    if hasattr(s, "media_type"):
        s.media_type = "IMAGE"
    s.file_format = "PNG"
    s.color_mode = "RGB"
    sc.display.render_aa = "8"


def camera_at(f):
    sc = bpy.context.scene
    cams = [m for m in sc.timeline_markers if m.frame <= f]
    return max(cams, key=lambda m: m.frame).camera if cams else sc.camera


def render_frames(out, step):
    sc = bpy.context.scene
    os.makedirs(out, exist_ok=True)
    for i, f in enumerate(range(sc.frame_start, sc.frame_end + 1, step)):
        sc.frame_set(f)
        sc.camera = camera_at(f)
        sc.render.filepath = os.path.join(out, f"f_{f:05d}.png")
        bpy.ops.render.render(write_still=True)


def render_stills(out, tl):
    sc = bpy.context.scene
    os.makedirs(out, exist_ok=True)
    for s in tl.shots:
        a, b = tl.range(s["id"])
        f = (a + b) // 2
        sc.frame_set(f)
        sc.camera = camera_at(f)
        sc.render.filepath = os.path.join(out, f"{s['id']}.png")
        bpy.ops.render.render(write_still=True)


def dump_shots(out, n, mod, tl):
    os.makedirs(out, exist_ok=True)
    data = dict(scene=n, title=mod.TITLE, fps=lib.FPS, step=lib.STEP, frames=tl.end_frame, shots=[])
    for s in tl.shots:
        a, b = tl.range(s["id"])
        data["shots"].append(dict(s, start=a, end=b))
    with open(os.path.join(out, "shots.json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)


def main():
    n, render_dir, stills_dir, res = SCENE, None, None, 854
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if "--scene" in args:
            n = int(args[args.index("--scene") + 1])
        if "--render" in args:
            render_dir = args[args.index("--render") + 1]
        if "--stills" in args:
            stills_dir = args[args.index("--stills") + 1]
        if "--res" in args:
            res = int(args[args.index("--res") + 1])
    mod, tl = build(n)
    setup_output(res)
    print(f"[kaerine] SC{n} built: {len(tl.shots)} shots, {tl.end_frame} frames")
    if stills_dir:
        dump_shots(stills_dir, n, mod, tl)
        render_stills(stills_dir, tl)
    if render_dir:
        dump_shots(render_dir, n, mod, tl)
        render_frames(render_dir, lib.STEP)


if __name__ == "__main__":
    main()
