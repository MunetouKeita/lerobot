"""自作スイート（custom_tasks/）が LeRobot から読み込めることと、隠れたシーンの SG を確認する。

    uv run python vla3dsg/scripts/test_custom_suite.py [--suite vla3dsg_hidden]
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import draccus  # noqa: E402
import numpy as np  # noqa: E402
from libero.libero import benchmark  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.configs.parser import load_plugin  # noqa: E402
from lerobot.envs.configs import EnvConfig  # noqa: E402

from vla3dsg.scene_graph import textify  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402


@dataclass
class _Wrapper:
    env: EnvConfig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="vla3dsg_hidden")
    args = parser.parse_args()

    load_plugin("vla3dsg.envs")
    assert args.suite in benchmark.get_benchmark_dict(), "自作スイートが登録されていない"
    spec = json.loads((settings.CUSTOM_TASKS_DIR / args.suite / "tasks.json").read_text())
    out_dir = settings.TMP_DIR / "test_custom_suite"
    out_dir.mkdir(parents=True, exist_ok=True)

    for task_id, task in enumerate(spec["tasks"]):
        cfg = draccus.parse(
            _Wrapper, args=["--env.type=libero_vla3dsg", f"--env.task={args.suite}", f"--env.task_ids=[{task_id}]"]
        ).env
        assert cfg.episode_length == spec["max_steps"], cfg.episode_length
        vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[args.suite][task_id]
        inner = vec_env.envs[0]
        assert inner._max_episode_steps == spec["max_steps"]
        assert inner.task_description == task["language"]
        assert inner._init_states.shape[0] == settings.CUSTOM_TASK_N_INIT
        assert Path(inner._task_bddl_file).parent == settings.CUSTOM_TASKS_DIR / args.suite

        obs, _ = vec_env.reset(seed=settings.SEED)
        sg = build_scene_graph(inner._env.env)
        print(f"task {task_id}: {task['language']}")
        print(f"  visibility: {task['visibility'].get('agentview_visible_ratio')}")
        print(f"  {textify.to_triples(sg)}")
        Image.fromarray(np.ascontiguousarray(obs["pixels"]["image"][0][::-1, ::-1])).save(out_dir / f"{task['name']}.png")
        vec_env.close()

    print(f"saved: {out_dir}")
    print("OK")


if __name__ == "__main__":
    main()
