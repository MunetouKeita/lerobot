"""BDDL の配置範囲から物体の配置をサンプリングし、問題のない初期状態だけを集める。"""

import numpy as np
from libero.libero.envs import OffScreenRenderEnv

from vla3dsg.config import settings
from vla3dsg.demos.scripted import NOOP


def body_positions(env: OffScreenRenderEnv) -> dict[str, np.ndarray]:
    e = env.env
    return {name: np.array(e.sim.data.body_xpos[e.obj_body_id[name]]) for name in e.objects_dict}


def sample_init_state(env: OffScreenRenderEnv, seed: int) -> np.ndarray | None:
    """seed で配置をサンプリングし、何もしない動作で落ち着かせる。問題がなければ MuJoCo の状態を返す。

    物体が落ち着いた後も動いている、または配置の直後から水平方向に大きく動いた（固定物と重なって押し出された・
    倒れた）配置は None を返す。物体はテーブルの少し上に置かれて落ちるため、押し出し・転倒は水平方向の移動で判定する。
    """
    env.seed(seed)
    env.reset()
    sampled = body_positions(env)
    for _ in range(settings.LIBERO_NUM_STEPS_WAIT):
        env.step(NOOP)
    settled = body_positions(env)
    for _ in range(settings.CUSTOM_TASK_STABILITY_STEPS):
        env.step(NOOP)
    final = body_positions(env)
    moved = max(np.linalg.norm(settled[k][:2] - sampled[k][:2]) for k in sampled)
    drift = max(np.linalg.norm(final[k] - settled[k]) for k in sampled)
    if moved > settings.CUSTOM_TASK_MAX_SETTLE_MOVE or drift > settings.CUSTOM_TASK_MAX_DRIFT:
        return None
    return env.get_sim_state()
