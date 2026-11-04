"""LIBERO の公式デモ（settings.DEMO_OFFICIAL_DATASET）から 1 つのタスクのエピソードを取り出し、データセットを作る。

追加学習で、自作のシーンのデモ（generate_demos.py）と結合して使う。観測・動作は公式のまま（generate_demos.py と同じ形式）。
キャッシュの公式デモはエピソード情報が簡略化されていて lerobot-edit-dataset では扱えないため、1 フレームずつ書き出す。

--condition を付けると、指示文に SG を加える。公式デモには物体の位置の記録がないため、元のシーン（--scene、
例: vla3dsg_goal の task 0 = 標準）の配置を DEMO_SEED_START から --n-layouts 個サンプリングし、評価と同じ関数で指示文を作る。
すべての配置で同じ指示文になる（SG がシーンで決まる）ことを確かめてから使う。

    uv run python vla3dsg/scripts/extract_official_demos.py --name official_bowl
    uv run python vla3dsg/scripts/extract_official_demos.py --name official_bowl_sg --condition base_short --scene vla3dsg_goal:0

データセットは data/<name>/（git 管理外）、記録（conditions.json）は results/demos/<name>/。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402

from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402
from vla3dsg.demos.scripted import settle  # noqa: E402
from vla3dsg.envs.custom_task_builder import sample_init_state  # noqa: E402
from vla3dsg.prompting.prompt_condition import compose_prompt  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402
from vla3dsg.scripts.generate_demos import IMAGE_KEYS, features, make_env, write_json  # noqa: E402
from vla3dsg.scripts.run_eval import git_info  # noqa: E402


def scene_prompt(scene: str, condition: str, n_layouts: int) -> str:
    """元のシーンの配置から指示文を作る（全配置で同じであることを確かめる）。"""
    suite, task_id = scene.split(":")
    suite_dir = settings.CUSTOM_TASKS_DIR / suite
    task = json.loads((suite_dir / "tasks.json").read_text())["tasks"][int(task_id)]
    env = make_env(suite_dir, task)
    prompts = set()
    for seed in range(settings.DEMO_SEED_START, settings.DEMO_SEED_START + n_layouts):
        state = sample_init_state(env, seed)
        if state is None:
            continue
        env.reset()
        env.set_init_state(state)
        settle(env)
        prompts.add(compose_prompt(task["language"], condition, build_scene_graph(env.env), env.env))
    env.close()
    if len(prompts) != 1:
        raise RuntimeError(f"配置によって指示文が変わる: {prompts}")
    return prompts.pop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="作るデータセットの名前（data/<name>/）")
    parser.add_argument("--task", default=settings.DEMO_OFFICIAL_TASK, help="取り出すタスク（<スイート>/<指示文の _ 区切り>）")
    parser.add_argument("--condition", help="指示文に SG を加えるプロンプト条件（settings.PROMPT_CONDITIONS）。省略すると公式の指示文のまま")
    parser.add_argument("--scene", help="--condition で SG を作る元のシーン（<自作スイート>:<task_id>）")
    parser.add_argument("--n-layouts", type=int, default=20, help="--condition で確かめる配置の数")
    args = parser.parse_args()
    if args.condition and not args.scene:
        parser.error("--condition には --scene が必要")

    data_dir, rec_dir = settings.DEMO_DIR / args.name, settings.RESULTS_DIR / "demos" / args.name
    for d in (data_dir, rec_dir):
        if d.exists():
            raise FileExistsError(f"{d} は既にある（上書きしない）")
    language = args.task.split("/")[1].replace("_", " ")
    prompt = scene_prompt(args.scene, args.condition, args.n_layouts) if args.condition else language
    print(f"指示文: {prompt}")

    off = LeRobotDataset(
        settings.DEMO_OFFICIAL_DATASET, root=snapshot_download(settings.DEMO_OFFICIAL_DATASET, repo_type="dataset"),
        video_backend="pyav",
    )
    task_index = int(off.meta.tasks.loc[language, "task_index"])
    task_col = np.asarray(off.hf_dataset["task_index"])
    episodes = [e for e in range(off.meta.total_episodes) if task_col[off.meta.episodes[e]["dataset_from_index"]] == task_index]

    dataset = LeRobotDataset.create(
        repo_id=f"vla3dsg/{args.name}", fps=settings.DEMO_FPS, features=features(), root=data_dir, robot_type="panda"
    )
    for e in episodes:
        ep = off.meta.episodes[e]
        for i in range(ep["dataset_from_index"], ep["dataset_to_index"]):
            f = off[i]
            frame = {k: (f[k].permute(1, 2, 0).numpy() * 255).round().astype(np.uint8) for k in IMAGE_KEYS.values()}
            dataset.add_frame(
                {**frame, "observation.state": f["observation.state"].numpy(), "action": f["action"].numpy(), "task": prompt}
            )
        dataset.save_episode()
        print(f"official episode {e}: {ep['length']} frames")
    dataset.finalize()

    rec_dir.mkdir(parents=True)
    write_json(
        rec_dir / "conditions.json",
        {"source": settings.DEMO_OFFICIAL_DATASET, "task": args.task, "official_episodes": episodes, "condition": args.condition,
         "scene": args.scene, "n_layouts": args.n_layouts if args.condition else None, "prompt": prompt,
         "n_episodes": len(episodes), "n_frames": dataset.meta.total_frames, "git": git_info()},
    )
    print(f"saved: {data_dir}（{len(episodes)} 本、{dataset.meta.total_frames} フレーム）, {rec_dir}")


if __name__ == "__main__":
    main()
