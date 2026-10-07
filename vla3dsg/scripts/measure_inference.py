"""lerobot-eval と同じ処理経路で、MolmoAct2 の推論時間と GPU メモリを計測する。

lerobot-eval の make_policy / make_pre_post_processors を差し替え、
前処理とアクションチャンク推論（predict_action_chunk）の時間を記録する。

    uv run python vla3dsg/scripts/measure_inference.py [--suite libero_goal] [--task-id 0] [--n-episodes 1]
"""

import argparse
import json
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import torch  # noqa: E402

from lerobot.scripts import lerobot_eval  # noqa: E402

TIMES: dict[str, list[float]] = {"preprocess": [], "predict_action_chunk": [], "select_action": []}


def timed(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        out = fn(*args, **kwargs)
        torch.cuda.synchronize()
        TIMES[name].append(time.perf_counter() - t0)
        return out

    return wrapper


def patch_eval() -> None:
    make_policy = lerobot_eval.make_policy
    make_processors = lerobot_eval.make_pre_post_processors

    def make_policy_timed(*args: Any, **kwargs: Any) -> Any:
        policy = make_policy(*args, **kwargs)
        # select_action 内から呼ばれるため、インスタンス属性で差し替える
        policy.predict_action_chunk = timed("predict_action_chunk", policy.predict_action_chunk)
        policy.select_action = timed("select_action", policy.select_action)
        return policy

    def make_processors_timed(*args: Any, **kwargs: Any) -> Any:
        pre, post = make_processors(*args, **kwargs)
        pre_call = pre.__call__

        class _Timed:
            def __getattr__(self, name: str) -> Any:
                return getattr(pre, name)

            def __call__(self, *a: Any, **kw: Any) -> Any:
                return timed("preprocess", pre_call)(*a, **kw)

        return _Timed(), post

    lerobot_eval.make_policy = make_policy_timed
    lerobot_eval.make_pre_post_processors = make_processors_timed


def summarize(values: list[float]) -> dict[str, Any]:
    ms = [v * 1000 for v in values]
    rest = ms[1:] if len(ms) > 1 else ms
    return {
        "count": len(ms),
        "first_ms": round(ms[0], 1) if ms else None,
        "median_ms_excl_first": round(statistics.median(rest), 1) if rest else None,
        "mean_ms_excl_first": round(statistics.mean(rest), 1) if rest else None,
        "max_ms_excl_first": round(max(rest), 1) if rest else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--n-episodes", type=int, default=1)
    args = parser.parse_args()

    out_dir = settings.OUTPUTS_DIR / "measure_inference" / f"{args.suite}_task{args.task_id}"
    sys.argv = [sys.argv[0], *settings.molmoact2_eval_args(args.suite, [args.task_id], args.n_episodes, out_dir)]

    patch_eval()
    torch.cuda.reset_peak_memory_stats()
    lerobot_eval.main()

    gpu = torch.cuda.get_device_properties(0)
    result = {
        "suite": args.suite,
        "task_id": args.task_id,
        "n_episodes": args.n_episodes,
        "checkpoint": settings.MOLMOACT2_CHECKPOINT,
        "dtype": settings.MOLMOACT2_DTYPE,
        "gpu": gpu.name,
        "torch_max_memory_allocated_gib": round(torch.cuda.max_memory_allocated() / 2**30, 2),
        "torch_max_memory_reserved_gib": round(torch.cuda.max_memory_reserved() / 2**30, 2),
        "timing": {k: summarize(v) for k, v in TIMES.items()},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inference_timing.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
