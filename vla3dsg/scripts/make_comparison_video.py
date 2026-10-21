"""複数の評価動画を、短いキャプションと結果を付けて横に並べた比較動画にする（ゼミ・報告用）。

並べ方はレイアウトの JSON で指定する。動画はまとまり（group）ごとに色付きの枠で囲み、枠の上に見出しを付ける。
各動画の下にキャプションを付け、動画が終わった時点で結果（成功・失敗。失敗は赤）を表示する。短い動画は最後の
フレームを止めて、いちばん長い動画に合わせる。

    uv run python vla3dsg/scripts/make_comparison_video.py --layout results/seminar/2026-10-15/layouts/exp1.json

レイアウトの例（パスは vla3dsg/ からの相対パス）:

    {"out": "results/seminar/2026-10-15/videos/exp1.mp4", "title": "...", "crop": "agentview",
     "groups": [{"label": "SG なし", "color": "#555555",
                 "videos": [{"caption": "SG から作った指示文", "result": "成功", "path": "results/zeroshot/shuffle/sg_command/videos/.../eval_episode_4.mp4"}]}]}

crop が "agentview" のとき、run_eval.py の動画（左が agentview、右が手首カメラ）の左半分だけを使い、上端に焼き込まれた
カメラ名を切り落とす。"left" のときは、左半分だけを使う（カメラ名のない動画。例: generate_demos.py --check の動画）。
crop は動画ごとにも指定できる（videos の要素の "crop"）。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

import imageio.v3 as iio  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

TILE = 320  # 各動画の幅・高さ（px）
LABEL_CROP = 20  # run_eval.py の動画の上端に焼き込まれたカメラ名の高さ（px）
GAP, PAD, BORDER = 12, 10, 4  # 動画の間隔、枠の内側の余白、枠の線の太さ
TITLE_H, GROUP_H, CAPTION_H = 52, 40, 64
RESULT_COLORS = {"成功": (20, 20, 20), "失敗": (220, 30, 30)}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(settings.DEMO_FONT_PATH, size)


def load(path: str, crop: str) -> list[Image.Image]:
    frames = iio.imread(settings.VLA3DSG_DIR / path, plugin="pyav")
    if crop == "agentview":
        frames = frames[:, LABEL_CROP:, : frames.shape[2] // 2]
    elif crop == "left":
        frames = frames[:, :, : frames.shape[2] // 2]
    return [Image.fromarray(f).resize((TILE, TILE)) for f in frames]


def centered(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, text: str, f: ImageFont.FreeTypeFont, fill) -> None:
    draw.text(((x0 + x1 - draw.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True, help="レイアウトの JSON（vla3dsg/ からの相対パス）")
    args = parser.parse_args()
    layout = json.loads((settings.VLA3DSG_DIR / args.layout).read_text())

    groups = [[(v, load(v["path"], v.get("crop", layout.get("crop", "none")))) for v in g["videos"]] for g in layout["groups"]]
    n = max(len(frames) for g in groups for _, frames in g)

    # 各まとまりの枠の位置
    boxes, x = [], GAP
    for g in groups:
        w = 2 * (PAD + BORDER) + len(g) * TILE + (len(g) - 1) * GAP
        boxes.append((x, x + w))
        x += w + GAP
    width = x
    title_h = TITLE_H if layout.get("title") else 0
    top = title_h + GROUP_H
    height = top + 2 * (PAD + BORDER) + TILE + CAPTION_H + GAP

    # 動画以外の部分（背景・タイトル・枠・見出し・キャプション）
    base = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(base)
    if layout.get("title"):
        draw.text((GAP, 10), layout["title"], font=font(28), fill=(0, 0, 0))
    tile_pos = []
    for (x0, x1), g, spec in zip(boxes, groups, layout["groups"]):
        color = spec.get("color", "#555555")
        draw.rectangle([x0, top, x1 - 1, height - GAP - 1], outline=color, width=BORDER)
        centered(draw, x0, x1, title_h + 4, spec["label"], font(26), color)
        for i, (v, _) in enumerate(g):
            tx = x0 + BORDER + PAD + i * (TILE + GAP)
            ty = top + BORDER + PAD
            tile_pos.append((tx, ty))
            centered(draw, tx, tx + TILE, ty + TILE + 6, v["caption"], font(24), (0, 0, 0))

    clips = [c for g in groups for c in g]
    video = []
    for t in range(n):
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        for (tx, ty), (v, frames) in zip(tile_pos, clips):
            frame.paste(frames[min(t, len(frames) - 1)], (tx, ty))
            if t >= len(frames) - 1:  # 動画が終わったら結果を出す
                centered(d, tx, tx + TILE, ty + TILE + 34, v["result"], font(24), RESULT_COLORS[v["result"]])
        video.append(np.asarray(frame))
    for _ in range(int(settings.LIBERO_CONTROL_FPS * layout.get("hold_last_s", 2.0))):
        video.append(video[-1])

    out = settings.VLA3DSG_DIR / layout["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    # libx264 は幅・高さが偶数である必要がある
    arr = np.stack(video)[:, : height // 2 * 2, : width // 2 * 2]
    iio.imwrite(out, arr, fps=settings.LIBERO_CONTROL_FPS, codec="libx264", plugin="pyav")
    print(f"saved: {out}（{len(video)} フレーム、{len(clips)} 本）")


if __name__ == "__main__":
    main()
