"""LIBERO 環境が EGL のヘッドレス描画で起動し、カメラ画像を保存できるかを確認する。

lerobot-eval と同じく LeRobot の LiberoEnv 設定から環境を作る。

    uv run python vla3dsg/scripts/test_libero_env.py [--suite libero_goal] [--task-id 0]
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.envs.configs import LiberoEnv  # noqa: E402
from lerobot.envs.libero import get_libero_dummy_action  # noqa: E402

N_STEPS = 20


def check_image(name: str, img: np.ndarray, size: int) -> None:
    assert img.shape == (size, size, 3), f"{name}: shape {img.shape}"
    assert img.dtype == np.uint8, f"{name}: dtype {img.dtype}"
    # 真っ黒・単色の画像は描画失敗とみなす
    assert img.std() > 1.0, f"{name}: 画像がほぼ単色（std={img.std():.2f}）"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    args = parser.parse_args()

    size = settings.LIBERO_OBS_SIZE
    cfg = LiberoEnv(
        task=args.suite,
        task_ids=[args.task_id],
        observation_height=size,
        observation_width=size,
        camera_name_mapping=settings.LIBERO_CAMERA_NAME_MAPPING,
    )
    envs = cfg.create_envs(n_envs=1, use_async_envs=False)
    vec_env = envs[args.suite][args.task_id]
    inner = vec_env.envs[0]
    print(f"task: {inner.task}\ninstruction: {inner.task_description}")

    t0 = time.perf_counter()
    obs, _ = vec_env.reset(seed=settings.SEED)
    print(f"reset: {time.perf_counter() - t0:.2f}s")

    cam_names = list(settings.LIBERO_CAMERA_NAME_MAPPING.values())
    for name in cam_names:
        check_image(name, obs["pixels"][name][0], size)

    action = np.asarray([get_libero_dummy_action()], dtype=np.float32)
    t0 = time.perf_counter()
    for _ in range(N_STEPS):
        obs, _, terminated, _, _ = vec_env.step(action)
        assert not terminated[0], "no-op 動作中にエピソードが終了した"
    print(f"step: {(time.perf_counter() - t0) / N_STEPS * 1000:.1f}ms/step")

    out_dir = settings.OUTPUTS_DIR / "test_libero_env" / f"{args.suite}_task{args.task_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in cam_names:
        img = obs["pixels"][name][0]
        check_image(name, img, size)
        # LIBERO の生画像は上下左右が反転しているため、LiberoProcessorStep と同様に180度回転する
        Image.fromarray(np.ascontiguousarray(img[::-1, ::-1])).save(out_dir / f"{name}.png")
    print(f"saved: {out_dir}")

    state = obs["robot_state"]
    print(f"eef_pos: {state['eef']['pos'][0]}, gripper_qpos: {state['gripper']['qpos'][0]}")
    vec_env.close()
    print("OK")


if __name__ == "__main__":
    main()
