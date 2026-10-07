"""評価結果の動画をつなぎ、指示（日本語訳）と成功率（成功回数/実行数）のテロップを付けたデモ動画を作る。

各タスクの先頭から DEMO_EPISODES_PER_TASK 本だけを等倍で載せ、成功率は全エピソードの結果を表示する。

run_eval.py の結果（results/<name>/summary.json と results/<name>/videos/）を使う。

    uv run python vla3dsg/scripts/make_demo_video.py --name samples/four_suites_t0_t5_n2
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402
from vla3dsg.config.instructions_ja import INSTRUCTIONS_JA  # noqa: E402

import av  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

LINE_H = 32
MAX_INSTRUCTION_LINES = 2
BAND_H = 12 + LINE_H * (MAX_INSTRUCTION_LINES + 1)
MARGIN = 12


def wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, max_lines: int) -> list[str]:
    """1 文字単位で折り返す（日本語向け）。読点があればその直後で改行する。
    行数を超える分は最終行の末尾を "…" にする。"""
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = [""]
    for ch in text:
        if draw.textlength(lines[-1] + ch, font=font) > max_w:
            cut = lines[-1].rfind("、") + 1
            if cut > len(lines[-1]) // 2:
                lines[-1], rest = lines[-1][:cut], lines[-1][cut:]
            else:
                rest = ""
            lines.append(rest)
        lines[-1] += ch
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while draw.textlength(last + "…", font=font) > max_w:
            last = last[:-1]
        lines = [*lines[: max_lines - 1], last + "…"]
    return lines


def caption(frame: np.ndarray, lines: list[str], font: ImageFont.FreeTypeFont) -> np.ndarray:
    h, w = frame.shape[:2]
    canvas = Image.new("RGB", (w, h + BAND_H), (0, 0, 0))
    canvas.paste(Image.fromarray(frame), (0, 0))
    draw = ImageDraw.Draw(canvas)
    for i, text in enumerate(lines):
        draw.text((MARGIN, h + 6 + i * LINE_H), text, fill=(255, 255, 255), font=font)
    return np.asarray(canvas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="run_eval.py の --name")
    parser.add_argument("--episodes-per-task", type=int, default=settings.DEMO_EPISODES_PER_TASK)
    args = parser.parse_args()

    summary = json.loads((settings.RESULTS_DIR / args.name / "summary.json").read_text())
    videos_dir = settings.RESULTS_DIR / args.name / "videos"
    out_path = videos_dir / "demo_with_captions.mp4"
    font = ImageFont.truetype(settings.DEMO_FONT_PATH, 22)
    fps = settings.LIBERO_CONTROL_FPS
    n_hold = int(settings.DEMO_HOLD_LAST_S * fps)
    frame_w = 2 * settings.LIBERO_OBS_SIZE

    with av.open(str(out_path), mode="w") as out:
        stream = None
        for task in summary["per_task"]:
            successes = task["successes"]
            instruction = INSTRUCTIONS_JA.get(task["instruction"])
            if instruction is None:
                print(f"warning: 日本語訳がないため英語のまま表示する: {task['instruction']}")
                instruction = task["instruction"]
            lines = wrap(f"指示：{instruction}", font, frame_w - 2 * MARGIN, MAX_INSTRUCTION_LINES)
            lines += [""] * (MAX_INSTRUCTION_LINES - len(lines))
            lines.append(f"成功率：{sum(successes)}/{len(successes)}")
            for ep in range(min(args.episodes_per_task, len(successes))):
                video = videos_dir / f"{task['suite']}_{task['task_id']}" / f"eval_episode_{ep}.mp4"
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

    print(f"saved: {out_path}（全体の成功率 {summary['n_success']}/{summary['n_episodes']}）")


if __name__ == "__main__":
    main()
