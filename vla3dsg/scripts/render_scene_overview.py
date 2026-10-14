"""自作スイートの各タスクの初期状態を、ポリシーの入力の 2 視点と、確認用の 4 視点（真上・横・正面・斜め）で描画する。

    uv run python vla3dsg/scripts/render_scene_overview.py [--suite vla3dsg_hidden] [--init-state 0]

画像は custom_tasks/<suite>/previews/overview.png。
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

from vla3dsg.demos.scripted import settle  # noqa: E402

CAMERAS = {
    "agentview": "agentview (policy input)",
    "robot0_eye_in_hand": "wrist camera (policy input)",
    "birdview": "birdview (top)",
    "sideview": "sideview",
    "frontview": "frontview",
    "galleryview": "galleryview",
}
SIZE = 320


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="vla3dsg_hidden")
    parser.add_argument("--init-state", type=int, default=0)
    args = parser.parse_args()

    suite_dir = settings.CUSTOM_TASKS_DIR / args.suite
    spec = json.loads((suite_dir / "tasks.json").read_text())
    font = ImageFont.truetype(settings.DEMO_FONT_PATH, 18)
    rows = []
    for task_id, task in enumerate(spec["tasks"]):
        env = OffScreenRenderEnv(
            bddl_file_name=str(suite_dir / task["bddl_file"]), camera_names=list(CAMERAS), camera_heights=SIZE, camera_widths=SIZE
        )
        init_states = torch.load(suite_dir / task["init_states_file"], weights_only=False)
        env.reset()
        env.set_init_state(init_states[args.init_state])
        obs = settle(env)
        tiles = []
        for cam, label in CAMERAS.items():
            im = Image.fromarray(np.ascontiguousarray(obs[f"{cam}_image"][::-1, ::-1]))
            ImageDraw.Draw(im).text((6, 4), label, fill=(255, 255, 0), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
            tiles.append(np.array(im))
        row = np.concatenate(tiles, 1)
        head = Image.new("RGB", (row.shape[1], 34), (255, 255, 255))
        ImageDraw.Draw(head).text((8, 6), f"task {task_id}: {task['language']}", fill=(0, 0, 0), font=font)
        rows += [np.array(head), row]
        env.close()
    out = suite_dir / "previews" / "overview.png"
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
