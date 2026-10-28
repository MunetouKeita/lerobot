"""シミュレータの正解の位置を使ったスクリプト制御（pick-and-place）。

上から近づいて縁を掴み、持ち上げ、経由点を通って置き場所の上へ運び、放す。動作の指令は人によるデモに近づける:
- 移動は位置の誤差に比例させ、3 軸まとめて速さ（ベクトルの大きさ）を制限し、1 ステップあたりの変化量も制限する
  （加速・減速をなめらかにし、動作の切り替えも急にしない）
- 回転は、手先の向きを初期の向きに保つように小さく補正する
- rng を渡すと、移動と回転にゆっくり変化する小さな揺らぎ（オルンシュタイン＝ウーレンベック過程）を加える
- 目標に届かずに手先が止まったら（物体に当たって押し続ける状態）、待たずに次の動作へ進む
- rng を渡すと、経路もデモごとに変える: 高さ（近づく・運ぶ・経由点）、速さの上限、途中の経由点の追加
"""

from collections import deque
from collections.abc import Callable
from typing import Any

import numpy as np
from libero.libero.envs import OffScreenRenderEnv
from scipy.spatial.transform import Rotation

from vla3dsg.config import settings

OPEN, CLOSE = -1.0, 1.0
NOOP = [0, 0, 0, 0, 0, 0, OPEN]

# (動作の直前の観測, 動作) を受け取るコールバック。デモの記録に使う
StepCallback = Callable[[dict, np.ndarray], None]


def body_pos(env: OffScreenRenderEnv, name: str) -> np.ndarray:
    e = env.env
    return np.array(e.sim.data.body_xpos[e.obj_body_id[name]])


class Runner:
    def __init__(
        self, env: OffScreenRenderEnv, obs: dict, on_step: StepCallback | None = None, rng: np.random.Generator | None = None
    ):
        self.env, self.obs, self.on_step, self.rng = env, obs, on_step, rng
        self.steps = 0
        self.done = False  # LIBERO は成功した時点でエピソードを終え、以降の動作指令はエラーになる
        self.ref_rot = Rotation.from_quat(obs["robot0_eef_quat"])  # 保つ手先の向き（x, y, z, w）
        self.prev = np.zeros(6)  # 直前の移動・回転の指令
        self.noise = np.zeros(6)

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

    def command(self, move: np.ndarray, grip: float, max_speed: float = settings.SCRIPTED_SPEED) -> None:
        """移動の指令（希望）を、速さ・変化量の制限、向きの補正、揺らぎを加えて送る。"""
        speed = np.linalg.norm(move)
        if speed > max_speed:
            move = move * (max_speed / speed)
        rot = (self.ref_rot * Rotation.from_quat(self.obs["robot0_eef_quat"]).inv()).as_rotvec() * settings.SCRIPTED_ROT_GAIN
        cmd = np.r_[move, rot]
        if self.rng is not None:
            sigma = np.r_[np.full(3, settings.DEMO_MOVE_NOISE), np.full(3, settings.DEMO_ROT_NOISE)]
            self.noise += -settings.DEMO_NOISE_THETA * self.noise + sigma * self.rng.standard_normal(6)
            cmd = cmd + self.noise
        cmd = self.prev + np.clip(cmd - self.prev, -settings.SCRIPTED_ACCEL, settings.SCRIPTED_ACCEL)
        self.prev = cmd
        self.step(np.r_[cmd, grip])

    def go(self, target: np.ndarray, grip: float, max_steps: int = 150, max_speed: float = settings.SCRIPTED_SPEED) -> None:
        history: deque[np.ndarray] = deque(maxlen=settings.SCRIPTED_STALL_STEPS + 1)
        for _ in range(max_steps):
            pos = self.obs["robot0_eef_pos"]
            err = target - pos
            if self.done or self.steps >= settings.SCRIPTED_MAX_STEPS or np.linalg.norm(err) < settings.SCRIPTED_TOL:
                return
            history.append(pos.copy())
            # 目標に届かないまま止まった（物体に当たっている）ら、押し続けずに次の動作へ進む
            if len(history) == history.maxlen and np.linalg.norm(history[-1] - history[0]) < settings.SCRIPTED_STALL_MOVE:
                return
            self.command(err * settings.SCRIPTED_GAIN, grip, max_speed)

    def hold(self, grip: float, n: int) -> None:
        for _ in range(n):
            self.command(np.zeros(3), grip)


def rim_grasp(angle_deg: float) -> tuple[tuple[float, float, float], float]:
    """縁を掴む向き（ボウルの中心から見た角度）から、(掴む点, 手先を回す角度) を返す。

    指が縁の壁を挟むよう、開いた指（初期の向きでは y 方向に並ぶ）を中心へ向かう方向に並べる。
    """
    a = np.deg2rad(angle_deg)
    offset = (settings.SCRIPTED_RIM_RADIUS * np.cos(a), settings.SCRIPTED_RIM_RADIUS * np.sin(a), settings.SCRIPTED_RIM_DZ)
    yaw = (angle_deg - 90.0 + 90.0) % 180.0 - 90.0  # 指は左右対称なので -90〜90° にそろえる
    return offset, yaw


def pick_and_place(
    env: OffScreenRenderEnv,
    obs: dict,
    target: str,
    dest: str,
    via: list[tuple[float, float]],
    grasp_offset: tuple[float, float, float] = settings.SCRIPTED_GRASP_OFFSET,
    grasp_yaw_deg: float = 0.0,
    rng: np.random.Generator | None = None,
    on_step: StepCallback | None = None,
) -> dict[str, Any]:
    """target を掴んで dest の上に置く。grasp_offset は target の中心から見た掴む点。
    grasp_yaw_deg だけ手先を鉛直軸まわりに回してから掴む（開いた指は初期の向きでは y 方向に並ぶ。縁の壁を挟むには、
    指を掴む点から target の中心へ向かう方向に並べる）。
    rng を渡すと、経由点をずらし、動作に揺らぎを加える（デモの多様性のため）。"""

    def jitter(scale: float, n: int) -> np.ndarray:
        return rng.uniform(-scale, scale, n) if rng is not None else np.zeros(n)

    # 経路のばらつき（デモごとに決める）
    approach_dz, lift_dz, via_dz = (
        np.array([settings.SCRIPTED_APPROACH_DZ, settings.SCRIPTED_LIFT_DZ, settings.SCRIPTED_VIA_DZ])
        + jitter(settings.DEMO_HEIGHT_JITTER, 3)
    )
    k = rng.uniform(*settings.DEMO_SPEED_RANGE) if rng is not None else 1.0
    speed, slow = settings.SCRIPTED_SPEED * k, settings.SCRIPTED_SLOW_SPEED * k

    r = Runner(env, obs, on_step, rng)
    r.ref_rot = Rotation.from_euler("z", grasp_yaw_deg, degrees=True) * r.ref_rot
    start = body_pos(env, target)
    grasp = start + np.array(grasp_offset) + np.r_[jitter(settings.DEMO_GRASP_JITTER, 2), 0]
    # まず今の高さのまま対象の真上へ動き、それから下ろす（斜めに下りると、背の高い固定物の角に当たることがある）
    above = grasp + [0, 0, approach_dz]
    r.go(np.r_[above[:2], max(above[2], r.obs["robot0_eef_pos"][2])], OPEN, max_speed=speed)
    r.go(above, OPEN, max_speed=speed)
    # 掴む直前（最後の SCRIPTED_SLOW_DZ）だけ、止まったときに勢いが残らないようにゆっくり下ろす
    r.go(grasp + [0, 0, settings.SCRIPTED_SLOW_DZ], OPEN, max_speed=speed)
    r.go(grasp, OPEN, max_speed=slow)
    r.hold(CLOSE, 15)
    r.go(grasp + [0, 0, lift_dz], CLOSE, max_speed=speed)
    lifted = float(body_pos(env, target)[2] - start[2])
    offset = (r.obs["robot0_eef_pos"] - body_pos(env, target))[:2]  # 掴んだ後の手先と対象のずれ
    d = body_pos(env, dest)
    if not via and rng is not None and rng.random() < settings.DEMO_EXTRA_VIA_PROB:
        # まっすぐ運ぶ経路の中点を横へずらした経由点を通る（回り込む経路）
        line = d[:2] + offset - r.obs["robot0_eef_pos"][:2]
        side = np.array([-line[1], line[0]]) / (np.linalg.norm(line) + 1e-9)
        mid = r.obs["robot0_eef_pos"][:2] + line / 2 + side * rng.uniform(-settings.DEMO_EXTRA_VIA_SIDE, settings.DEMO_EXTRA_VIA_SIDE)
        r.go(np.r_[mid, grasp[2] + lift_dz], CLOSE, max_speed=speed)
    for x, y in via:
        r.go(np.r_[np.array([x, y]) + jitter(settings.DEMO_VIA_JITTER, 2), grasp[2] + via_dz], CLOSE, max_speed=speed)
    r.go(np.r_[d[:2] + offset, grasp[2] + lift_dz], CLOSE, max_speed=speed)
    r.go(np.r_[d[:2] + offset, grasp[2] + settings.SCRIPTED_RELEASE_DZ + settings.SCRIPTED_SLOW_DZ], CLOSE, max_speed=speed)
    r.go(np.r_[d[:2] + offset, grasp[2] + settings.SCRIPTED_RELEASE_DZ], CLOSE, max_speed=slow)
    r.hold(OPEN, 15)
    r.go(np.r_[d[:2], grasp[2] + via_dz], OPEN, max_steps=30, max_speed=speed)
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
