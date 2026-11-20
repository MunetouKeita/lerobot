"""複数の評価動画を、短いキャプションと結果を付けて横に並べた比較動画にする（ゼミ・報告用）。

並べ方はレイアウトの JSON で指定する。動画はまとまり（group）ごとに色付きの枠で囲み、枠の上に見出しを付ける。
各動画の下にキャプションを付け、動画が終わった時点で結果（成功・失敗）を表示する。短い動画は最後の
フレームを止めて、いちばん長い動画に合わせる。最後の約 2 秒は、各動画の右上に結果のバッジ（成功 ○・失敗 ×）を出す。

色は発表資料の配色に合わせ、意味を固定する（settings.SEMINAR_COLORS）。まとまりの color には、提案・注目する条件
（SG あり、公式デモも混ぜる、指示どおりに動いた例）は "#85023E"（九大カラー）、比較・ベースライン（追加学習なし、
SG なし、自作デモだけ、指示に従わない例）は "#6B7280"（灰）を使う。結果の文字とバッジは成功が九大カラー、失敗が灰。

動画に "target": {"suite": ..., "task_id": ..., "episode": ...} を付けると、そのタスクの初期状態（エピソード番号と
同じ番号）から正解の物体（BDDL の :obj_of_interest の最初の物体）の位置を画像上に投影し、最初のフレームから
ロボットが掴みに来るまで（物体のまわりの画素が最初のフレームから大きく変わるまで）点線の丸で囲む。

    uv run python vla3dsg/scripts/make_comparison_video.py --layout results/seminar/2026-10-15/layouts/exp1.json

レイアウトの例（パスは vla3dsg/ からの相対パス）:

    {"out": "results/seminar/2026-10-15/videos/exp1.mp4", "title": "...", "crop": "agentview",
     "groups": [{"label": "SG なし", "color": "#6B7280",
                 "videos": [{"caption": "＋SG", "result": "成功", "path": "results/zeroshot/shuffle/base_short/videos/.../eval_episode_4.mp4",
                             "target": {"suite": "vla3dsg_goal", "task_id": 1, "episode": 4}}]}]}

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
COLORS = settings.SEMINAR_COLORS
RESULT_COLORS = {"成功": COLORS["proposed"], "失敗": COLORS["baseline"]}
RESULT_MARKS = {"成功": "○", "失敗": "×"}
BADGE_R, BADGE_S = 22, 2.0  # 結果のバッジの半径（px）、出す長さ（秒）
TARGET_R, TARGET_DIFF = 30, 30.0  # 正解の物体の丸の半径（px）、掴みに来たとみなす画素の変化（平均の差、0〜255）


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(settings.DEMO_FONT_PATH, size)


def load(path: str, crop: str) -> list[Image.Image]:
    frames = iio.imread(settings.VLA3DSG_DIR / path, plugin="pyav")
    if crop == "agentview":
        frames = frames[:, LABEL_CROP:, : frames.shape[2] // 2]
    elif crop == "left":
        frames = frames[:, :, : frames.shape[2] // 2]
    return [Image.fromarray(f).resize((TILE, TILE)) for f in frames]


def target_pixel(target: dict, size: int) -> tuple[float, float]:
    """タスクの初期状態での正解の物体の位置を、run_eval.py の動画（生画像の上下左右を反転）の size × size の画像上の (x, y) にする。"""
    import re

    import torch
    from libero.libero.envs import OffScreenRenderEnv
    from robosuite.utils.camera_utils import get_camera_transform_matrix, project_points_from_world_to_camera

    suite_dir = settings.CUSTOM_TASKS_DIR / target["suite"]
    task = json.loads((suite_dir / "tasks.json").read_text())["tasks"][target["task_id"]]
    bddl = suite_dir / task["bddl_file"]
    obj = re.search(r"\(:obj_of_interest\s+(\S+)", bddl.read_text()).group(1)
    states = torch.load(suite_dir / task["init_states_file"], weights_only=False)  # nosec B614
    env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_heights=size, camera_widths=size)
    env.reset()
    env.set_init_state(states[target["episode"] % len(states)])
    e = env.env
    pos = np.array(e.sim.data.body_xpos[e.sim.model.body_name2id(e.get_object(obj).root_body)])
    world_to_px = get_camera_transform_matrix(e.sim, "agentview", size, size)
    row, col = project_points_from_world_to_camera(pos[None], world_to_px, size, size)[0]
    env.close()
    # robosuite の投影は上下を反転した生画像の向きで返すため、動画の向きに合わせるには左右だけを反転する
    return size - 1 - float(col), float(row)


def tile_xy(xy: tuple[float, float], size: int, crop: str) -> tuple[float, float]:
    """元の動画の agentview（size × size）上の位置を、切り出して TILE × TILE にした画像上の位置にする。"""
    x, y = xy
    if crop == "agentview":
        return x * TILE / size, (y - LABEL_CROP) * TILE / (size - LABEL_CROP)
    return x * TILE / size, y * TILE / size


def grasp_frame(frames: list[Image.Image], xy: tuple[float, float]) -> int:
    """正解の物体のまわりの画素が最初のフレームから大きく変わった（ロボットが掴みに来た）フレーム。来なければ最後。"""
    x, y = (int(round(v)) for v in xy)
    box = (max(x - TARGET_R, 0), max(y - TARGET_R, 0), min(x + TARGET_R, TILE), min(y + TARGET_R, TILE))
    first = np.asarray(frames[0].crop(box), dtype=np.float32)
    for t, f in enumerate(frames):
        if np.abs(np.asarray(f.crop(box), dtype=np.float32) - first).mean() > TARGET_DIFF:
            return t
    return len(frames)


def dashed_circle(draw: ImageDraw.ImageDraw, xy: tuple[float, float], r: int, color: str, n: int = 16) -> None:
    x, y = xy
    for i in range(n):
        start = 360 / n * i
        draw.arc([x - r, y - r, x + r, y + r], start, start + 360 / n * 0.6, fill=color, width=4)


def badge(draw: ImageDraw.ImageDraw, tx: int, ty: int, result: str) -> None:
    cx, cy = tx + TILE - BADGE_R - 8, ty + BADGE_R + 8
    draw.ellipse([cx - BADGE_R, cy - BADGE_R, cx + BADGE_R, cy + BADGE_R], fill=RESULT_COLORS[result], outline="white", width=2)
    draw.text((cx, cy), RESULT_MARKS[result], font=font(28), fill="white", anchor="mm")


def centered(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, text: str, f: ImageFont.FreeTypeFont, fill) -> None:
    draw.text(((x0 + x1 - draw.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True, help="レイアウトの JSON（vla3dsg/ からの相対パス）")
    args = parser.parse_args()
    layout = json.loads((settings.VLA3DSG_DIR / args.layout).read_text())

    groups = [[(v, load(v["path"], v.get("crop", layout.get("crop", "none")))) for v in g["videos"]] for g in layout["groups"]]
    n = max(len(frames) for g in groups for _, frames in g)
    n_total = n + int(settings.LIBERO_CONTROL_FPS * layout.get("hold_last_s", 2.0))
    n_badge = int(settings.LIBERO_CONTROL_FPS * BADGE_S)

    # 正解の物体の丸の位置と、出す長さ（位置が求められないときは付けない）
    circles = {}
    for g in groups:
        for v, frames in g:
            if "target" not in v:
                continue
            crop = v.get("crop", layout.get("crop", "none"))
            h, w = iio.improps(settings.VLA3DSG_DIR / v["path"], plugin="pyav").shape[1:3]
            size = h if crop in ("agentview", "left") else w
            try:
                xy = tile_xy(target_pixel(v["target"], size), size, crop)
            except Exception as err:  # noqa: BLE001
                print(f"丸を付けない（位置が求められない）: {v['path']}: {err}")
                continue
            if 0 <= xy[0] < TILE and 0 <= xy[1] < TILE:
                circles[id(v)] = (xy, grasp_frame(frames, xy))

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
        draw.text((GAP, 10), layout["title"], font=font(28), fill=COLORS["text"])
    tile_pos = []
    for (x0, x1), g, spec in zip(boxes, groups, layout["groups"]):
        color = spec.get("color", COLORS["baseline"])
        draw.rectangle([x0, top, x1 - 1, height - GAP - 1], outline=color, width=BORDER)
        centered(draw, x0, x1, title_h + 4, spec["label"], font(26), color)
        for i, (v, _) in enumerate(g):
            tx = x0 + BORDER + PAD + i * (TILE + GAP)
            ty = top + BORDER + PAD
            tile_pos.append((tx, ty))
            centered(draw, tx, tx + TILE, ty + TILE + 6, v["caption"], font(24), COLORS["text"])

    clips = [c for g in groups for c in g]
    video = []
    for t in range(n_total):
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        for (tx, ty), (v, frames) in zip(tile_pos, clips):
            frame.paste(frames[min(t, len(frames) - 1)], (tx, ty))
            if id(v) in circles and t < circles[id(v)][1]:
                (cx, cy), _ = circles[id(v)]
                dashed_circle(d, (tx + cx, ty + cy), TARGET_R, COLORS["proposed"])
            if t >= len(frames) - 1:  # 動画が終わったら結果を出す
                centered(d, tx, tx + TILE, ty + TILE + 34, v["result"], font(24), RESULT_COLORS[v["result"]])
            if t >= n_total - n_badge:
                badge(d, tx, ty, v["result"])
        video.append(np.asarray(frame))

    out = settings.VLA3DSG_DIR / layout["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    # libx264 は幅・高さが偶数である必要がある
    arr = np.stack(video)[:, : height // 2 * 2, : width // 2 * 2]
    iio.imwrite(out, arr, fps=settings.LIBERO_CONTROL_FPS, codec="libx264", plugin="pyav")
    print(f"saved: {out}（{len(video)} フレーム、{len(clips)} 本）")


if __name__ == "__main__":
    main()
