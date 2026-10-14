"""自作タスクで、対象物体を掴んで置き場所へ運ぶ動作が物理的にできるかを、スクリプト制御で確かめる。

シミュレータの正解の位置へ手先を動かす（姿勢は初期のまま、位置の誤差に比例した移動量の指令）。
上から近づいて縁を掴み、持ち上げ、経由点（--via）を通って置き場所の上へ運び、放す。成否は BDDL の成功条件で判定する。

    uv run python vla3dsg/scripts/scripted_pick_place.py --name phase4/scripted_hidden_cabinet \\
        --suite vla3dsg_hidden --task-id 0 --target akita_black_bowl_1 --dest plate_1 --via=-0.25,0.0

結果は results/<name>/（summary.json、videos/ に先頭 --n-video 本の動画）。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import imageio  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from libero.libero.envs import OffScreenRenderEnv  # noqa: E402

from vla3dsg.scripts.run_eval import git_info  # noqa: E402

OPEN, CLOSE = -1.0, 1.0
NOOP = [0, 0, 0, 0, 0, 0, OPEN]


class Runner:
    def __init__(self, env: OffScreenRenderEnv, record: bool):
        self.env, self.record = env, record
        self.frames: list[np.ndarray] = []
        self.steps = 0
        self.done = False  # LIBERO は成功した時点でエピソードを終え、以降の動作指令はエラーになる
        self.obs: dict = {}

    def pos(self, name: str) -> np.ndarray:
        e = self.env.env
        return np.array(e.sim.data.body_xpos[e.obj_body_id[name]])

    def step(self, action: list[float] | np.ndarray) -> None:
        if self.done:
            return
        self.obs, _, self.done, _ = self.env.step(action)
        self.steps += 1
        if self.record:
            views = [self.obs[f"{c}_image"][::-1, ::-1] for c in ("agentview", "robot0_eye_in_hand")]
            self.frames.append(np.concatenate(views, axis=1))

    def go(self, target: np.ndarray, grip: float, max_steps: int = 150) -> None:
        for _ in range(max_steps):
            err = target - self.obs["robot0_eef_pos"]
            if self.done or np.linalg.norm(err) < settings.SCRIPTED_TOL:
                return
            self.step(np.r_[np.clip(err * settings.SCRIPTED_GAIN, -1, 1), 0, 0, 0, grip])

    def hold(self, grip: float, n: int) -> None:
        for _ in range(n):
            self.step([0, 0, 0, 0, 0, 0, grip])


def run_episode(env: OffScreenRenderEnv, init_state: np.ndarray, args: argparse.Namespace, record: bool) -> tuple[dict, list]:
    env.reset()
    r = Runner(env, record)
    r.obs = env.set_init_state(init_state)
    for _ in range(settings.LIBERO_NUM_STEPS_WAIT):
        r.obs, *_ = env.step(NOOP)

    start = r.pos(args.target)
    grasp = start + np.array(settings.SCRIPTED_GRASP_OFFSET)
    r.go(grasp + [0, 0, settings.SCRIPTED_APPROACH_DZ], OPEN)
    r.go(grasp, OPEN)
    r.hold(CLOSE, 15)
    r.go(grasp + [0, 0, settings.SCRIPTED_LIFT_DZ], CLOSE)
    lifted = float(r.pos(args.target)[2] - start[2])
    offset = (r.obs["robot0_eef_pos"] - r.pos(args.target))[:2]  # 掴んだ後の手先と対象のずれ
    for x, y in args.via:
        r.go(np.r_[x, y, grasp[2] + settings.SCRIPTED_VIA_DZ], CLOSE)
    dest = r.pos(args.dest)
    r.go(np.r_[dest[:2] + offset, grasp[2] + settings.SCRIPTED_LIFT_DZ], CLOSE)
    r.go(np.r_[dest[:2] + offset, grasp[2] + settings.SCRIPTED_RELEASE_DZ], CLOSE)
    r.hold(OPEN, 15)
    r.go(np.r_[dest[:2], grasp[2] + settings.SCRIPTED_VIA_DZ], OPEN, max_steps=30)
    r.hold(OPEN, 20)
    result = {
        "success": bool(r.done or env.env._check_success()),
        "lifted_m": round(lifted, 3),
        "steps": r.steps,  # 成功した場合は成功するまでのステップ数（物体が落ち着くまでの待機を除く）
    }
    return result, r.frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="結果の保存先（results/<name>/）")
    parser.add_argument("--suite", required=True, help="自作スイート（custom_tasks/<suite>/）")
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--target", required=True, help="掴む物体（例: akita_black_bowl_1）")
    parser.add_argument("--dest", required=True, help="置き場所の物体（例: plate_1）")
    parser.add_argument("--via", action="append", default=[], help="運ぶ途中の経由点 x,y（世界座標、複数可。負の値は --via=x,y と書く）")
    parser.add_argument("--n-init", type=int, default=settings.CUSTOM_TASK_N_INIT)
    parser.add_argument("--n-video", type=int, default=3)
    args = parser.parse_args()
    args.via = [tuple(float(v) for v in p.split(",")) for p in args.via]

    res_dir = settings.RESULTS_DIR / args.name
    if res_dir.exists():
        raise FileExistsError(f"{res_dir} は既にある（上書きしない）")
    (res_dir / "videos").mkdir(parents=True)

    suite_dir = settings.CUSTOM_TASKS_DIR / args.suite
    task = json.loads((suite_dir / "tasks.json").read_text())["tasks"][args.task_id]
    size = settings.LIBERO_OBS_SIZE
    env = OffScreenRenderEnv(bddl_file_name=str(suite_dir / task["bddl_file"]), camera_heights=size, camera_widths=size)
    init_states = torch.load(suite_dir / task["init_states_file"], weights_only=False)

    episodes = []
    for i in range(min(args.n_init, len(init_states))):
        result, frames = run_episode(env, init_states[i], args, record=i < args.n_video)
        episodes.append({"init_state": i, **result})
        if frames:
            imageio.mimsave(res_dir / "videos" / f"episode_{i}.mp4", frames, fps=settings.LIBERO_CONTROL_FPS)
        print(episodes[-1])
    env.close()

    n_success = sum(e["success"] for e in episodes)
    summary = {
        "suite": args.suite,
        "task_id": args.task_id,
        "instruction": task["language"],
        "n_success": n_success,
        "n_episodes": len(episodes),
        "steps_max": max(e["steps"] for e in episodes),
        "episodes": episodes,
    }
    conditions = {
        "args": {k: v for k, v in vars(args).items() if k != "name"},
        "controller": {k: getattr(settings, k) for k in dir(settings) if k.startswith("SCRIPTED_")},
        "git": git_info(),
    }
    (res_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (res_dir / "conditions.json").write_text(json.dumps(conditions, indent=2, ensure_ascii=False))
    print(f"{n_success}/{len(episodes)} saved: {res_dir}")


if __name__ == "__main__":
    main()
