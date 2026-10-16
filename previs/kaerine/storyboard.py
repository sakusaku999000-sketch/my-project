"""絵コンテ (シーンごとの縦長 PNG) と STORYBOARD.md を作る

python3 storyboard.py RENDER_ROOT OUT_DIR

RENDER_ROOT/scN/stills/ に build.py --stills の出力 (ショットIDの PNG と shots.json) がある前提。
"""

import json
import os
import sys

from PIL import Image, ImageDraw

from compose import font

W = 1280
TH_W, TH_H = 512, 288
PAD = 24


def wrap(d, text, f, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > width:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def fmt(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def scene_sheet(data, stills, out, t0):
    f_h1, f_b, f_t, f_s = font(34, True), font(22, True), font(20), font(18)
    rows = []
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for s in data["shots"]:
        text = []
        text.append(("b", f"{s['id']}   {s['dur']}秒   {s.get('size', '')}   {s.get('move', '')}"))
        if s.get("desc"):
            text += [("t", ln) for ln in wrap(tmp, s["desc"], f_t, W - TH_W - PAD * 3)]
        for t, who, line in s.get("lines", []):
            text += [("d", ln) for ln in wrap(tmp, f"{t:.1f}s  {who}「{line}」", f_t, W - TH_W - PAD * 3)]
        if s.get("sfx"):
            text.append(("s", "SE: " + "、".join(f"{k}@{t:.1f}s" for t, k in s["sfx"])))
        if s.get("card"):
            text.append(("s", f"テロップ: {s['card']}"))
        h = max(TH_H, 34 + 30 * len(text)) + PAD
        rows.append((s, text, h))
    head_h = 90
    H = head_h + sum(r[2] for r in rows) + PAD
    im = Image.new("RGB", (W, H), (246, 244, 240))
    d = ImageDraw.Draw(im)
    dur = data["frames"] / data["fps"]
    d.text((PAD, 24), f"SCENE {data['scene']}｜{data['title']}", font=f_h1, fill=(20, 20, 20))
    span = f"{fmt(t0)}〜{fmt(t0 + dur)}（{dur:.0f}秒・{len(data['shots'])}ショット）"
    d.text((W - PAD - d.textlength(span, font=f_t), 36), span, font=f_t, fill=(90, 90, 90))
    y = head_h
    for s, text, h in rows:
        p = os.path.join(stills, f"{s['id']}.png")
        if os.path.exists(p):
            th = Image.open(p).convert("RGB").resize((TH_W, TH_H))
            im.paste(th, (PAD, y))
        d.rectangle((PAD, y, PAD + TH_W, y + TH_H), outline=(60, 60, 60), width=2)
        ty = y + 4
        for kind, ln in text:
            f, c = {"b": (f_b, (20, 20, 20)), "t": (f_t, (50, 50, 50)), "d": (f_t, (30, 70, 140)),
                    "s": (f_s, (130, 90, 40))}[kind]
            d.text((PAD * 2 + TH_W, ty), ln, font=f, fill=c)
            ty += 34 if kind == "b" else 30
        y += h
        d.line((PAD, y - PAD / 2, W - PAD, y - PAD / 2), fill=(210, 205, 198), width=1)
    im.save(out)
    return dur


def main():
    root, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    t = 0.0
    md = ["# 『返り音』絵コンテ（プリビズ版）", "",
          "脚本 v1.0 をもとに、Blender のプリビズから各ショットの中間フレームを切り出したもの。",
          "グレーのマネキン・簡易セットによる構図とカメラワークの確認用です。", ""]
    for n in range(1, 10):
        stills = os.path.join(root, f"sc{n}", "stills")
        js = os.path.join(stills, "shots.json")
        if not os.path.exists(js):
            continue
        data = json.load(open(js, encoding="utf-8"))
        name = f"SC{n}_storyboard.png"
        dur = scene_sheet(data, stills, os.path.join(out, name), t)
        md += [f"## SCENE {n}｜{data['title']}（{fmt(t)}〜{fmt(t + dur)}）", "", f"![SC{n}]({name})", ""]
        t += dur
    md += [f"合計 {fmt(t)}", ""]
    with open(os.path.join(out, "STORYBOARD.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(md))


if __name__ == "__main__":
    main()
