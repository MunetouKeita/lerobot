"""環境タイプ `libero_vla3dsg` の登録と `num_steps_wait` の受け渡しを確認する。

    uv run python vla3dsg/scripts/test_libero_vla3dsg_env.py
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import draccus  # noqa: E402
import numpy as np  # noqa: E402

from lerobot.configs.parser import load_plugin  # noqa: E402
from lerobot.envs.configs import EnvConfig  # noqa: E402

SUITE = "libero_goal"
TASK_ID = 0


@dataclass
class _Wrapper:
    env: EnvConfig


def parse_env(*args: str) -> EnvConfig:
    # lerobot-eval の --env.* と同じく、親の設定のフィールドとして解析する
    argv = ["--env.type=libero_vla3dsg", f"--env.task={SUITE}", *(f"--env.{a[2:]}" for a in args)]
    return draccus.parse(_Wrapper, args=argv).env


def max_object_speed(cfg: EnvConfig) -> tuple[int, float]:
    """reset 直後の関節速度の最大値（物体が落ち着いているかの目安）を返す。"""
    vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[SUITE][TASK_ID]
    vec_env.reset(seed=settings.SEED)
    inner = vec_env.envs[0]
    n_wait = inner.num_steps_wait
    speed = float(np.abs(inner._env.env.sim.data.qvel).max())
    vec_env.close()
    return n_wait, speed


def main() -> None:
    # プラグインとして読み込めること
    load_plugin("vla3dsg.envs")
    assert "libero_vla3dsg" in EnvConfig.get_known_choices()

    cfg = parse_env(f"--task_ids=[{TASK_ID}]")
    assert cfg.type == "libero_vla3dsg"
    assert cfg.num_steps_wait == settings.LIBERO_NUM_STEPS_WAIT
    assert cfg.gym_kwargs["num_steps_wait"] == settings.LIBERO_NUM_STEPS_WAIT
    assert parse_env("--num_steps_wait=10").num_steps_wait == 10
    print(f"parse: OK (default num_steps_wait={cfg.num_steps_wait})")

    # 環境まで値が届き、待ちステップを増やすと reset 直後の動きが小さくなること
    results = {}
    for n in (10, settings.LIBERO_NUM_STEPS_WAIT):
        n_wait, speed = max_object_speed(parse_env(f"--task_ids=[{TASK_ID}]", f"--num_steps_wait={n}"))
        assert n_wait == n, f"env.num_steps_wait={n_wait}, expected {n}"
        results[n] = speed
        print(f"num_steps_wait={n}: max |qvel| after reset = {speed:.2e}")
    assert results[settings.LIBERO_NUM_STEPS_WAIT] <= results[10]
    print("OK")


if __name__ == "__main__":
    main()
