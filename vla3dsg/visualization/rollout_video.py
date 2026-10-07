"""lerobot-eval が保存するロールアウト動画を、確認しやすい形に差し替える。

LeRobot の LiberoEnv の render / reset / step を差し替え、
agentview と手首カメラを横に並べ、指示文・ステップ数・成否を重ねたフレームを返す。
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

HEADER_H = 64
COLORS = {"RUNNING": (230, 230, 230), "SUCCESS": (80, 220, 100), "TIMEOUT": (240, 80, 80)}

_installed = False
# 終了したエピソードの最後のフレーム（終了順）
_final_frames: deque[np.ndarray] = deque()


def _font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _fit(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: float) -> str:
    """幅に収まらない文字列を末尾 "..." で切り詰める。"""
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "...", font=font) > max_w:
        text = text[:-1]
    return text + "..."


def compose_frame(
    agentview: np.ndarray, wrist: np.ndarray, title: str, instruction: str, step: int, max_steps: int, status: str
) -> np.ndarray:
    """2 視点の画像（LIBERO の生画像、上下左右反転のまま）から表示用フレームを作る。"""
    # LIBERO の生画像は 180 度回転しているため戻す
    views = [np.ascontiguousarray(img[::-1, ::-1]) for img in (agentview, wrist)]
    h, w = views[0].shape[:2]
    canvas = Image.new("RGB", (w * 2, h + HEADER_H), (20, 20, 20))
    for i, view in enumerate(views):
        canvas.paste(Image.fromarray(view), (w * i, HEADER_H))
    draw = ImageDraw.Draw(canvas)
    step_text = f"step {step}/{max_steps}"
    title = _fit(draw, title, _font(14), w * 2 - 24 - draw.textlength(step_text, font=_font(14)))
    # 状態表示は最長の "TIMEOUT"・"RUNNING" の幅を空けておく
    status_w = max(draw.textlength(t, font=_font(18)) for t in COLORS)
    instruction = _fit(draw, instruction, _font(18), w * 2 - 32 - status_w)
    draw.text((8, 6), title, fill=(170, 170, 170), font=_font(14))
    draw.text((8, 26), instruction, fill=(255, 255, 255), font=_font(18))
    draw.text((w * 2 - 8, 6), step_text, fill=(170, 170, 170), font=_font(14), anchor="ra")
    draw.text((w * 2 - 8, 26), status, fill=COLORS[status], font=_font(18), anchor="ra")
    draw.text((8, HEADER_H + 4), "agentview", fill=(255, 255, 0), font=_font(12))
    draw.text((w + 8, HEADER_H + 4), "wrist", fill=(255, 255, 0), font=_font(12))
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
        self._vis_success = False
        self._vis_final_saved = False
        return out

    def step(self: LiberoEnv, action: np.ndarray) -> Any:
        out = orig_step(self, action)
        self._vis_step += 1
        self._vis_success = self._vis_success or bool(out[4].get("is_success", False))
        return out

    def render(self: LiberoEnv) -> np.ndarray:
        self._ensure_env()
        raw = self._env.env._get_observations()
        step_i = getattr(self, "_vis_step", 0)
        if getattr(self, "_vis_success", False):
            status = "SUCCESS"
        elif step_i >= self._max_episode_steps:
            status = "TIMEOUT"
        else:
            status = "RUNNING"
        frame = compose_frame(
            raw["agentview_image"],
            raw["robot0_eye_in_hand_image"],
            title=f"task {self.task_id}: {self.task}",
            instruction=self.task_description,
            step=step_i,
            max_steps=self._max_episode_steps,
            status=status,
        )
        if status != "RUNNING" and not getattr(self, "_vis_final_saved", True):
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
