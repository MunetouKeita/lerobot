"""既存の LIBERO タスクの BDDL を元に、物体の配置を変えた自作タスクを作る。

1. 元の BDDL の配置範囲（:regions の :ranges）を書き換えて custom_tasks/<スイート>/<名前>.bddl に保存する
2. reset（配置のサンプリング）→ 何もしない動作で物体を落ち着かせ、問題のない配置だけを初期状態として集める
   - 物体が落ち着いた後も動いている、または配置の直後から水平方向に大きく動いた（固定物と重なって押し出された・倒れた）ものは除く
3. 対象物体の見え方（agentview・手首カメラから、遮っている物体をどけた場合に対して表面の何 % が直接見えるか）を測る
4. 初期状態（.pruned_init）と tasks.json を保存し、スイートの全タスクを複数の視点で描画した確認用の画像
   （previews/overview.png、visualization/scene_overview.py）を作り直す

    uv run python vla3dsg/scripts/make_custom_task.py --suite vla3dsg_hidden --name <タスク名> \\
        --base libero_spatial/<元のタスク名> --language "<指示文>" \\
        --region akita_black_bowl_1_region=-0.30,-0.34,-0.28,-0.32 --target akita_black_bowl_1 --occluder wooden_cabinet_1

--preview を付けると、初期状態を 1 件だけ作って画像と見え方を tmp/ に保存する（custom_tasks/ には書かない）。
--overview だけを付けると、タスクは作らず確認用の画像だけを作り直す（例: --suite vla3dsg_hidden --overview）。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero import get_libero_path  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from PIL import Image  # noqa: E402

from vla3dsg.envs.custom_task_builder import (  # noqa: E402
    body_positions,
    remove_object,
    sample_init_state,
    set_region_range,
    visibility,
)
from vla3dsg.visualization.scene_overview import render_overview  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True)
    parser.add_argument("--name", help="タスク名（ファイル名にも使う）")
    parser.add_argument(
        "--base", help="元のタスク。LIBERO のタスク（<スイート>/<タスク名>）か、custom_tasks/ からの BDDL のパス（例: vla3dsg_occluded/scene.bddl）"
    )
    parser.add_argument("--language", help="ポリシーに渡す指示文")
    parser.add_argument("--location-language", help="場所を書いた指示文（プロンプト条件 P1 で使う。--language に場所を書かない場合）")
    parser.add_argument("--region", action="append", default=[], help="<領域名>=x_min,y_min,x_max,y_max（複数可）")
    parser.add_argument("--remove-object", action="append", default=[], help="シーンから取り除く物体（例: akita_black_bowl_2。複数可）")
    parser.add_argument("--target", help="見え方を測る対象物体（例: akita_black_bowl_1）")
    parser.add_argument("--occluder", help="対象を遮っている固定物（見え方の比較用）")
    parser.add_argument("--max-steps", type=int, default=settings.CUSTOM_TASK_MAX_STEPS)
    parser.add_argument("--n-init", type=int, default=settings.CUSTOM_TASK_N_INIT)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--overview", action="store_true", help="確認用の画像だけを作り直す")
    args = parser.parse_args()
    if args.overview:
        print(f"saved: {render_overview(args.suite)}")
        return
    for required in ("name", "base", "language", "target"):
        if getattr(args, required) is None:
            parser.error(f"--{required} が必要")

    if args.base.endswith(".bddl"):
        bddl = (settings.CUSTOM_TASKS_DIR / args.base).read_text()
    else:
        base_suite, base_task = args.base.split("/")
        bddl = (Path(get_libero_path("bddl_files")) / base_suite / f"{base_task}.bddl").read_text()
    for obj_id in args.remove_object:
        bddl = remove_object(bddl, obj_id)
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
    if args.preview:
        for cam, img in first["images"].items():
            Image.fromarray(img).save(out_dir / f"{args.name}_{cam}.png")
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
                **({"language_with_location": args.location_language} if args.location_language else {}),
                "bddl_file": f"{args.name}.bddl",
                "init_states_file": f"{args.name}.pruned_init",
                "base": args.base,
                "regions": args.region,
                "removed_objects": args.remove_object,
                "visibility": stats,
            }
        ]
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
        print(f"saved: {render_overview(args.suite)}")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"saved: {out_dir}")


if __name__ == "__main__":
    main()
