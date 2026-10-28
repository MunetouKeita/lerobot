"""自作タスクを作るための処理: BDDL の配置範囲の書き換え、配置のサンプリング、対象物体の見え方の計測。

scripts/make_custom_task.py（評価の初期状態）と scripts/generate_demos.py（デモの配置）から使う。
"""

import re

import mujoco
import numpy as np
from libero.libero.envs import OffScreenRenderEnv
from robosuite.utils.errors import RandomizationError

from vla3dsg.config import settings
from vla3dsg.demos.scripted import NOOP
from vla3dsg.scene_graph.builder import _display_names, _support_relations

CAMERAS = ["agentview", "robot0_eye_in_hand"]


def set_region_range(bddl: str, region: str, rng: tuple[float, float, float, float]) -> str:
    """BDDL の :regions 内の指定した領域の :ranges を (x_min y_min x_max y_max) に書き換える。"""
    pattern = re.compile(rf"(\({re.escape(region)}\s*\(:target [^)]+\)\s*\(:ranges \(\s*)\([^)]*\)", re.S)
    if not pattern.search(bddl):
        raise ValueError(f"BDDL に領域 {region!r} が見つからない")
    return pattern.sub(lambda m: m.group(1) + "(" + " ".join(f"{v}" for v in rng) + ")", bddl, count=1)


def remove_object(bddl: str, obj_id: str) -> str:
    """BDDL の :objects と :init から物体を取り除く（例: おとりのボウルを除いたシーン）。"""
    objects = re.search(r"\(:objects(.*?)\n  \)", bddl, re.S)
    if objects is None or not re.search(rf"\b{re.escape(obj_id)}\b", objects.group(1)):
        raise ValueError(f"BDDL の :objects に {obj_id!r} がない")
    lines = []
    for line in objects.group(1).splitlines():
        if re.search(rf"\b{re.escape(obj_id)}\b", line):
            names, _, category = line.partition(" - ")
            rest = [n for n in names.split() if n != obj_id]
            if not rest:
                continue
            line = "    " + " ".join(rest) + " - " + category
        lines.append(line)
    bddl = bddl[: objects.start(1)] + "\n".join(lines) + bddl[objects.end(1) :]
    # :init の (On <obj_id> ...) などを消す
    return re.sub(rf"\n\s*\((On|In) {re.escape(obj_id)} [^)]*\)", "", bddl)


def add_object(bddl: str, obj_id: str, category: str, region: str, rng: tuple[float, float, float, float]) -> str:
    """BDDL に物体を足す（例: おとりのボウル）。テーブル上の領域 region（範囲 rng）を作り、そこに置く。"""
    if re.search(rf"\b{re.escape(obj_id)}\b", bddl):
        raise ValueError(f"BDDL に {obj_id!r} がすでにある")
    table = re.search(r"\(:fixtures\s*\n\s*(\w+) - ", bddl).group(1)
    ranges = " ".join(f"{v}" for v in rng)
    entry = f"\n      ({region}\n          (:target {table})\n          (:ranges (\n              ({ranges})\n            )\n          )\n      )"
    bddl = re.sub(r"\(:regions", lambda m: m.group(0) + entry, bddl, count=1)
    same = re.search(rf"(\(:objects.*?\n\s*)([\w ]+?)( - {re.escape(category)}\n)", bddl, re.S)
    if same:  # 同じ種類の物体がすでにあれば同じ行に足す（LIBERO の BDDL の読み込みは種類ごとに 1 行）
        bddl = bddl[: same.end(2)] + f" {obj_id}" + bddl[same.end(2) :]
    else:
        bddl = re.sub(r"(\(:objects.*?)(\n  \))", lambda m: m.group(1) + f"\n    {obj_id} - {category}" + m.group(2), bddl, count=1, flags=re.S)
    return re.sub(r"\(:init", lambda m: m.group(0) + f"\n    (On {obj_id} {table}_{region})", bddl, count=1)


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


def ray_hits(model: mujoco.MjModel, data: mujoco.MjData, target: str, cam: str) -> list[str | None]:
    """カメラの画角内にある対象物体の表面の点ごとに、カメラからその点へ飛ばした光線が最初に当たる body の名前。

    最初に当たったのが対象物体（その点か、同じ物体の手前側の面）なら、その方向に対象が見えている。
    robosuite・mujoco.Renderer のセグメンテーション描画は、この環境（numpy 2、robosuite の描画コンテキストと併用）では
    正しく動かないため、描画に頼らない方法にしている。
    """
    points, _ = _target_points(model, data, target)
    cam_id = model.camera(cam).id
    origin = data.cam_xpos[cam_id].copy()
    rot = data.cam_xmat[cam_id].reshape(3, 3)  # 列: カメラの x・y・z 軸（-z が視線方向）
    tan_half = np.tan(np.deg2rad(model.cam_fovy[cam_id]) / 2)
    geom_id = np.zeros(1, dtype=np.int32)
    hits: list[str | None] = []
    for p in points:
        local = rot.T @ (p - origin)
        if local[2] >= 0 or abs(local[0] / -local[2]) > tan_half or abs(local[1] / -local[2]) > tan_half:
            continue  # カメラの後ろ、または画角の外
        vec = (p - origin) / np.linalg.norm(p - origin)
        hit = mujoco.mj_ray(model, data, origin, vec, None, 1, -1, geom_id) >= 0
        hits.append(model.body(model.geom_bodyid[int(geom_id[0])]).name if hit else None)
    return hits


def visible_points(env: OffScreenRenderEnv, target: str) -> dict[str, tuple[int, int]]:
    """カメラごとに、(画角内にある対象物体の表面の点の数, そのうちカメラから直接見える点の数)。"""
    model, data = env.env.sim.model._model, env.env.sim.data._data
    result = {}
    for cam in CAMERAS:
        hits = ray_hits(model, data, target, cam)
        result[cam] = (len(hits), sum(1 for h in hits if h is not None and h.startswith(f"{target}_")))
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


def make_env(bddl_file: str, **kwargs) -> OffScreenRenderEnv:
    """環境を作る。作るときの配置のサンプリング（乱数は固定されない）が、配置範囲の広いタスクでまれに失敗するため作り直す
    （配置は後で初期状態やシードで上書きする）。"""
    for attempt in range(settings.ENV_CREATE_RETRIES):
        try:
            return OffScreenRenderEnv(bddl_file_name=bddl_file, **kwargs)
        except RandomizationError:
            if attempt == settings.ENV_CREATE_RETRIES - 1:
                raise
    raise AssertionError


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


def too_close(env: OffScreenRenderEnv, state: np.ndarray, min_distance: float) -> bool:
    """評価と同じく初期状態から落ち着かせた後、動かせる物体どうしが min_distance より近いか、
    物体がテーブル以外の物（ほかの物体・固定物）に乗っている・触れているか、待つあいだに大きく動いたか。

    保存した状態では問題がなくても、読み込んで待つとコンロに乗る・隣の物体にもたれる・皿と重なった物体が弾かれてテーブルの外へ
    落ちることがある（MuJoCo の状態の読み込みが、保存したときの動きを完全には再現しない）ため、評価と同じ手順で確かめる。
    """
    env.reset()
    env.set_init_state(state)
    e = env.env
    if _support_relations(e, _display_names(e)):
        return True
    start = body_positions(env)
    for _ in range(settings.LIBERO_NUM_STEPS_WAIT):
        env.step(NOOP)
    pos = body_positions(env)
    ids = list(pos)
    if any(np.linalg.norm(pos[k] - start[k]) > settings.CUSTOM_TASK_MAX_SETTLE_MOVE for k in ids):
        return True
    if any(np.linalg.norm(pos[a][:2] - pos[b][:2]) < min_distance for i, a in enumerate(ids) for b in ids[i + 1 :]):
        return True
    if _support_relations(e, _display_names(e)):
        return True
    owners = sorted([*e.objects_dict, *e.fixtures_dict], key=len, reverse=True)
    model, data = e.sim.model._model, e.sim.data._data

    def owner(geom: int) -> str | None:
        body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, model.geom_bodyid[geom]) or ""
        return next((o for o in owners if body.startswith(o)), None)

    for c in data.contact[: data.ncon]:
        a, b = owner(c.geom1), owner(c.geom2)
        if a and b and a != b and (a in e.objects_dict or b in e.objects_dict) and "table" not in a + b:
            return True
    return False
