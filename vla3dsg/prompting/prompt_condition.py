"""プロンプト条件に従って、エピソードごとに指示文を差し替える。

LeRobot の LiberoEnv.reset を差し替え、reset 後（物体が落ち着いた後）のシミュレータの状態から SG を作り、
`task_description`（lerobot-eval がポリシーに渡す指示文）を書き換える。LeRobot 本体のファイルは変更しない。
エピソードの終了時（成功または最大ステップ数）の SG も記録し、どの物体をどこに置いたかを後から分類できるようにする。

MolmoAct2 の前処理の正規化は SG のテキスト（JSON の括弧など）を壊すため、評価では
`--policy.normalize_language=false` とし、元の指示文だけをここで同じ関数で正規化する。
"""

import re
import zlib
from functools import cache
from typing import Any

import numpy as np
from transformers import AutoTokenizer

from lerobot.envs.libero import LiberoEnv
from lerobot.policies.molmoact2.processor_molmoact2 import _normalize_question_text

from vla3dsg.config import settings
from vla3dsg.scene_graph import textify
from vla3dsg.scene_graph.builder import SceneGraph, build_scene_graph

_installed = False
# 実際に使ったプロンプトの記録（run_eval.py が prompts.jsonl に保存する）
records: list[dict[str, Any]] = []


@cache
def _tokenizer() -> Any:
    return AutoTokenizer.from_pretrained(settings.MOLMOACT2_CHECKPOINT)


def count_tokens(text: str) -> int:
    """MolmoAct2 のトークナイザーでのトークン数（特殊トークンを除く）。"""
    return len(_tokenizer()(text, add_special_tokens=False)["input_ids"])


def compose_prompt(
    instruction: str, condition: str, sg: SceneGraph, rng: np.random.Generator, other_instruction: str = ""
) -> str:
    """条件に応じた指示文を返す。条件 A は元の指示文の正規化のみ（モデルへの入力はこれまでと同一）。"""
    base = _normalize_question_text(instruction)
    if condition == "A":
        return base
    if condition == "L0":
        stripped, n = re.subn(settings.PROMPT_LOCATION_PATTERN, r"\1 \2", base)
        if n != 1:
            raise ValueError(f"条件 L0 に対応しない指示文: {base!r}")
        return stripped
    if condition == "L1":
        return _normalize_question_text(other_instruction)
    if condition == "B1":
        extra = textify.to_json(sg)
    elif condition == "B2":
        extra = textify.to_triples(sg)
    elif condition == "B3":
        extra = textify.to_natural(sg)
    elif condition == "C":
        # SG（JSON）とトークン数をそろえる
        extra = textify.filler(count_tokens(textify.to_json(sg)), count_tokens)
    elif condition == "D":
        extra = textify.to_json(textify.shuffled(sg, rng))
    else:
        raise ValueError(f"Unknown prompt condition {condition!r}. Expected one of {list(settings.PROMPT_CONDITIONS)}")
    return f"{base}. {settings.PROMPT_SG_LABEL}: {extra}"


def install(condition: str) -> None:
    """LiberoEnv を差し替える。環境を作る前に呼ぶこと。"""
    global _installed
    if condition not in settings.PROMPT_CONDITIONS:
        raise ValueError(f"Unknown prompt condition {condition!r}. Expected one of {list(settings.PROMPT_CONDITIONS)}")
    if _installed:
        return
    _installed = True
    orig_init, orig_reset, orig_step = LiberoEnv.__init__, LiberoEnv.reset, LiberoEnv.step

    def init(self: LiberoEnv, task_suite: Any, task_id: int, *args: Any, **kwargs: Any) -> None:
        orig_init(self, task_suite, task_id, *args, **kwargs)
        n_tasks = task_suite.get_num_tasks()
        self._other_task_description = task_suite.get_task((task_id + settings.PROMPT_OTHER_TASK_OFFSET) % n_tasks).language

    def reset(self: LiberoEnv, *args: Any, **kwargs: Any) -> Any:
        out = orig_reset(self, *args, **kwargs)
        if not hasattr(self, "_orig_task_description"):
            self._orig_task_description = self.task_description
            self._prompt_episode = 0
        sg = build_scene_graph(self._env.env)
        # 条件 D の入れ替えはタスクとエピソードごとに固定する
        seed = zlib.crc32(f"{self.task}:{self._prompt_episode}".encode())
        rng = np.random.default_rng(seed)
        prompt = compose_prompt(self._orig_task_description, condition, sg, rng, self._other_task_description)
        self.task_description = prompt
        self._prompt_step = 0
        self._prompt_record = {
                "task": self.task,
                "task_id": self.task_id,
                "episode": self._prompt_episode,
                "condition": condition,
                "prompt": prompt,
            "scene_graph": sg.to_dict(),
        }
        records.append(self._prompt_record)
        self._prompt_episode += 1
        return out

    def step(self: LiberoEnv, action: Any) -> Any:
        out = orig_step(self, action)
        self._prompt_step += 1
        # lerobot-eval は最大ステップ数で打ち切るとき環境に知らせないため、ステップ数で終了を判定する
        if out[2] or self._prompt_step == self._max_episode_steps:
            self._prompt_record["final_step"] = self._prompt_step
            self._prompt_record["final_scene_graph"] = build_scene_graph(self._env.env).to_dict()
        return out

    LiberoEnv.__init__ = init
    LiberoEnv.reset = reset
    LiberoEnv.step = step
