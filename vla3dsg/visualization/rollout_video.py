"""lerobot-eval が保存するロールアウト動画を、確認しやすい形に差し替える。

LeRobot の LiberoEnv の render / reset / step を差し替え、agentview と手首カメラを横に並べたフレームを返す。
動画の fps も制御周期（実時間）に合わせる。LeRobot 本体のファイルは変更しない。

lerobot-eval は動画を書き出すときに終了ステップのフレームを落とす
（`stacked_frames[: done_index + 1]` で、reset 直後のフレームの分だけずれる）。
終了時のフレームを保持し、write_video の差し替えで末尾に足す。eval.batch_size=1 が前提。
"""

from collections import deque
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from lerobot.envs.libero import LiberoEnv
from lerobot.scripts import lerobot_eval

from vla3dsg.config import settings

_installed = False
# 終了したエピソードの最後のフレーム（終了順）
_final_frames: deque[np.ndarray] = deque()


def compose_frame(agentview: np.ndarray, wrist: np.ndarray) -> np.ndarray:
    """2 視点の画像（LIBERO の生画像、上下左右反転のまま）を横に並べる。"""
    # LIBERO の生画像は 180 度回転しているため戻す
    views = [np.ascontiguousarray(img[::-1, ::-1]) for img in (agentview, wrist)]
    h, w = views[0].shape[:2]
    canvas = Image.new("RGB", (w * 2, h))
    for i, view in enumerate(views):
        canvas.paste(Image.fromarray(view), (w * i, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=12)
    draw.text((8, 4), "agentview", fill=(255, 255, 0), font=font)
    draw.text((w + 8, 4), "wrist", fill=(255, 255, 0), font=font)
    return np.asarray(canvas)


def install() -> None:
    """LiberoEnv を差し替える。環境を作る前に呼ぶこと。"""
    global _installed
    if _installed:
        return
    _installed = True

    orig_reset = LiberoEnv.reset
    orig_step = LiberoEnv.step
    orig_write_video = lerobot_eval.write_video

    def reset(self: LiberoEnv, *args: Any, **kwargs: Any) -> Any:
        out = orig_reset(self, *args, **kwargs)
        self._vis_step = 0
        self._vis_done = False
        self._vis_final_saved = False
        return out

    def step(self: LiberoEnv, action: np.ndarray) -> Any:
        out = orig_step(self, action)
        self._vis_step += 1
        terminated, truncated = out[2], out[3]
        self._vis_done = bool(terminated or truncated or self._vis_step >= self._max_episode_steps)
        return out

    def render(self: LiberoEnv) -> np.ndarray:
        self._ensure_env()
        raw = self._env.env._get_observations()
        frame = compose_frame(raw["agentview_image"], raw["robot0_eye_in_hand_image"])
        if getattr(self, "_vis_done", False) and not self._vis_final_saved:
            _final_frames.append(frame)
            self._vis_final_saved = True
        return frame

    def write_video(video_path: Any, stacked_frames: Any, fps: int) -> None:
        frames = list(stacked_frames)
        if _final_frames:
            frames.append(_final_frames.popleft())
        orig_write_video(video_path, frames, fps)

    LiberoEnv.reset = reset
    LiberoEnv.step = step
    LiberoEnv.render = render
    lerobot_eval.write_video = write_video
    # lerobot-eval は render_fps で動画を書き出す（既定の 80 は実時間の 4 倍速になる）
    LiberoEnv.metadata = {**LiberoEnv.metadata, "render_fps": settings.LIBERO_CONTROL_FPS}
