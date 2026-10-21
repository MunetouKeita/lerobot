"""自作スイートの各シーンと、各プロンプト条件の指示文をセットで示す確認用の資料を作る（評価の前の確認用）。

- scenes.png: 各タスクの初期状態（agentview と真上）。掴む対象を赤丸で示す
- prompts.md: タスクごとに、全条件（settings.PROMPT_CONDITIONS）の指示文

    uv run python vla3dsg/scripts/show_conditions.py --suite vla3dsg_goal --out zeroshot/conditions
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from robosuite.utils.camera_utils import get_camera_transform_matrix, project_points_from_world_to_camera  # noqa: E402

from vla3dsg.demos.scripted import body_pos, settle  # noqa: E402
from vla3dsg.prompting.prompt_condition import compose_prompt  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402

CAMERAS = ["agentview", "birdview"]
SIZE = 360


def mark(img: np.ndarray, env: OffScreenRenderEnv, cam: str, point: np.ndarray) -> Image.Image:
    im = Image.fromarray(np.ascontiguousarray(img[::-1, ::-1]))
    r, c = project_points_from_world_to_camera(point[None], get_camera_transform_matrix(env.env.sim, cam, SIZE, SIZE), SIZE, SIZE)[0]
    # 表示は上下左右を反転しているが、投影の縦方向はすでに画像の向きに合っているため、横だけ反転する
    x, y = SIZE - 1 - c, r
    ImageDraw.Draw(im).ellipse([x - 26, y - 26, x + 26, y + 26], outline=(255, 0, 0), width=4)
    return im


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="vla3dsg_goal")
    parser.add_argument("--out", required=True, help="results/ 以下の保存先")
    parser.add_argument("--init-state", type=int, default=0)
    args = parser.parse_args()

    suite_dir = settings.CUSTOM_TASKS_DIR / args.suite
    spec = json.loads((suite_dir / "tasks.json").read_text())
    font, small = ImageFont.truetype(settings.DEMO_FONT_PATH, 24), ImageFont.truetype(settings.DEMO_FONT_PATH, 20)
    rows, md = [], [f"# {args.suite} のシーンと指示文（初期状態 {args.init_state}）", ""]
    for task_id, task in enumerate(spec["tasks"]):
        env = OffScreenRenderEnv(
            bddl_file_name=str(suite_dir / task["bddl_file"]), camera_names=CAMERAS, camera_heights=SIZE, camera_widths=SIZE
        )
        env.reset()
        env.set_init_state(torch.load(suite_dir / task["init_states_file"], weights_only=False)[args.init_state])
        obs = settle(env)
        e = env.env
        sg = build_scene_graph(e)
        target_id = next(i for i in e.obj_of_interest if i in e.objects_dict)
        title = f"task {task_id}: {settings.SCENE_LABELS.get(task['name'], task['name'])}"
        md += [f"## {title}", "", f"対象: {sg.target}（scenes.png の赤丸）", "", "| 条件 | 指示文 |", "|---|---|"]
        md += [f"| {k} | {compose_prompt(task['language'], k, sg, e)} |" for k in settings.PROMPT_CONDITIONS]
        md.append("")

        tiles = []
        for cam in CAMERAS:
            im = mark(obs[f"{cam}_image"], env, cam, body_pos(env, target_id))
            ImageDraw.Draw(im).text((6, 4), cam, fill=(255, 255, 0), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
            tiles.append(np.array(im))
        head = Image.new("RGB", (len(CAMERAS) * SIZE, 44), (255, 255, 255))
        ImageDraw.Draw(head).text((8, 8), f"{title}　対象: 赤丸（{sg.target}）", fill=(0, 0, 0), font=font)
        rows.append(np.concatenate([np.array(head), np.concatenate(tiles, 1)], 0))
        env.close()

    # 2 列に並べる
    if len(rows) % 2:
        rows.append(np.full_like(rows[0], 255))
    grid = np.concatenate([np.concatenate(rows[k : k + 2], 1) for k in range(0, len(rows), 2)], 0)
    out = settings.RESULTS_DIR / args.out
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(grid).save(out / "scenes.png")
    (out / "prompts.md").write_text("\n".join(md))
    print("\n".join(md))
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
