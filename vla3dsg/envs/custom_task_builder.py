"""自作タスクを作るための処理: BDDL の配置範囲の書き換え、配置のサンプリング、対象物体の見え方の計測。

scripts/make_custom_task.py（評価の初期状態）と scripts/generate_demos.py（デモの配置）から使う。
"""

import re

import mujoco
import numpy as np
from libero.libero.envs import OffScreenRenderEnv

from vla3dsg.config import settings
from vla3dsg.demos.scripted import NOOP

CAMERAS = ["agentview", "robot0_eye_in_hand"]


def set_region_range(bddl: str, region: str, rng: tuple[float, float, float, float]) -> str:
    """BDDL の :regions 内の指定した領域の :ranges を (x_min y_min x_max y_max) に書き換える。"""
    pattern = re.compile(rf"(\({re.escape(region)}\s*\(:target [^)]+\)\s*\(:ranges \(\s*)\([^)]*\)", re.S)
    if not pattern.search(bddl):
        raise ValueError(f"BDDL に領域 {region!r} が見つからない")
    return pattern.sub(lambda m: m.group(1) + "(" + " ".join(f"{v}" for v in rng) + ")", bddl, count=1)


def _target_points(model: mujoco.MjModel, data: mujoco.MjData, target: str) -> tuple[np.ndarray, set[int]]:
    """対象物体の見た目用メッシュの頂点（世界座標）と、対象物体の geom の ID。"""
    geoms = {g for g in range(model.ngeom) if model.body(model.geom_bodyid[g]).name.startswith(f"{target}_")}
    points = []
    for g in geoms:
        if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mesh = model.geom_dataid[g]
        verts = model.mesh_vert[model.mesh_vertadr[mesh] : model.mesh_vertadr[mesh] + model.mesh_vertnum[mesh]]
        points.append(verts @ data.geom_xmat[g].reshape(3, 3).T + data.geom_xpos[g])
    points = np.concatenate(points)
    step = max(1, len(points) // settings.CUSTOM_TASK_VIS_MAX_POINTS)
    return points[::step], geoms


def visible_points(env: OffScreenRenderEnv, target: str) -> dict[str, tuple[int, int]]:
    """カメラごとに、(画角内にある対象物体の表面の点の数, そのうちカメラから直接見える点の数)。

    カメラから各点へ光線を飛ばし（mujoco.mj_ray）、最初に当たる geom が対象物体なら見えているとする。
    robosuite・mujoco.Renderer のセグメンテーション描画は、この環境（numpy 2、robosuite の描画コンテキストと併用）では
    正しく動かないため、描画に頼らない方法にしている。
    """
    model, data = env.env.sim.model._model, env.env.sim.data._data
    points, geoms = _target_points(model, data, target)
    result = {}
    for cam in CAMERAS:
        cam_id = model.camera(cam).id
        origin = data.cam_xpos[cam_id].copy()
        rot = data.cam_xmat[cam_id].reshape(3, 3)  # 列: カメラの x・y・z 軸（-z が視線方向）
        half = np.deg2rad(model.cam_fovy[cam_id]) / 2
        in_view = visible = 0
        geom_id = np.zeros(1, dtype=np.int32)
        for p in points:
            local = rot.T @ (p - origin)
            if local[2] >= 0 or abs(local[0] / -local[2]) > np.tan(half) or abs(local[1] / -local[2]) > np.tan(half):
                continue  # カメラの後ろ、または画角の外
            in_view += 1
            vec = (p - origin) / np.linalg.norm(p - origin)
            # 最初に当たったのが対象物体（その点か、同じ物体の手前側の面）なら、その方向に対象が見えている
            if mujoco.mj_ray(model, data, origin, vec, None, 1, -1, geom_id) >= 0 and int(geom_id[0]) in geoms:
                visible += 1
        result[cam] = (in_view, visible)
    return result


def visibility(env: OffScreenRenderEnv, target: str, occluder: str | None) -> dict:
    """対象物体の見え方。遮っている物体を遠くへどけた場合に見える点の数に対する割合で表す。"""
    e = env.env
    seen = visible_points(env, target)
    result: dict = {"visible_points": {c: v[1] for c, v in seen.items()}}
    if occluder:
        body_id = e.sim.model.body_name2id(e.get_object(occluder).root_body)
        orig = np.array(e.sim.model.body_pos[body_id])
        e.sim.model.body_pos[body_id] = orig + np.array([0.0, 0.0, -10.0])
        e.sim.forward()
        unoccluded = visible_points(env, target)
        e.sim.model.body_pos[body_id] = orig
        e.sim.forward()
        result["visible_points_without_occluder"] = {c: v[1] for c, v in unoccluded.items()}
        result["visible_ratio"] = {
            c: round(seen[c][1] / unoccluded[c][1], 3) if unoccluded[c][1] else None for c in CAMERAS
        }
    obs = e._get_observations(force_update=True)
    result["images"] = {cam: np.ascontiguousarray(obs[f"{cam}_image"][::-1, ::-1]) for cam in CAMERAS}
    return result


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
