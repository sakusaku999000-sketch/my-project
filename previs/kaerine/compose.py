"""『返り音』プリビズの仕上げ: レンダー連番 → 字幕・ショット情報・効果音付きの動画

python3 compose.py RENDER_ROOT OUT_DIR

RENDER_ROOT/scN/frames/ に build.py --render の出力 (f_XXXXX.png と shots.json) がある前提。
OUT_DIR に scN.mp4 と、全シーンをつないだ kaerine_previs_full.mp4 を書き出す。
必要なもの: Python 3, numpy, Pillow, ffmpeg
"""

import glob
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 44100
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
]
BOLD_CANDIDATES = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "C:/Windows/Fonts/YuGothB.ttc"]


def font(size, bold=False):
    for p in (BOLD_CANDIDATES if bold else []) + FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size, index=0)
    return ImageFont.load_default()


# ---------------------------------------------------------------- 効果音 (合成)
rng = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx_tap():
    t = _t(0.18)
    knock = np.sin(2 * np.pi * 820 * t) * np.exp(-t / 0.025) + 0.6 * np.sin(2 * np.pi * 1650 * t) * np.exp(-t / 0.012)
    noise = _lowpass(rng.normal(0, 1, len(t)), 6) * np.exp(-t / 0.008)
    return 0.55 * (knock + 0.8 * noise)


def sfx_ring():
    t = _t(3.0)
    buzz = np.sign(np.sin(2 * np.pi * 160 * t)) * 0.5 + np.sin(2 * np.pi * 320 * t) * 0.3
    gate = ((t % 1.0) < 0.55).astype(float)
    return 0.18 * _lowpass(buzz * gate, 20)


def sfx_rain(sec=5.0):
    t = _t(sec)
    n = _lowpass(rng.normal(0, 1, len(t)), 3) - _lowpass(rng.normal(0, 1, len(t)), 60)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (sec - t) / 0.5)
    return 0.12 * n * env


def sfx_crash():
    t = _t(1.6)
    n = _lowpass(rng.normal(0, 1, len(t)), 30) * np.exp(-t / 0.35)
    thump = np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.25)
    return 0.7 * (n * 2.5 + thump)


def sfx_bell():
    t = _t(4.5)
    parts = [(196, 1.0, 3.0), (392 * 1.01, 0.6, 2.2), (588 * 0.99, 0.4, 1.5), (1046, 0.25, 0.8), (1530, 0.15, 0.5)]
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in parts)
    return 0.35 * s * np.minimum(1, t / 0.005)


def sfx_rumble():
    t = _t(3.0)
    n = _lowpass(_lowpass(rng.normal(0, 1, len(t)), 120), 120)
    env = np.sin(np.pi * t / 3.0)
    return 4.0 * n * env


def sfx_voices():
    t = _t(6.5)
    out = np.zeros(len(t))
    for i in range(7):
        c = rng.uniform(0.3, 5.5)
        env = np.exp(-((t - c) / 0.45) ** 2)
        tone = np.sin(2 * np.pi * rng.uniform(380, 620) * t + 3 * np.sin(2 * np.pi * 5 * t))
        out += env * (0.25 * tone + _lowpass(rng.normal(0, 1, len(t)), 8))
    return 0.12 * out


def sfx_chime():
    t = _t(3.0)
    out = np.zeros(len(t))
    for i, f in enumerate((880, 1109, 1319, 1760, 2217)):
        st = i * 0.25
        tt = np.clip(t - st, 0, None)
        out += (t >= st) * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.9)
    return 0.18 * out


def sfx_wind():
    t = _t(4.0)
    n = _lowpass(rng.normal(0, 1, len(t)), 40)
    env = np.sin(np.pi * t / 4.0) ** 2
    return 1.2 * n * env


SFX = dict(tap=sfx_tap, ring=sfx_ring, rain=sfx_rain, crash=sfx_crash, bell=sfx_bell, rumble=sfx_rumble,
           voices=sfx_voices, chime=sfx_chime, wind=sfx_wind)


def scene_audio(data, path):
    fps = data["fps"]
    total = data["frames"] / fps
    buf = np.zeros(int((total + 5) * SR))
    for s in data["shots"]:
        t0 = (s["start"] - 1) / fps
        for t, kind in s.get("sfx", []):
            clip = SFX[kind]()
            i = int((t0 + t) * SR)
            buf[i:i + len(clip)] += clip[:len(buf) - i]
    buf = buf[:int(total * SR)]
    buf = np.clip(buf, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32000).astype(np.int16).tobytes())


# ---------------------------------------------------------------- 画面の重ね
def fmt_time(sec):
    return f"{int(sec // 60):02d}:{sec % 60:04.1f}"


def active_line(shot, t):
    lines = shot.get("lines", [])
    for i, (lt, who, text) in enumerate(lines):
        nxt = lines[i + 1][0] if i + 1 < len(lines) else shot["dur"]
        if lt <= t < min(nxt, lt + 3.6):
            return who, text
    return None


def overlay(img, data, shot, t_shot, t_global):
    W, H = img.size
    im = img.convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    # フェード
    fade = shot.get("fade")
    if fade == "white" and t_shot > shot["dur"] - 1.4:
        a = int(255 * min(1, (t_shot - (shot["dur"] - 1.4)) / 1.2))
        d.rectangle((0, 0, W, H), fill=(255, 255, 255, a))
    if shot.get("fade_in") == "white" and t_shot < 1.2:
        a = int(255 * (1 - t_shot / 1.2))
        d.rectangle((0, 0, W, H), fill=(255, 255, 255, a))
    card = shot.get("card")
    if card:
        show = t_shot < 2.6 if card != "END" else t_shot > shot["dur"] - 2.0
        if show:
            d.rectangle((0, 0, W, H), fill=(0, 0, 0, 170))
            f = font(int(H * 0.09), bold=True)
            tw = d.textlength(card, font=f)
            d.text(((W - tw) / 2, H / 2 - H * 0.06), card, font=f, fill=(255, 255, 255))
    # 16:9 の画面全体を見せ、情報は半透明の帯に載せる
    small = font(max(11, int(H * 0.03)))
    strip = int(H * 0.065)
    d.rectangle((0, 0, W, strip), fill=(0, 0, 0, 120))
    head = f"SC{data['scene']} {data['title']}   |   {shot['id']}   {shot.get('size', '')}   {shot.get('move', '')}"
    ty = (strip - small.size) / 2 - 1
    d.text((12, ty), head, font=small, fill=(225, 225, 225))
    tc = fmt_time(t_global)
    d.text((W - 12 - d.textlength(tc, font=small), ty), tc, font=small, fill=(225, 225, 225))
    if shot.get("silent"):
        tag = "（無音）"
        d.text((W - 12 - d.textlength(tag, font=small), H - strip), tag, font=small, fill=(230, 230, 230),
               stroke_width=2, stroke_fill=(0, 0, 0))
    line = active_line(shot, t_shot)
    if line:
        who, text = line
        s = f"{who}「{text}」" if who not in ("声", "電話", "澪の声") else f"（{who}）「{text}」"
        f = font(int(H * 0.042))
        while d.textlength(s, font=f) > W - 60 and f.size > 10:
            f = font(f.size - 1)
        tw = d.textlength(s, font=f)
        x, y = (W - tw) / 2, H - f.size * 2.2
        d.rectangle((x - 12, y - 6, x + tw + 12, y + f.size + 10), fill=(0, 0, 0, 140))
        d.text((x, y), s, font=f, fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0))
    return im


def compose_scene(scene_dir, out_dir, t_offset):
    data = json.load(open(os.path.join(scene_dir, "shots.json"), encoding="utf-8"))
    fps, step = data["fps"], data["step"]
    files = sorted(glob.glob(os.path.join(scene_dir, "f_*.png")))
    comp = os.path.join(out_dir, f"_comp_sc{data['scene']}")
    os.makedirs(comp, exist_ok=True)
    for i, fp in enumerate(files):
        f = int(os.path.basename(fp)[2:-4])
        shot = [s for s in data["shots"] if s["start"] <= f <= s["end"]]
        shot = shot[0] if shot else data["shots"][-1]
        im = overlay(Image.open(fp), data, shot, (f - shot["start"]) / fps, t_offset + (f - 1) / fps)
        im.save(os.path.join(comp, f"{i:05d}.png"))
    wav = os.path.join(out_dir, f"_sc{data['scene']}.wav")
    scene_audio(data, wav)
    mp4 = os.path.join(out_dir, f"sc{data['scene']}.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps / step), "-i",
                    os.path.join(comp, "%05d.png"), "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-r", str(fps / step), "-c:a", "aac", "-b:a", "128k", "-shortest", mp4], check=True)
    return mp4, data["frames"] / fps


def main():
    root, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    only = [int(x) for x in sys.argv[3:]] or list(range(1, 10))
    t = 0.0
    parts = []
    for n in range(1, 10):
        d = os.path.join(root, f"sc{n}", "frames")
        if not os.path.exists(os.path.join(d, "shots.json")):
            continue
        dur = json.load(open(os.path.join(d, "shots.json"), encoding="utf-8"))["frames"] / 24
        if n in only:
            mp4, _ = compose_scene(d, out, t)
            print("wrote", mp4)
        parts.append(os.path.join(out, f"sc{n}.mp4"))
        t += dur
    if len(parts) == 9 and all(os.path.exists(p) for p in parts):
        lst = os.path.join(out, "_concat.txt")
        with open(lst, "w") as fp:
            for p in parts:
                fp.write(f"file '{os.path.abspath(p)}'\n")
        full = os.path.join(out, "kaerine_previs_full.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        full], check=True)
        print("wrote", full)


if __name__ == "__main__":
    main()
