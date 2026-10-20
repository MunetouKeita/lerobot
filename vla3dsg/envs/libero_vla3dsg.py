"""LeRobot の LIBERO 環境設定を拡張した環境タイプ `libero_vla3dsg`。"""

from dataclasses import dataclass
from typing import Any

import draccus

from lerobot.envs.configs import EnvConfig, LiberoEnv

from vla3dsg.config import settings
from vla3dsg.envs.custom_suites import custom_suite_max_steps


@EnvConfig.register_subclass("libero_vla3dsg")
@dataclass
class LiberoVla3dsgEnv(LiberoEnv):
    # reset 後に物体を落ち着かせる no-op ステップ数（LeRobot の既定値は 10）
    num_steps_wait: int = settings.LIBERO_NUM_STEPS_WAIT

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.num_steps_wait < 0:
            raise ValueError(f"num_steps_wait must be >= 0, got {self.num_steps_wait}")
        # 自作スイートは LeRobot の既定（500）ではなく tasks.json の max_steps を使う
        max_steps = custom_suite_max_steps()
        suites = [s.strip() for s in str(self.task).split(",")]
        if self.episode_length is None and any(s in max_steps for s in suites):
            if not all(s in max_steps for s in suites):
                raise ValueError("自作スイートと LIBERO のスイートは同時に指定できない（最大ステップ数が異なるため）")
            self.episode_length = max(max_steps[s] for s in suites)

    @property
    def gym_kwargs(self) -> dict[str, Any]:
        kwargs = super().gym_kwargs
        kwargs["num_steps_wait"] = self.num_steps_wait
        return kwargs


@dataclass
class _Wrapper:
    env: EnvConfig


def parse_config(suite: str, *args: str) -> EnvConfig:
    """lerobot-eval の --env.* と同じく解析した環境設定（args は "task_ids=[0]" のような --env. の後ろの部分）。"""
    argv = ["--env.type=libero_vla3dsg", f"--env.task={suite}", *(f"--env.{a}" for a in args)]
    return draccus.parse(_Wrapper, args=argv).env


def make_env(suite: str, task_id: int, *args: str) -> Any:
    """1 タスク・1 並列の環境（gymnasium の VectorEnv）。テストや確認用。"""
    return parse_config(suite, f"task_ids=[{task_id}]", *args).create_envs(n_envs=1, use_async_envs=False)[suite][task_id]
