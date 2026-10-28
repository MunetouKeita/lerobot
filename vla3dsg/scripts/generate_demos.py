"""自作タスクのデモを、スクリプト制御（vla3dsg/demos/scripted.py）で自動生成し、LeRobot 形式のデータセットに保存する。

1. 評価の初期状態とは別のシード（settings.DEMO_SEED_START から）で配置をサンプリングし、問題のない配置だけ使う
   （tasks.json に min_distance があるタスクは、評価の初期状態と同じく近すぎる・乗った・動く配置も除く）
2. 評価と同じく、初期状態を設定して num_steps_wait だけ待ってから、スクリプト制御で掴んで置く
3. 成功し、かつ評価の最大ステップ数に収まったエピソードだけを保存する

観測と動作は lerobot/libero と同じ形式にする（画像は 180° 回転、状態は手先の位置・軸角・グリッパー の 8 次元、
動作は 7 次元）。指示文はタスクの元の指示文。エピソード開始時の SG は episodes.jsonl に保存し、
SG を加えた指示文のデータセットは後から作る。

    uv run python vla3dsg/scripts/generate_demos.py --name goal_v1 --suite vla3dsg_goal --task-ids 0 1 2 3 --n-episodes 50

データセットは data/<name>/（git 管理外）、生成の記録（summary.json・conditions.json・episodes.jsonl）は results/demos/<name>/。

--check を付けると、データセットは作らず、評価の初期状態（.pruned_init）でスクリプト制御が成功するか（タスクが
物理的にできるか）を確かめる。--randomize を付けると、デモの生成と同じく掴む向き・経路・揺らぎをランダムにして確かめる。結果は results/<name>/（summary.json、videos/ に各タスクの先頭 --n-video 本の動画）。

    uv run python vla3dsg/scripts/generate_demos.py --check --name demos/check_goal --suite vla3dsg_goal --task-ids 0 1 2 3

--report を付けると、生成済みのデータセット data/<name>/ を LIBERO の公式デモ（lerobot/libero の同じ元タスク）と比べる。
動作の統計（report.json）、1 エピソードずつの動作の指令のグラフ（actions_vs_official.png）、縦に並べた比較動画
（videos/compare_with_official.mp4）を results/demos/<name>/ に保存する。

    uv run python vla3dsg/scripts/generate_demos.py --report --name goal_v1 --suite vla3dsg_goal --task-ids 0 1 2 3
"""

import argparse
import json
import sys
import time
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import imageio  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402

from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402
from lerobot.processor.env_processor import LiberoProcessorStep  # noqa: E402

from vla3dsg.envs.custom_task_builder import make_env as create_env, sample_init_state, too_close  # noqa: E402
from vla3dsg.demos.scripted import body_pos, pick_and_place, rim_grasp, settle  # noqa: E402
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


def make_env(suite_dir: Path, task: dict) -> OffScreenRenderEnv:
    size = settings.DEMO_IMAGE_SIZE
    return create_env(str(suite_dir / task["bddl_file"]), camera_heights=size, camera_widths=size)


def run_scripted(env: OffScreenRenderEnv, obs: dict, demo: dict, rng: np.random.Generator | None, on_step) -> dict[str, Any]:
    """settings.DEMO_TASK_SPECS のタスクの設定で、スクリプト制御を 1 エピソード実行する。

    grasp_angles があれば、縁を掴む向きをその範囲から選ぶ（rng を渡すとランダム、渡さないと中央）。
    grasp_angles_by_x があれば、対象の x の位置で範囲を切り替える（((x の上限, (lo, hi)), ...)。上限 None は残り全部）。
    """
    offset, yaw = demo.get("grasp_offset", settings.SCRIPTED_GRASP_OFFSET), demo.get("grasp_yaw_deg", 0.0)
    angle = None
    ranges = demo.get("grasp_angles")
    if "grasp_angles_by_x" in demo:
        x = body_pos(env, demo["target"])[0]
        ranges = next(r for x_max, r in demo["grasp_angles_by_x"] if x_max is None or x < x_max)
    if ranges is not None:
        lo, hi = ranges
        angle = float(rng.uniform(lo, hi)) if rng is not None else (lo + hi) / 2
        offset, yaw = rim_grasp(angle)
    result = pick_and_place(
        env, obs, demo["target"], demo["dest"], demo["via"], grasp_offset=offset, grasp_yaw_deg=yaw, rng=rng, on_step=on_step
    )
    return {**result, "grasp_angle": None if angle is None else round(angle, 1)}


def conditions(args: argparse.Namespace) -> dict:
    return {
        "args": vars(args),
        "settings": {k: getattr(settings, k) for k in dir(settings) if k.startswith(("SCRIPTED_", "DEMO_")) and k != "DEMO_DIR"},
        "git": git_info(),
    }


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def check(args: argparse.Namespace, suite_dir: Path, spec: dict) -> None:
    res_dir = settings.RESULTS_DIR / args.name
    if res_dir.exists():
        raise FileExistsError(f"{res_dir} は既にある（上書きしない）")
    (res_dir / "videos").mkdir(parents=True)
    per_task = []
    for task_id in args.task_ids:
        task = spec["tasks"][task_id]
        env = make_env(suite_dir, task)
        init_states = torch.load(suite_dir / task["init_states_file"], weights_only=False)
        n = min(args.n_episodes or len(init_states), len(init_states))
        episodes = []
        for i in range(n):
            env.reset()
            env.set_init_state(init_states[i])
            obs = settle(env)
            frames: list[np.ndarray] = []

            def on_step(o: dict, _action: np.ndarray) -> None:
                if i < args.n_video:
                    frames.append(np.concatenate([o[f"{c}_image"][::-1, ::-1] for c in ("agentview", "robot0_eye_in_hand")], axis=1))

            rng = np.random.default_rng(settings.DEMO_SEED_START + i) if args.randomize else None
            result = run_scripted(env, obs, settings.DEMO_TASK_SPECS[args.suite][task_id], rng, on_step)
            episodes.append({"init_state": i, **result})
            if frames:
                imageio.mimsave(res_dir / "videos" / f"task{task_id}_episode_{i}.mp4", frames, fps=settings.LIBERO_CONTROL_FPS)
            print(f"task {task_id}: {episodes[-1]}")
        env.close()
        per_task.append(
            {
                "task_id": task_id,
                "instruction": task["language"],
                "n_success": sum(e["success"] for e in episodes),
                "n_episodes": len(episodes),
                "steps_max": max(e["steps"] for e in episodes),
                "episodes": episodes,
            }
        )
    write_json(res_dir / "summary.json", {"suite": args.suite, "per_task": per_task})
    write_json(res_dir / "conditions.json", conditions(args))
    for t in per_task:
        print(f"task {t['task_id']}: {t['n_success']}/{t['n_episodes']}")
    print(f"saved: {res_dir}")


def generate(args: argparse.Namespace, suite_dir: Path, spec: dict) -> None:
    data_dir = settings.DEMO_DIR / args.name
    rec_dir = settings.RESULTS_DIR / "demos" / args.name
    for d in (data_dir, rec_dir):
        if d.exists():
            raise FileExistsError(f"{d} は既にある（上書きしない）")
    rec_dir.mkdir(parents=True)

    dataset = LeRobotDataset.create(
        repo_id=f"vla3dsg/{args.name}", fps=settings.DEMO_FPS, features=features(), root=data_dir, robot_type="panda"
    )

    episodes, per_task = [], []
    start = time.time()
    for task_id in args.task_ids:
        task = spec["tasks"][task_id]
        demo = settings.DEMO_TASK_SPECS[args.suite][task_id]
        env = make_env(suite_dir, task)
        counts = {"rejected_placement": 0, "failed": 0, "too_long": 0}
        seed = settings.DEMO_SEED_START
        n_saved = 0
        while n_saved < args.n_episodes:
            if seed - settings.DEMO_SEED_START >= args.n_episodes * settings.DEMO_MAX_TRIALS_FACTOR:
                raise RuntimeError(f"task {task_id}: 成功したデモが集まらない（{n_saved}/{args.n_episodes}、{counts}）")
            state = sample_init_state(env, seed)
            seed += 1
            # 評価の初期状態と同じ基準で配置を除く（make_custom_task.py --min-distance）
            min_distance = task.get("min_distance")
            if state is None or (min_distance is not None and too_close(env, state, min_distance)):
                counts["rejected_placement"] += 1
                continue
            env.reset()
            env.set_init_state(state)
            obs = settle(env)
            sg = build_scene_graph(env.env)
            frames: list[dict] = []
            result = run_scripted(
                env, obs, demo, np.random.default_rng(seed - 1), lambda o, a: frames.append(to_frame(o, a, task["language"]))
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
    write_json(rec_dir / "summary.json", summary)
    write_json(rec_dir / "conditions.json", conditions(args))
    with open(rec_dir / "episodes.jsonl", "w") as f:
        for e in episodes:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"saved: {data_dir}, {rec_dir}")


def load_episode(ds: LeRobotDataset, ep: int) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """(2 視点を横に並べた画像, 動作, 状態)"""
    e = ds.meta.episodes[ep]
    frames, actions, states = [], [], []
    for i in range(e["dataset_from_index"], e["dataset_to_index"]):
        f = ds[i]
        frames.append(np.concatenate([(f[k].permute(1, 2, 0).numpy() * 255).astype(np.uint8) for k in IMAGE_KEYS.values()], 1))
        actions.append(f["action"].numpy())
        states.append(f["observation.state"].numpy())
    return frames, np.array(actions), np.array(states)


def action_stats(actions: np.ndarray, states: np.ndarray) -> dict:
    moved = np.linalg.norm(np.diff(states[:, :3], axis=0), axis=1)
    return {
        "steps": len(actions),
        "move_abs_mean": np.abs(actions[:, :3]).mean(0).round(3).tolist(),
        "move_saturated_frac": (np.abs(actions[:, :3]) > 0.9).mean(0).round(3).tolist(),
        "rot_abs_mean": np.abs(actions[:, 3:6]).mean(0).round(3).tolist(),
        "stalled_frac": round(float((moved < settings.DEMO_REPORT_STALL_MOVE).mean()), 3),  # 手先がほぼ動かないステップの割合
    }


def report(args: argparse.Namespace, spec: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from huggingface_hub import snapshot_download
    from PIL import Image, ImageDraw, ImageFont

    rec_dir = settings.RESULTS_DIR / "demos" / args.name
    gen = LeRobotDataset(f"vla3dsg/{args.name}", root=settings.DEMO_DIR / args.name, video_backend="pyav")
    off_root = snapshot_download(settings.DEMO_OFFICIAL_DATASET, repo_type="dataset")
    off = LeRobotDataset(settings.DEMO_OFFICIAL_DATASET, root=off_root, video_backend="pyav")
    episodes = [json.loads(line) for line in (rec_dir / "episodes.jsonl").read_text().splitlines()]

    # 公式デモ: 元タスク（tasks.json の base）の先頭 DEMO_REPORT_N_EPISODES 本
    off_task_index = {}
    for t in off.meta.tasks.itertuples():
        off_task_index[t.Index] = int(t.task_index)
    off_eps = {}
    for e in range(off.meta.total_episodes):
        off_eps.setdefault(int(off.hf_dataset[int(off.meta.episodes[e]["dataset_from_index"])]["task_index"]), []).append(e)
    rows, result = [], {}
    for task_id in args.task_ids:
        task = spec["tasks"][task_id]
        # 元が LIBERO のタスクならその公式デモ、自作のシーンなら settings.DEMO_OFFICIAL_TASK と比べる
        base = task["base"] if not task["base"].endswith(".bddl") else settings.DEMO_OFFICIAL_TASK
        base_language = base.split("/")[1].replace("_", " ")
        groups = {
            f"official ({base})": (off, off_eps[off_task_index[base_language]][: settings.DEMO_REPORT_N_EPISODES]),
            f"generated (task {task_id})": (
                gen, [e["episode_index"] for e in episodes if e["task_id"] == task_id][: settings.DEMO_REPORT_N_EPISODES]
            ),
        }
        for label, (ds, eps) in groups.items():
            loaded = [load_episode(ds, ep) for ep in eps]
            per = [action_stats(a, st) for _, a, st in loaded]
            result[label] = {k: np.mean([p[k] for p in per], axis=0).round(3).tolist() for k in per[0]}
            if label not in {r[0] for r in rows}:
                rows.append((label, *loaded[0][:2]))
    write_json(rec_dir / "report.json", {"n_episodes_each": settings.DEMO_REPORT_N_EPISODES, "stats": result})

    fig, axes = plt.subplots(len(rows), 1, figsize=(11, 2.7 * len(rows)), sharex=True)
    for ax, (label, _, actions) in zip(axes, rows):
        for k, name in enumerate(["x", "y", "z", "rx", "ry", "rz", "gripper"]):
            ax.plot(actions[:, k], label=name, lw=1.2, ls="-" if k < 3 else (":" if k < 6 else "--"))
        for v in (settings.SCRIPTED_ACTION_MAX, -settings.SCRIPTED_ACTION_MAX):
            ax.axhline(v, color="gray", lw=0.5)
        ax.set_title(label)
        ax.set_ylim(-1.1, 1.1)
        ax.set_ylabel("action")
    axes[0].legend(ncol=7, fontsize=8, loc="upper right")
    axes[-1].set_xlabel("step")
    fig.tight_layout()
    fig.savefig(rec_dir / "actions_vs_official.png", dpi=110)

    font, small = ImageFont.truetype(settings.DEMO_FONT_PATH, 20), ImageFont.truetype(settings.DEMO_FONT_PATH, 14)
    n = max(len(f) for _, f, _ in rows)
    video = []
    for t in range(n):
        tiles = []
        for label, frames, actions in rows:
            k = min(t, len(frames) - 1)
            im = Image.fromarray(frames[k])
            draw = ImageDraw.Draw(im)
            draw.text((6, 4), label, fill=(255, 255, 0), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
            a = actions[k]
            text = f"step {k}/{len(frames)}{' (done)' if t >= len(frames) else ''}  move=({a[0]:+.2f},{a[1]:+.2f},{a[2]:+.2f}) rot=({a[3]:+.2f},{a[4]:+.2f},{a[5]:+.2f})"
            draw.text((6, settings.DEMO_IMAGE_SIZE - 30), text, fill=(255, 255, 255), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
            tiles.append(np.array(im))
        video.append(np.concatenate(tiles, 0))
    (rec_dir / "videos").mkdir(exist_ok=True)
    imageio.mimsave(rec_dir / "videos" / "compare_with_official.mp4", video, fps=settings.LIBERO_CONTROL_FPS)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"saved: {rec_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="データセットの名前（data/<name>/）。--check では結果の保存先（results/<name>/）")
    parser.add_argument("--suite", required=True, help="自作スイート（custom_tasks/<suite>/）")
    parser.add_argument("--task-ids", type=int, nargs="+", required=True)
    parser.add_argument("--n-episodes", type=int, help="タスクごとのエピソード数（--check では省略すると初期状態すべて）")
    parser.add_argument("--check", action="store_true", help="評価の初期状態でスクリプト制御が成功するかだけを確かめる")
    parser.add_argument("--n-video", type=int, default=3, help="--check で動画を保存するエピソード数（タスクごと）")
    parser.add_argument(
        "--randomize", action="store_true", help="--check で、デモの生成と同じく掴む向き・経路・揺らぎをランダムにする"
    )
    parser.add_argument("--report", action="store_true", help="生成済みのデータセットを公式デモと比べる")
    args = parser.parse_args()

    suite_dir = settings.CUSTOM_TASKS_DIR / args.suite
    spec = json.loads((suite_dir / "tasks.json").read_text())
    if args.check:
        check(args, suite_dir, spec)
    elif args.report:
        report(args, spec)
    else:
        if args.n_episodes is None:
            parser.error("--n-episodes が必要")
        generate(args, suite_dir, spec)


if __name__ == "__main__":
    main()
