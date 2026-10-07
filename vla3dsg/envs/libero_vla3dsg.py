"""LeRobot の LIBERO 環境設定を拡張した環境タイプ `libero_vla3dsg`。"""

from dataclasses import dataclass
from typing import Any

from lerobot.envs.configs import EnvConfig, LiberoEnv

from vla3dsg.config import settings


@EnvConfig.register_subclass("libero_vla3dsg")
@dataclass
class LiberoVla3dsgEnv(LiberoEnv):
    # reset 後に物体を落ち着かせる no-op ステップ数（LeRobot の既定値は 10）
    num_steps_wait: int = settings.LIBERO_NUM_STEPS_WAIT

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.num_steps_wait < 0:
            raise ValueError(f"num_steps_wait must be >= 0, got {self.num_steps_wait}")

    @property
    def gym_kwargs(self) -> dict[str, Any]:
        kwargs = super().gym_kwargs
        kwargs["num_steps_wait"] = self.num_steps_wait
        return kwargs
