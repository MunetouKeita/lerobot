"""複数の動画を、ラベルを付けて格子状に並べた 1 本の比較動画にする（ゼミ・報告用）。

短い動画は最後のフレームを止めて、いちばん長い動画に合わせる。ラベルは各動画の上に表示する。

    uv run python vla3dsg/scripts/make_comparison_video.py --out results/seminar/xxx/videos/compare.mp4 --cols 3 \\
        --title "実験1: libero_spatial task 7 episode 4" --crop agentview \\
        --video "A 元の指示文のみ（成功）=results/exp1/libero_spatial_n5/A/videos/libero_spatial_7/eval_episode_4.mp4" ...

パスは vla3dsg/ からの相対パス。--crop agentview は、run_eval.py の動画（左が agentview、右が手首カメラ）の左半分だけを使う。
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

import imageio.v3 as iio  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

LABEL_H = 40
TITLE_H = 48


def text_bar(width: int, height: int, text: str, size: int) -> np.ndarray:
    """白地に黒の 1 行の文字。幅に収まらなければ文字を小さくする。"""
    im = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(settings.DEMO_FONT_PATH, size)
    while size > 10 and draw.textlength(text, font=font) > width - 16:
        size -= 1
        font = ImageFont.truetype(settings.DEMO_FONT_PATH, size)
    draw.text((8, (height - size) // 2 - 2), text, fill=(0, 0, 0), font=font)
    return np.array(im)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="出力先（vla3dsg/ からの相対パス）")
    parser.add_argument("--video", action="append", required=True, help="<ラベル>=<動画のパス>（並べる順に複数）")
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--title", default="")
    parser.add_argument("--crop", choices=["none", "agentview"], default="none")
    parser.add_argument("--fps", type=int, default=settings.LIBERO_CONTROL_FPS)
    args = parser.parse_args()

    clips = []
    for spec in args.video:
        label, path = spec.split("=", 1)
        frames = iio.imread(settings.VLA3DSG_DIR / path, plugin="pyav")
        if args.crop == "agentview":
            frames = frames[:, :, : frames.shape[2] // 2]
        clips.append((label, frames))
    h, w = clips[0][1].shape[1:3]
    n = max(len(f) for _, f in clips)
    rows = (len(clips) + args.cols - 1) // args.cols
    labels = [text_bar(w, LABEL_H, label, 20) for label, _ in clips]
    blank = np.full((h + LABEL_H, w, 3), 255, np.uint8)
    title = text_bar(w * args.cols, TITLE_H, args.title, 26) if args.title else None

    out = settings.VLA3DSG_DIR / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    video = []
    for t in range(n):
        tiles = [np.concatenate([labels[i], np.asarray(Image.fromarray(f[min(t, len(f) - 1)]).resize((w, h)))], 0) for i, (_, f) in enumerate(clips)]
        tiles += [blank] * (rows * args.cols - len(tiles))
        grid = np.concatenate([np.concatenate(tiles[r * args.cols : (r + 1) * args.cols], 1) for r in range(rows)], 0)
        video.append(np.concatenate([title, grid], 0) if title is not None else grid)
    iio.imwrite(out, np.stack(video), fps=args.fps, codec="libx264", plugin="pyav")
    print(f"saved: {out}（{n} フレーム、{len(clips)} 本）")


if __name__ == "__main__":
    main()
