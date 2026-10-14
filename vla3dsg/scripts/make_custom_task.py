"""既存の LIBERO タスクの BDDL を元に、物体の配置を変えた自作タスクを作る。

1. 元の BDDL の配置範囲（:regions の :ranges）を書き換えて custom_tasks/<スイート>/<名前>.bddl に保存する
2. reset（配置のサンプリング）→ 何もしない動作で物体を落ち着かせ、問題のない配置だけを初期状態として集める
   - 物体が落ち着いた後も動いている、または配置の直後から水平方向に大きく動いた（固定物と重なって押し出された・倒れた）ものは除く
3. 対象物体の見え方（agentview・手首カメラから、遮っている物体をどけた場合に対して表面の何 % が直接見えるか）を測る
4. 初期状態（.pruned_init）、tasks.json、確認用の画像（previews/）を保存する

    uv run python vla3dsg/scripts/make_custom_task.py --suite vla3dsg_hidden --name <タスク名> \\
        --base libero_spatial/<元のタスク名> --language "<指示文>" \\
        --region akita_black_bowl_1_region=-0.30,-0.34,-0.28,-0.32 --target akita_black_bowl_1 --occluder wooden_cabinet_1

--preview を付けると、初期状態を 1 件だけ作って画像と見え方を tmp/ に保存する（custom_tasks/ には書かない）。
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero import get_libero_path  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from PIL import Image  # noqa: E402

from vla3dsg.demos.placement import body_positions, sample_init_state  # noqa: E402

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True)
    parser.add_argument("--name", required=True, help="タスク名（ファイル名にも使う）")
    parser.add_argument("--base", required=True, help="元のタスク（<スイート>/<タスク名>）")
    parser.add_argument("--language", required=True, help="ポリシーに渡す指示文")
    parser.add_argument("--region", action="append", default=[], help="<領域名>=x_min,y_min,x_max,y_max（複数可）")
    parser.add_argument("--target", required=True, help="見え方を測る対象物体（例: akita_black_bowl_1）")
    parser.add_argument("--occluder", help="対象を遮っている固定物（見え方の比較用）")
    parser.add_argument("--max-steps", type=int, default=settings.CUSTOM_TASK_MAX_STEPS)
    parser.add_argument("--n-init", type=int, default=settings.CUSTOM_TASK_N_INIT)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    base_suite, base_task = args.base.split("/")
    bddl = (Path(get_libero_path("bddl_files")) / base_suite / f"{base_task}.bddl").read_text()
    for spec in args.region:
        region, values = spec.split("=")
        bddl = set_region_range(bddl, region, tuple(float(v) for v in values.split(",")))

    out_dir = settings.TMP_DIR / "make_custom_task" / args.name if args.preview else settings.CUSTOM_TASKS_DIR / args.suite
    out_dir.mkdir(parents=True, exist_ok=True)
    bddl_path = out_dir / f"{args.name}.bddl"
    bddl_path.write_text(bddl)

    size = settings.LIBERO_OBS_SIZE
    env = OffScreenRenderEnv(bddl_file_name=str(bddl_path), camera_heights=size, camera_widths=size)
    n_target = 1 if args.preview else args.n_init
    states, vis_list, rejected = [], [], 0
    seed = 0
    while len(states) < n_target:
        if seed >= n_target * settings.CUSTOM_TASK_MAX_TRIALS_FACTOR:
            raise RuntimeError(f"有効な配置が集まらない（{len(states)}/{n_target}、除外 {rejected}）。配置範囲を見直すこと")
        state = sample_init_state(env, seed)
        seed += 1
        if state is None:
            rejected += 1
            continue
        states.append(state)
        vis_list.append(visibility(env, args.target, args.occluder))

    first = vis_list[0]
    image_dir = out_dir if args.preview else out_dir / "previews"
    image_dir.mkdir(exist_ok=True)
    for cam, img in first["images"].items():
        Image.fromarray(img).save(image_dir / f"{args.name}_{cam}.png")
    stats = {
        "target": args.target,
        "occluder": args.occluder,
        "n_init": len(states),
        "n_rejected": rejected,
        "target_position_last": [round(float(v), 3) for v in body_positions(env)[args.target]],
    }
    if args.occluder:
        ratios = [v["visible_ratio"]["agentview"] for v in vis_list if v["visible_ratio"]["agentview"] is not None]
        stats["agentview_visible_ratio"] = {"mean": round(float(np.mean(ratios)), 3), "max": round(float(np.max(ratios)), 3)}
        stats["wrist_visible_ratio_first"] = first["visible_ratio"]["robot0_eye_in_hand"]
    stats["visible_points_first"] = first["visible_points"]
    env.close()

    if not args.preview:
        torch.save(np.stack(states), out_dir / f"{args.name}.pruned_init")
        spec_path = out_dir / "tasks.json"
        spec = json.loads(spec_path.read_text()) if spec_path.exists() else {"max_steps": args.max_steps, "tasks": []}
        spec["max_steps"] = args.max_steps
        spec["tasks"] = [t for t in spec["tasks"] if t["name"] != args.name] + [
            {
                "name": args.name,
                "language": args.language,
                "bddl_file": f"{args.name}.bddl",
                "init_states_file": f"{args.name}.pruned_init",
                "base": args.base,
                "regions": args.region,
                "visibility": stats,
            }
        ]
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"saved: {out_dir}")


if __name__ == "__main__":
    main()
