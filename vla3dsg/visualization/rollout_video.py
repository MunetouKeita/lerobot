"""lerobot-eval が保存するロールアウト動画を、確認しやすい形に差し替える。

LeRobot の LiberoEnv の render / reset / step を差し替え、agentview と手首カメラを横に並べたフレームを返す。
動画の fps も制御周期（実時間）に合わせる。LeRobot 本体のファイルは変更しない。

lerobot-eval は動画を書き出すときに終了ステップのフレームを落とす
（`stacked_frames[: done_index + 1]` で、reset 直後のフレームの分だけずれる）。
終了時のフレームを保持し、write_video の差し替えで末尾に足す。eval.batch_size=1 が前提。

保存する動画: lerobot-eval は 1 タスクあたり先頭 10 本しか描画しない（本数はコード内で固定）。
全エピソードを描画させ、各タスクの先頭 VIDEO_SAVE_FIRST_N 本と、それ以降の失敗エピソードだけを書き出す。
"""

import re
from collections import deque
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from lerobot.envs.libero import LiberoEnv
from lerobot.scripts import lerobot_eval

from vla3dsg.config import settings

_installed = False
# 終了したエピソードの (最後のフレーム, 成功したか)（終了順）
_final_frames: deque[tuple[np.ndarray, bool]] = deque()
_EPISODE_INDEX = re.compile(r"eval_episode_(\d+)\.mp4$")


def should_save(episode_index: int, success: bool) -> bool:
    if episode_index < settings.VIDEO_SAVE_FIRST_N:
        return True
    return settings.VIDEO_SAVE_FAILURES and not success


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
    orig_eval_policy_all = lerobot_eval.eval_policy_all

    def reset(self: LiberoEnv, *args: Any, **kwargs: Any) -> Any:
        out = orig_reset(self, *args, **kwargs)
        self._vis_step = 0
        self._vis_done = False
        self._vis_success = False
        self._vis_final_saved = False
        return out

    def step(self: LiberoEnv, action: np.ndarray) -> Any:
        out = orig_step(self, action)
        self._vis_step += 1
        terminated, truncated = out[2], out[3]
        self._vis_success = self._vis_success or bool(out[4].get("is_success", False))
        self._vis_done = bool(terminated or truncated or self._vis_step >= self._max_episode_steps)
        return out

    def render(self: LiberoEnv) -> np.ndarray:
        self._ensure_env()
        raw = self._env.env._get_observations()
        frame = compose_frame(raw["agentview_image"], raw["robot0_eye_in_hand_image"])
        if getattr(self, "_vis_done", False) and not self._vis_final_saved:
            _final_frames.append((frame, self._vis_success))
            self._vis_final_saved = True
        return frame

    def write_video(video_path: Any, stacked_frames: Any, fps: int) -> None:
        frames = list(stacked_frames)
        success = True
        if _final_frames:
            final_frame, success = _final_frames.popleft()
            frames.append(final_frame)
        match = _EPISODE_INDEX.search(str(video_path))
        if match and not should_save(int(match.group(1)), success):
            return
        orig_write_video(video_path, frames, fps)

    def eval_policy_all(*args: Any, **kwargs: Any) -> Any:
        # 全エピソードを描画させる（保存するかは write_video で決める）
        if kwargs.get("max_episodes_rendered", 0) > 0:
            kwargs["max_episodes_rendered"] = 10**9
        return orig_eval_policy_all(*args, **kwargs)

    LiberoEnv.reset = reset
    LiberoEnv.step = step
    LiberoEnv.render = render
    lerobot_eval.write_video = write_video
    lerobot_eval.eval_policy_all = eval_policy_all
    # lerobot-eval は render_fps で動画を書き出す（既定の 80 は実時間の 4 倍速になる）
    LiberoEnv.metadata = {**LiberoEnv.metadata, "render_fps": settings.LIBERO_CONTROL_FPS}
