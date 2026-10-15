# ECHO プリビズ

## S4「千本鳥居の疾走」 `s4_torii_run.py`

Shot 4-1〜4-5（18秒・24fps・432フレーム）のプリビズを自動生成する Blender スクリプト。

| Shot | フレーム | レンズ | 内容 |
|---|---|---|---|
| 4-1 | 1–72 | 24mm | 低い位置から背中を追従 |
| 4-2 | 73–168 | 85mm | 鳥居の外から真横で並走、手前に彼岸花のボケ |
| 4-3 | 169–264 | 16mm | 正面から後退しながら表情 |
| 4-4 | 265–360 | 24→16mm | 主観で加速、奥に白い光 |
| 4-5 | 361–432 | 24mm | 急上昇して鳥居の列を俯瞰 |

鳥居は進むにつれて朱 → 白に褪せる（`FADE_FROM` / `FADE_TO` で調整）。

### 使い方
1. Blender で新規ファイルを開く（5.1 で確認済み、4.2 以降も動く想定）
2. Scripting タブでスクリプトを開いて実行
3. タイムラインのマーカーで各ショットのカメラに自動で切り替わる
4. `RENDER_MODE` を `GREY` / `DEPTH` / `COLOR` に変えて Ctrl+F12 で書き出し

コマンドラインから：
```
blender -b -P s4_torii_run.py -- --mode grey --render
blender -b -P s4_torii_run.py -- --mode depth --render
```

- `GREY`：動画→動画 / モーション参照用のグレーレンダー
- `DEPTH`：深度マップ（手前=白）。ControlNet 等の depth 入力用
- `COLOR`：EEVEE の簡易カラー

### 調整ポイント（ファイル先頭の設定）
- 走る速さ：`SPEED_START` / `SPEED_END`
- ショットの尺・レンズ：`SHOTS`
- 参道のうねり：`CURVE_AMP` / `CURVE_WAVELENGTH`
- カメラ位置：`shot_pose()` 内の各ショット

`s4_contact_sheet.png` はテストレンダーのコマ（各ショット2枚）。
