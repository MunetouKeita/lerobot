"""環境まわりを確認する。

1. LIBERO が EGL のヘッドレス描画で起動し、カメラ画像を保存できる（LeRobot の LiberoEnv 設定から作る）
2. 環境タイプ `libero_vla3dsg` がプラグインとして読み込め、`num_steps_wait` が環境まで届く
3. 自作スイート（custom_tasks/）が LeRobot から読み込め、最大ステップ数・指示文・初期状態が正しい。開始時の SG を表示する

    uv run python vla3dsg/tests/test_envs.py [--suite libero_goal] [--task-id 0] [--custom-suite vla3dsg_goal]

画像は tmp/test_envs/ に保存する。
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
from libero.libero import benchmark  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.configs.parser import load_plugin  # noqa: E402
from lerobot.envs.configs import EnvConfig, LiberoEnv  # noqa: E402
from lerobot.envs.libero import get_libero_dummy_action  # noqa: E402

from vla3dsg.envs.libero_vla3dsg import make_env, parse_config  # noqa: E402
from vla3dsg.scene_graph import textify  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402

N_STEPS = 20
OUT_DIR = settings.TMP_DIR / "test_envs"


def save_image(img: np.ndarray, path: Path) -> None:
    # LIBERO の生画像は上下左右が反転しているため、LiberoProcessorStep と同様に 180 度回転する
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(img[::-1, ::-1])).save(path)


def check_image(name: str, img: np.ndarray, size: int) -> None:
    assert img.shape == (size, size, 3), f"{name}: shape {img.shape}"
    assert img.dtype == np.uint8, f"{name}: dtype {img.dtype}"
    # 真っ黒・単色の画像は描画失敗とみなす
    assert img.std() > 1.0, f"{name}: 画像がほぼ単色（std={img.std():.2f}）"


def check_rendering(suite: str, task_id: int) -> None:
    size = settings.LIBERO_OBS_SIZE
    cfg = LiberoEnv(
        task=suite,
        task_ids=[task_id],
        observation_height=size,
        observation_width=size,
        camera_name_mapping=settings.LIBERO_CAMERA_NAME_MAPPING,
    )
    vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[suite][task_id]
    print(f"task: {vec_env.envs[0].task}\ninstruction: {vec_env.envs[0].task_description}")
    t0 = time.perf_counter()
    obs, _ = vec_env.reset(seed=settings.SEED)
    print(f"reset: {time.perf_counter() - t0:.2f}s")

    action = np.asarray([get_libero_dummy_action()], dtype=np.float32)
    t0 = time.perf_counter()
    for _ in range(N_STEPS):
        obs, _, terminated, _, _ = vec_env.step(action)
        assert not terminated[0], "no-op 動作中にエピソードが終了した"
    print(f"step: {(time.perf_counter() - t0) / N_STEPS * 1000:.1f}ms/step")
    for name in settings.LIBERO_CAMERA_NAME_MAPPING.values():
        img = obs["pixels"][name][0]
        check_image(name, img, size)
        save_image(img, OUT_DIR / "rendering" / f"{suite}_{task_id}_{name}.png")
    state = obs["robot_state"]
    print(f"eef_pos: {state['eef']['pos'][0]}, gripper_qpos: {state['gripper']['qpos'][0]}")
    vec_env.close()
    print("rendering: OK")


def check_env_type(suite: str, task_id: int) -> None:
    assert "libero_vla3dsg" in EnvConfig.get_known_choices()
    cfg = parse_config(suite, f"task_ids=[{task_id}]")
    assert cfg.num_steps_wait == settings.LIBERO_NUM_STEPS_WAIT
    assert cfg.gym_kwargs["num_steps_wait"] == settings.LIBERO_NUM_STEPS_WAIT
    assert parse_config(suite, "num_steps_wait=10").num_steps_wait == 10

    # 環境まで値が届き、待ちステップを増やすと reset 直後の動きが小さくなること
    speeds = {}
    for n in (10, settings.LIBERO_NUM_STEPS_WAIT):
        vec_env = make_env(suite, task_id, f"num_steps_wait={n}")
        vec_env.reset(seed=settings.SEED)
        inner = vec_env.envs[0]
        assert inner.num_steps_wait == n, f"env.num_steps_wait={inner.num_steps_wait}, expected {n}"
        speeds[n] = float(np.abs(inner._env.env.sim.data.qvel).max())
        vec_env.close()
        print(f"num_steps_wait={n}: max |qvel| after reset = {speeds[n]:.2e}")
    assert speeds[settings.LIBERO_NUM_STEPS_WAIT] <= speeds[10]
    print("env type: OK")


def check_custom_suite(suite: str) -> None:
    assert suite in benchmark.get_benchmark_dict(), "自作スイートが登録されていない"
    spec = json.loads((settings.CUSTOM_TASKS_DIR / suite / "tasks.json").read_text())
    for task_id, task in enumerate(spec["tasks"]):
        cfg = parse_config(suite, f"task_ids=[{task_id}]")
        assert cfg.episode_length == spec["max_steps"], cfg.episode_length
        vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[suite][task_id]
        inner = vec_env.envs[0]
        assert inner._max_episode_steps == spec["max_steps"]
        assert inner.task_description == task["language"]
        assert inner._init_states.shape[0] == settings.CUSTOM_TASK_N_INIT
        assert Path(inner._task_bddl_file).parent == settings.CUSTOM_TASKS_DIR / suite

        obs, _ = vec_env.reset(seed=settings.SEED)
        sg = build_scene_graph(inner._env.env)
        print(f"task {task_id}: {task['language']}")
        print(f"  visibility: {task['visibility'].get('agentview_visible_ratio')}")
        print(f"  {textify.to_triples(sg)}")
        save_image(obs["pixels"]["image"][0], OUT_DIR / "custom_suite" / f"{task['name']}.png")
        vec_env.close()
    print("custom suite: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--custom-suite", default="vla3dsg_goal")
    args = parser.parse_args()

    load_plugin("vla3dsg.envs")
    check_rendering(args.suite, args.task_id)
    check_env_type(args.suite, args.task_id)
    check_custom_suite(args.custom_suite)
    print(f"saved: {OUT_DIR}")
    print("OK")


if __name__ == "__main__":
    main()
