"""MolmoAct2 の LIBERO 評価を実行し、結果を条件とともに results/<name>/ に保存する。

lerobot-eval の出力先も results/<name>/ にする（eval_info.json と videos/）。
実行ログは results/<name>/eval.log に保存する（videos/ と eval.log は git 管理外）。

    uv run python vla3dsg/scripts/run_eval.py --name baseline/libero_goal_n5 --suite libero_goal --n-episodes 5
    uv run python vla3dsg/scripts/run_eval.py --name samples/all_suites --suite libero_spatial,libero_goal \
        --task-ids 0 5 --n-episodes 2 --annotated-video
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402
from vla3dsg.visualization import rollout_video  # noqa: E402

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


class _Tee:
    """標準出力・標準エラーを画面とログファイルの両方に書く。"""

    def __init__(self, stream: TextIO, log: TextIO) -> None:
        self.stream, self.log = stream, log

    def write(self, data: str) -> int:
        self.log.write(data)
        return self.stream.write(data)

    def flush(self) -> None:
        self.log.flush()
        self.stream.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="results/ 以下の保存先（例: baseline/libero_goal_n5）")
    parser.add_argument("--suite", default="libero_goal", help="カンマ区切りで複数指定できる")
    parser.add_argument("--task-ids", type=int, nargs="*", help="省略時はスイートの全タスク（複数スイートでは必須）")
    parser.add_argument("--n-episodes", type=int, default=5, help="1タスクあたりのエピソード数")
    parser.add_argument(
        "--annotated-video", action="store_true", help="2 視点・指示文・成否を重ねた実時間の動画で保存する"
    )
    args = parser.parse_args()

    suites = args.suite.split(",")
    if args.task_ids:
        task_ids = args.task_ids
    elif len(suites) == 1:
        task_ids = list(range(len(_get_suite(suites[0]).tasks)))
    else:
        sys.exit("複数スイートでは --task-ids を指定すること")
    res_dir = settings.RESULTS_DIR / args.name
    if res_dir.exists():
        sys.exit(f"{res_dir} は既に存在する。別の --name を指定すること")

    eval_args = settings.molmoact2_eval_args(args.suite, task_ids, args.n_episodes, res_dir)
    conditions = {
        "suite": args.suite,
        "task_ids": task_ids,
        "n_episodes_per_task": args.n_episodes,
        "prompt_condition": "original",
        "annotated_video": args.annotated_video,
        "video_save": {"first_n": settings.VIDEO_SAVE_FIRST_N, "failures": settings.VIDEO_SAVE_FAILURES},
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

    if args.annotated_video:
        rollout_video.install()
    sys.argv = [sys.argv[0], *eval_args]
    res_dir.mkdir(parents=True)
    t0 = time.perf_counter()
    # lerobot のロガーが stderr を保持するため、プロセス終了までログファイルを開いたままにする
    log = open(res_dir / "eval.log", "w")  # noqa: SIM115
    sys.stdout, sys.stderr = _Tee(sys.stdout, log), _Tee(sys.stderr, log)
    lerobot_eval.main()
    conditions["wall_s"] = round(time.perf_counter() - t0, 1)

    info = json.loads((res_dir / "eval_info.json").read_text())
    if args.annotated_video:
        # 保存しなかった動画（先頭 N 本以降の成功エピソード）のパスを除く
        def _existing(paths: list[str]) -> list[str]:
            return [p for p in paths if Path(p).exists()]

        for task in info["per_task"]:
            task["metrics"]["video_paths"] = _existing(task["metrics"].get("video_paths", []))
        for group in [*info["per_group"].values(), info["overall"]]:
            group["video_paths"] = _existing(group.get("video_paths", []))
        (res_dir / "eval_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
    per_task = [
        {
            "suite": t["task_group"],
            "task_id": t["task_id"],
            "instruction": _get_suite(t["task_group"]).get_task(t["task_id"]).language,
            "successes": t["metrics"]["successes"],
            "pc_success": t["pc_success"],
        }
        for t in info["per_task"]
    ]
    summary = {
        "pc_success": info["overall"]["pc_success"],
        "n_success": info["overall"]["n_success"],
        "n_episodes": info["overall"]["n_episodes"],
        "pc_success_ci95": info["overall"]["pc_success_ci95"],
        "per_suite": {g: v["pc_success"] for g, v in info["per_group"].items()},
        "per_task": per_task,
    }

    (res_dir / "conditions.json").write_text(json.dumps(conditions, indent=2, ensure_ascii=False))
    (res_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"saved: {res_dir}")


if __name__ == "__main__":
    main()
