"""自作スイートの各タスクの初期状態を、ポリシーの入力の 2 視点と、確認用の 4 視点（真上・横・正面・斜め）で描画する。"""

import json
from pathlib import Path

import numpy as np
import torch
from libero.libero.envs import OffScreenRenderEnv
from PIL import Image, ImageDraw, ImageFont

from vla3dsg.config import settings
from vla3dsg.demos.scripted import settle

CAMERAS = {
    "agentview": "agentview (policy input)",
    "robot0_eye_in_hand": "wrist camera (policy input)",
    "birdview": "birdview (top)",
    "sideview": "sideview",
    "frontview": "frontview",
    "galleryview": "galleryview",
}
SIZE = 320


def render_overview(suite: str, init_state: int = 0) -> Path:
    """custom_tasks/<suite>/previews/overview.png に保存して、そのパスを返す。"""
    suite_dir = settings.CUSTOM_TASKS_DIR / suite
    spec = json.loads((suite_dir / "tasks.json").read_text())
    font = ImageFont.truetype(settings.DEMO_FONT_PATH, 18)
    rows = []
    for task_id, task in enumerate(spec["tasks"]):
        env = OffScreenRenderEnv(
            bddl_file_name=str(suite_dir / task["bddl_file"]), camera_names=list(CAMERAS), camera_heights=SIZE, camera_widths=SIZE
        )
        init_states = torch.load(suite_dir / task["init_states_file"], weights_only=False)
        env.reset()
        env.set_init_state(init_states[init_state])
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
    out.parent.mkdir(exist_ok=True)
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    return out
