"""シミュレータの正解の位置を使ったスクリプト制御（pick-and-place）。

手先の姿勢は初期のまま、位置の誤差に比例した移動量の指令を出す。上から近づいて縁を掴み、持ち上げ、
経由点を通って置き場所の上へ運び、放す。
"""

from collections.abc import Callable
from typing import Any

import numpy as np
from libero.libero.envs import OffScreenRenderEnv

from vla3dsg.config import settings

OPEN, CLOSE = -1.0, 1.0
NOOP = [0, 0, 0, 0, 0, 0, OPEN]

# (動作の直前の観測, 動作) を受け取るコールバック。デモの記録に使う
StepCallback = Callable[[dict, np.ndarray], None]


def body_pos(env: OffScreenRenderEnv, name: str) -> np.ndarray:
    e = env.env
    return np.array(e.sim.data.body_xpos[e.obj_body_id[name]])


class Runner:
    def __init__(self, env: OffScreenRenderEnv, obs: dict, on_step: StepCallback | None = None):
        self.env, self.obs, self.on_step = env, obs, on_step
        self.steps = 0
        self.done = False  # LIBERO は成功した時点でエピソードを終え、以降の動作指令はエラーになる

    def step(self, action: list[float] | np.ndarray) -> None:
        # robosuite はエピソード長の上限（horizon）を超えると動作指令をエラーにするが、LIBERO は終了フラグを
        # 成功判定で上書きするため、上限に達したことがわからない。その前に打ち切る
        if self.done or self.steps >= settings.SCRIPTED_MAX_STEPS:
            return
        action = np.asarray(action, dtype=np.float64)
        action[:6] = np.clip(action[:6], -settings.SCRIPTED_ACTION_MAX, settings.SCRIPTED_ACTION_MAX)
        if self.on_step is not None:
            self.on_step(self.obs, action)
        self.obs, _, self.done, _ = self.env.step(action)
        self.steps += 1

    def go(self, target: np.ndarray, grip: float, max_steps: int = 150) -> None:
        for _ in range(max_steps):
            err = target - self.obs["robot0_eef_pos"]
            if self.done or self.steps >= settings.SCRIPTED_MAX_STEPS or np.linalg.norm(err) < settings.SCRIPTED_TOL:
                return
            self.step(np.r_[err * settings.SCRIPTED_GAIN, 0, 0, 0, grip])

    def hold(self, grip: float, n: int) -> None:
        for _ in range(n):
            self.step([0, 0, 0, 0, 0, 0, grip])


def pick_and_place(
    env: OffScreenRenderEnv,
    obs: dict,
    target: str,
    dest: str,
    via: list[tuple[float, float]],
    grasp_offset: tuple[float, float, float] = settings.SCRIPTED_GRASP_OFFSET,
    rng: np.random.Generator | None = None,
    on_step: StepCallback | None = None,
) -> dict[str, Any]:
    """target を掴んで dest の上に置く。grasp_offset は target の中心から見た掴む点。
    rng を渡すと、掴む点と経由点を少しずらす（デモの多様性のため）。"""

    def jitter(scale: float, n: int) -> np.ndarray:
        return rng.uniform(-scale, scale, n) if rng is not None else np.zeros(n)

    r = Runner(env, obs, on_step)
    start = body_pos(env, target)
    grasp = start + np.array(grasp_offset) + np.r_[jitter(settings.DEMO_GRASP_JITTER, 2), 0]
    r.go(grasp + [0, 0, settings.SCRIPTED_APPROACH_DZ], OPEN)
    r.go(grasp, OPEN)
    r.hold(CLOSE, 15)
    r.go(grasp + [0, 0, settings.SCRIPTED_LIFT_DZ], CLOSE)
    lifted = float(body_pos(env, target)[2] - start[2])
    offset = (r.obs["robot0_eef_pos"] - body_pos(env, target))[:2]  # 掴んだ後の手先と対象のずれ
    for x, y in via:
        r.go(np.r_[np.array([x, y]) + jitter(settings.DEMO_VIA_JITTER, 2), grasp[2] + settings.SCRIPTED_VIA_DZ], CLOSE)
    d = body_pos(env, dest)
    r.go(np.r_[d[:2] + offset, grasp[2] + settings.SCRIPTED_LIFT_DZ], CLOSE)
    r.go(np.r_[d[:2] + offset, grasp[2] + settings.SCRIPTED_RELEASE_DZ], CLOSE)
    r.hold(OPEN, 15)
    r.go(np.r_[d[:2], grasp[2] + settings.SCRIPTED_VIA_DZ], OPEN, max_steps=30)
    r.hold(OPEN, 20)
    return {
        "success": bool(r.done or env.env._check_success()),
        "lifted_m": round(lifted, 3),
        "steps": r.steps,  # 成功した場合は成功するまでのステップ数（物体が落ち着くまでの待機を除く）
    }


def settle(env: OffScreenRenderEnv) -> dict:
    """reset 後、評価（num_steps_wait）と同じだけ何もしない動作で物体を落ち着かせる。最後の観測を返す。"""
    obs = None
    for _ in range(settings.LIBERO_NUM_STEPS_WAIT):
        obs, *_ = env.step(NOOP)
    return obs
