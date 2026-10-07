"""MolmoAct2 の LIBERO 評価を実行し、結果を条件とともに results/ に保存する。

    uv run python vla3dsg/scripts/run_eval.py --name baseline/libero_goal_n5 --suite libero_goal --n-episodes 5
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

from lerobot.envs.libero import _get_suite  # noqa: E402
from lerobot.scripts import lerobot_eval  # noqa: E402


def git_info() -> dict[str, str | bool]:
    def run(*cmd: str) -> str:
        return subprocess.run(cmd, cwd=settings.REPO_ROOT, capture_output=True, text=True).stdout.strip()

    return {
        "commit": run("git", "rev-parse", "HEAD"),
        "upstream_base": run("git", "merge-base", "HEAD", "upstream/main"),
        "dirty": bool(run("git", "status", "--porcelain", "--", "src", "vla3dsg/envs", "vla3dsg/config")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="results/ 以下の保存先（例: baseline/libero_goal_n5）")
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-ids", type=int, nargs="*", help="省略時はスイートの全タスク")
    parser.add_argument("--n-episodes", type=int, default=5, help="1タスクあたりのエピソード数")
    args = parser.parse_args()

    task_ids = args.task_ids or list(range(len(_get_suite(args.suite).tasks)))
    out_dir = settings.OUTPUTS_DIR / "eval" / args.name
    res_dir = settings.RESULTS_DIR / args.name
    if res_dir.exists():
        sys.exit(f"{res_dir} は既に存在する。別の --name を指定すること")

    eval_args = settings.molmoact2_eval_args(args.suite, task_ids, args.n_episodes, out_dir)
    conditions = {
        "suite": args.suite,
        "task_ids": task_ids,
        "n_episodes_per_task": args.n_episodes,
        "prompt_condition": "original",
        "checkpoint": settings.MOLMOACT2_CHECKPOINT,
        "norm_tag": settings.MOLMOACT2_NORM_TAG,
        "dtype": settings.MOLMOACT2_DTYPE,
        "num_steps_wait": settings.LIBERO_NUM_STEPS_WAIT,
        "seed": settings.SEED,
        "eval_seed": settings.EVAL_SEED,
        "git": git_info(),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "lerobot_eval_args": eval_args,
    }

    sys.argv = [sys.argv[0], *eval_args]
    t0 = time.perf_counter()
    lerobot_eval.main()
    conditions["wall_s"] = round(time.perf_counter() - t0, 1)

    info = json.loads((out_dir / "eval_info.json").read_text())
    per_task = [
        {"task_id": t["task_id"], "n_success": t["n_success"], "n_episodes": t["n_episodes"], "pc_success": t["pc_success"]}
        for t in info["per_task"]
    ]
    summary = {
        "pc_success": info["overall"]["pc_success"],
        "n_success": info["overall"]["n_success"],
        "n_episodes": info["overall"]["n_episodes"],
        "pc_success_ci95": info["overall"]["pc_success_ci95"],
        "per_task": per_task,
    }

    res_dir.mkdir(parents=True)
    (res_dir / "conditions.json").write_text(json.dumps(conditions, indent=2, ensure_ascii=False))
    (res_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (res_dir / "eval_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"saved: {res_dir}（動画は {out_dir / 'videos'}）")


if __name__ == "__main__":
    main()
