"""生成済みのデモのデータセット（generate_demos.py）から、指示文に SG を加えたデータセットを作る。

各エピソードの配置を、生成時のシード（results/demos/<src>/episodes.jsonl）から同じ手順で再現し、
評価と同じ関数（prompting/prompt_condition.py の compose_prompt）で指示文を作る。観測・動作・動画は元のデータセットと同じ
（動画はハードリンク）。再現した配置の SG が生成時の記録と一致するかも確かめる。

学習では `--policy.normalize_language=false` とする（指示文はここで正規化済み。SG の括弧を壊さないため）。

    uv run python vla3dsg/scripts/make_sg_dataset.py --src goal_train --name goal_train_sg

データセットは data/<name>/（git 管理外）、記録（conditions.json・prompts.jsonl）は results/demos/<name>/。
"""

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import pandas as pd  # noqa: E402

from vla3dsg.demos.scripted import settle  # noqa: E402
from vla3dsg.envs.custom_task_builder import sample_init_state  # noqa: E402
from vla3dsg.prompting.prompt_condition import compose_prompt, count_tokens  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402
from vla3dsg.scripts.generate_demos import make_env, write_json  # noqa: E402
from vla3dsg.scripts.run_eval import git_info  # noqa: E402


def make_prompts(episodes: list[dict], condition: str) -> list[dict]:
    """エピソードごとに配置を再現し、指示文を作る。"""
    out, envs = [], {}
    for e in episodes:
        key = (e["suite"], e["task_id"])
        if key not in envs:
            suite_dir = settings.CUSTOM_TASKS_DIR / e["suite"]
            task = json.loads((suite_dir / "tasks.json").read_text())["tasks"][e["task_id"]]
            envs[key] = make_env(suite_dir, task)
        env = envs[key]
        # generate_demos.py の generate() と同じ手順
        state = sample_init_state(env, e["seed"], check=False)  # 一致は下の sg_matches で確かめる
        env.reset()
        env.set_init_state(state)
        settle(env)
        sg = build_scene_graph(env.env)
        prompt = compose_prompt(e["task"], condition, sg, env.env)
        out.append(
            {"episode_index": e["episode_index"], "task_id": e["task_id"], "prompt": prompt, "n_tokens": count_tokens(prompt),
             "sg_matches": sg.to_dict() == e["scene_graph"]}
        )
        print(f"episode {e['episode_index']}: {prompt}")
    for env in envs.values():
        env.close()
    return out


def write_dataset(src: Path, dst: Path, prompts: list[dict]) -> None:
    """src を dst に写し、指示文（tasks）だけを差し替える。"""
    shutil.copytree(src, dst, copy_function=os.link)
    tasks = list(dict.fromkeys(p["prompt"] for p in prompts))
    task_index = {t: i for i, t in enumerate(tasks)}
    ep_task = {p["episode_index"]: task_index[p["prompt"]] for p in prompts}
    # ハードリンクを書き換えると元のファイルも変わるため、消してから書く
    def rewrite(path: Path, df: pd.DataFrame) -> None:
        path.unlink()
        df.to_parquet(path)

    rewrite(dst / "meta/tasks.parquet", pd.DataFrame({"task_index": range(len(tasks))}, index=pd.Index(tasks, name="task")))
    for path in sorted((dst / "data").rglob("*.parquet")):
        df = pd.read_parquet(path)
        df["task_index"] = df["episode_index"].map(ep_task).astype(df["task_index"].dtype)
        rewrite(path, df)
    for path in sorted((dst / "meta/episodes").rglob("*.parquet")):
        df = pd.read_parquet(path)
        df["tasks"] = [[tasks[ep_task[i]]] for i in df["episode_index"]]
        rewrite(path, df)
    info = json.loads((dst / "meta/info.json").read_text())
    info["total_tasks"] = len(tasks)
    (dst / "meta/info.json").unlink()
    write_json(dst / "meta/info.json", info)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="元のデータセットの名前（data/<src>/、記録は results/demos/<src>/）")
    parser.add_argument("--name", required=True, help="作るデータセットの名前（data/<name>/）")
    parser.add_argument("--condition", default=settings.DEMO_SG_CONDITION, help="プロンプト条件（settings.PROMPT_CONDITIONS）")
    args = parser.parse_args()

    src, dst = settings.DEMO_DIR / args.src, settings.DEMO_DIR / args.name
    rec_dir = settings.RESULTS_DIR / "demos" / args.name
    for d in (dst, rec_dir):
        if d.exists():
            raise FileExistsError(f"{d} は既にある（上書きしない）")
    episodes = [json.loads(line) for line in (settings.RESULTS_DIR / "demos" / args.src / "episodes.jsonl").open()]
    prompts = make_prompts(episodes, args.condition)
    write_dataset(src, dst, prompts)

    rec_dir.mkdir(parents=True)
    with open(rec_dir / "prompts.jsonl", "w") as f:
        for p in prompts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    n_match = sum(p["sg_matches"] for p in prompts)
    write_json(
        rec_dir / "conditions.json",
        {"src": args.src, "condition": args.condition, "n_episodes": len(prompts), "n_tasks": len({p["prompt"] for p in prompts}),
         "sg_matches_generation": f"{n_match}/{len(prompts)}", "max_tokens": max(p["n_tokens"] for p in prompts),
         "git": git_info()},
    )
    print(f"SG が生成時と一致: {n_match}/{len(prompts)}、指示文の種類: {len({p['prompt'] for p in prompts})}")
    for task_id, n in sorted(Counter(p["task_id"] for p in prompts).items()):
        print(f"task {task_id}: {n} 本、例: {next(p['prompt'] for p in prompts if p['task_id'] == task_id)}")
    print(f"saved: {dst}, {rec_dir}")


if __name__ == "__main__":
    main()
