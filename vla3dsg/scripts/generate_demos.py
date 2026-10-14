"""自作タスクのデモを、スクリプト制御（vla3dsg/demos/scripted.py）で自動生成し、LeRobot 形式のデータセットに保存する。

1. 評価の初期状態とは別のシード（settings.DEMO_SEED_START から）で配置をサンプリングし、問題のない配置だけ使う
2. 評価と同じく、初期状態を設定して num_steps_wait だけ待ってから、スクリプト制御で掴んで置く
3. 成功し、かつ評価の最大ステップ数に収まったエピソードだけを保存する

観測と動作は lerobot/libero と同じ形式にする（画像は 180° 回転、状態は手先の位置・軸角・グリッパー の 8 次元、
動作は 7 次元）。指示文はタスクの元の指示文。エピソード開始時の SG は episodes.jsonl に保存し、
SG を加えた指示文のデータセットは後から作る。

    uv run python vla3dsg/scripts/generate_demos.py --name hidden_cabinet_v1 --suite vla3dsg_hidden --task-ids 0 1 --n-episodes 50

データセットは data/<name>/（git 管理外）、生成の記録（summary.json・conditions.json・episodes.jsonl）は results/demos/<name>/。
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402

from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402
from lerobot.processor.env_processor import LiberoProcessorStep  # noqa: E402

from vla3dsg.demos.placement import sample_init_state  # noqa: E402
from vla3dsg.demos.scripted import pick_and_place, settle  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402
from vla3dsg.scripts.run_eval import git_info  # noqa: E402

IMAGE_KEYS = {"agentview_image": "observation.images.image", "robot0_eye_in_hand_image": "observation.images.image2"}


def features() -> dict:
    size = settings.DEMO_IMAGE_SIZE
    image = {"dtype": "video", "shape": (size, size, 3), "names": ["height", "width", "channel"]}
    return {
        **{key: dict(image) for key in IMAGE_KEYS.values()},
        "observation.state": {"dtype": "float32", "shape": (8,), "names": ["state"]},
        "action": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
    }


def to_frame(obs: dict, action: np.ndarray, task: str) -> dict:
    """評価時に LeRobot がポリシーへ渡す形（LiberoProcessorStep）と同じ観測にする。"""
    quat = torch.as_tensor(obs["robot0_eef_quat"], dtype=torch.float32).unsqueeze(0)
    axisangle = LiberoProcessorStep()._quat2axisangle(quat)[0].numpy()
    state = np.concatenate([obs["robot0_eef_pos"], axisangle, obs["robot0_gripper_qpos"]]).astype(np.float32)
    frame = {key: np.ascontiguousarray(obs[raw][::-1, ::-1]) for raw, key in IMAGE_KEYS.items()}
    return {**frame, "observation.state": state, "action": action.astype(np.float32), "task": task}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="データセットの名前（data/<name>/）")
    parser.add_argument("--suite", required=True, help="自作スイート（custom_tasks/<suite>/）")
    parser.add_argument("--task-ids", type=int, nargs="+", required=True)
    parser.add_argument("--n-episodes", type=int, required=True, help="タスクごとのエピソード数")
    args = parser.parse_args()

    data_dir = settings.DEMO_DIR / args.name
    rec_dir = settings.RESULTS_DIR / "demos" / args.name
    for d in (data_dir, rec_dir):
        if d.exists():
            raise FileExistsError(f"{d} は既にある（上書きしない）")
    rec_dir.mkdir(parents=True)

    suite_dir = settings.CUSTOM_TASKS_DIR / args.suite
    spec = json.loads((suite_dir / "tasks.json").read_text())
    dataset = LeRobotDataset.create(
        repo_id=f"vla3dsg/{args.name}", fps=settings.DEMO_FPS, features=features(), root=data_dir, robot_type="panda"
    )

    episodes, per_task = [], []
    start = time.time()
    for task_id in args.task_ids:
        task = spec["tasks"][task_id]
        demo = settings.DEMO_TASK_SPECS[args.suite][task_id]
        size = settings.DEMO_IMAGE_SIZE
        env = OffScreenRenderEnv(
            bddl_file_name=str(suite_dir / task["bddl_file"]), camera_heights=size, camera_widths=size
        )
        counts = {"rejected_placement": 0, "failed": 0, "too_long": 0}
        seed = settings.DEMO_SEED_START
        n_saved = 0
        while n_saved < args.n_episodes:
            if seed - settings.DEMO_SEED_START >= args.n_episodes * settings.CUSTOM_TASK_MAX_TRIALS_FACTOR:
                raise RuntimeError(f"task {task_id}: 成功したデモが集まらない（{n_saved}/{args.n_episodes}、{counts}）")
            state = sample_init_state(env, seed)
            seed += 1
            if state is None:
                counts["rejected_placement"] += 1
                continue
            env.reset()
            env.set_init_state(state)
            obs = settle(env)
            sg = build_scene_graph(env.env)
            frames: list[dict] = []
            result = pick_and_place(
                env, obs, demo["target"], demo["dest"], demo["via"],
                grasp_offset=demo.get("grasp_offset", settings.SCRIPTED_GRASP_OFFSET), rng=np.random.default_rng(seed - 1),
                on_step=lambda o, a: frames.append(to_frame(o, a, task["language"])),
            )
            if not result["success"]:
                counts["failed"] += 1
                continue
            if result["steps"] > spec["max_steps"]:
                counts["too_long"] += 1
                continue
            for frame in frames:
                dataset.add_frame(frame)
            dataset.save_episode()
            episodes.append(
                {
                    "episode_index": len(episodes),
                    "suite": args.suite,
                    "task_id": task_id,
                    "task": task["language"],
                    "seed": seed - 1,
                    "steps": result["steps"],
                    "scene_graph": sg.to_dict(),
                }
            )
            n_saved += 1
            print(f"task {task_id}: {n_saved}/{args.n_episodes} (seed {seed - 1}, {result['steps']} steps)")
        env.close()
        steps = [e["steps"] for e in episodes if e["task_id"] == task_id]
        per_task.append(
            {"task_id": task_id, "task": task["language"], "n_episodes": n_saved, "n_trials": seed - settings.DEMO_SEED_START,
             **counts, "steps_min": min(steps), "steps_max": max(steps), "n_frames": sum(steps)}
        )
    dataset.finalize()

    summary = {
        "dataset": str(data_dir.relative_to(settings.REPO_ROOT)),
        "n_episodes": len(episodes),
        "n_frames": sum(e["steps"] for e in episodes),
        "elapsed_s": round(time.time() - start),
        "per_task": per_task,
    }
    conditions = {
        "args": vars(args),
        "settings": {k: getattr(settings, k) for k in dir(settings) if k.startswith(("SCRIPTED_", "DEMO_")) and k != "DEMO_DIR"},
        "git": git_info(),
    }
    (rec_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    (rec_dir / "conditions.json").write_text(json.dumps(conditions, indent=2, ensure_ascii=False, default=str))
    with open(rec_dir / "episodes.jsonl", "w") as f:
        for e in episodes:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"saved: {data_dir}, {rec_dir}")


if __name__ == "__main__":
    main()
