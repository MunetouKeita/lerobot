"""評価結果の動画をつなぎ、指示文と成功率（成功回数/実行数）のテロップを付けたデモ動画を作る。

run_eval.py の結果（results/<name>/summary.json）と動画（outputs/eval/<name>/videos/）を使う。

    uv run python vla3dsg/scripts/make_demo_video.py --name samples/four_suites_t0_t5_n2
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

import av  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

LINE_H = 30
MAX_INSTRUCTION_LINES = 2
BAND_H = 12 + LINE_H * (MAX_INSTRUCTION_LINES + 1)
MARGIN = 10


def wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, max_lines: int) -> list[str]:
    """単語単位で折り返す。行数を超える分は最終行の末尾を "..." にする。"""
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines: list[str] = []
    for word in text.split():
        if lines and draw.textlength(f"{lines[-1]} {word}", font=font) <= max_w:
            lines[-1] = f"{lines[-1]} {word}"
        else:
            lines.append(word)
    if len(lines) > max_lines:
        last = " ".join(lines[max_lines - 1 :])
        while draw.textlength(last + "...", font=font) > max_w:
            last = last[:-1]
        lines = [*lines[: max_lines - 1], last + "..."]
    return lines


def caption(frame: np.ndarray, lines: list[tuple[str, tuple[int, int, int]]], font: ImageFont.FreeTypeFont) -> np.ndarray:
    h, w = frame.shape[:2]
    canvas = Image.new("RGB", (w, h + BAND_H), (0, 0, 0))
    canvas.paste(Image.fromarray(frame), (0, 0))
    draw = ImageDraw.Draw(canvas)
    for i, (text, color) in enumerate(lines):
        draw.text((MARGIN, h + 6 + i * LINE_H), text, fill=color, font=font)
    return np.asarray(canvas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="run_eval.py の --name")
    args = parser.parse_args()

    summary = json.loads((settings.RESULTS_DIR / args.name / "summary.json").read_text())
    videos_dir = settings.OUTPUTS_DIR / "eval" / args.name / "videos"
    out_path = videos_dir / "demo_with_captions.mp4"
    font = ImageFont.truetype(settings.DEMO_FONT_PATH, 20)
    fps = settings.LIBERO_CONTROL_FPS
    n_hold = int(settings.DEMO_HOLD_LAST_S * fps)

    with av.open(str(out_path), mode="w") as out:
        stream = None
        for task in summary["per_task"]:
            successes = task["successes"]
            rate = f"成功率 {sum(successes)}/{len(successes)}（{task['suite']} task {task['task_id']}）"
            for ep, ok in enumerate(successes):
                video = videos_dir / f"{task['suite']}_{task['task_id']}" / f"eval_episode_{ep}.mp4"
                frame_w = 2 * settings.LIBERO_OBS_SIZE
                instruction = wrap(f"指示: {task['instruction']}", font, frame_w - 2 * MARGIN, MAX_INSTRUCTION_LINES)
                instruction += [""] * (MAX_INSTRUCTION_LINES - len(instruction))
                lines = [
                    *((text, (255, 255, 255)) for text in instruction),
                    (
                        f"{rate}    エピソード {ep + 1}/{len(successes)}: {'成功' if ok else '失敗'}",
                        (120, 230, 130) if ok else (250, 110, 110),
                    ),
                ]
                with av.open(str(video)) as src:
                    frames = [f.to_ndarray(format="rgb24") for f in src.decode(video=0)]
                frames += [frames[-1]] * n_hold
                for img in frames:
                    img = caption(img, lines, font)
                    if stream is None:
                        stream = out.add_stream("libx264", rate=fps)
                        stream.height, stream.width = img.shape[:2]
                        stream.pix_fmt = "yuv420p"
                    for packet in stream.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
                        out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)

    total = f"{summary['n_success']}/{summary['n_episodes']}"
    print(f"saved: {out_path}（全体の成功率 {total}）")


if __name__ == "__main__":
    main()
