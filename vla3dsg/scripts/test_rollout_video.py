"""可視化用の render 差し替え（visualization/rollout_video.py）を確認する。

    uv run python vla3dsg/scripts/test_rollout_video.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.envs.configs import LiberoEnv as LiberoEnvConfig  # noqa: E402
from lerobot.envs.libero import get_libero_dummy_action  # noqa: E402

from vla3dsg.visualization import rollout_video  # noqa: E402

SUITE = "libero_goal"
TASK_ID = 0


def main() -> None:
    rollout_video.install()
    size = settings.LIBERO_OBS_SIZE
    cfg = LiberoEnvConfig(task=SUITE, task_ids=[TASK_ID], camera_name_mapping=settings.LIBERO_CAMERA_NAME_MAPPING)
    vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[SUITE][TASK_ID]
    assert vec_env.metadata["render_fps"] == settings.LIBERO_CONTROL_FPS, vec_env.metadata

    vec_env.reset(seed=settings.SEED)
    action = np.asarray([get_libero_dummy_action()], dtype=np.float32)
    for _ in range(3):
        vec_env.step(action)
    inner = vec_env.envs[0]
    frame = inner.render()
    assert frame.shape == (size, size * 2, 3), frame.shape
    assert frame.dtype == np.uint8
    assert inner._vis_step == 3 and not inner._vis_done
    assert not rollout_video._final_frames

    # 終了したエピソードの最後のフレームが保持されること
    inner._vis_done = True
    inner.render()
    inner.render()
    assert len(rollout_video._final_frames) == 1
    rollout_video._final_frames.clear()

    out = settings.TMP_DIR / "test_rollout_video" / "frame.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(frame).save(out)
    print(f"saved: {out}")
    vec_env.close()
    print("OK")


if __name__ == "__main__":
    main()
