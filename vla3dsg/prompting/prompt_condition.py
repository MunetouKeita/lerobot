"""実験1 のプロンプト条件に従って、エピソードごとに指示文を差し替える。

LeRobot の LiberoEnv.reset を差し替え、reset 後（物体が落ち着いた後）のシミュレータの状態から SG を作り、
`task_description`（lerobot-eval がポリシーに渡す指示文）を書き換える。LeRobot 本体のファイルは変更しない。

MolmoAct2 の前処理の正規化は SG のテキスト（JSON の括弧など）を壊すため、評価では
`--policy.normalize_language=false` とし、元の指示文だけをここで同じ関数で正規化する。
"""

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


def compose_prompt(instruction: str, condition: str, sg: SceneGraph, rng: np.random.Generator) -> str:
    """条件に応じた指示文を返す。条件 A は元の指示文の正規化のみ（モデルへの入力はこれまでと同一）。"""
    base = _normalize_question_text(instruction)
    if condition == "A":
        return base
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
    orig_reset = LiberoEnv.reset

    def reset(self: LiberoEnv, *args: Any, **kwargs: Any) -> Any:
        out = orig_reset(self, *args, **kwargs)
        if not hasattr(self, "_orig_task_description"):
            self._orig_task_description = self.task_description
            self._prompt_episode = 0
        sg = build_scene_graph(self._env.env)
        # 条件 D の入れ替えはタスクとエピソードごとに固定する
        seed = zlib.crc32(f"{self.task}:{self._prompt_episode}".encode())
        prompt = compose_prompt(self._orig_task_description, condition, sg, np.random.default_rng(seed))
        self.task_description = prompt
        records.append(
            {
                "task": self.task,
                "task_id": self.task_id,
                "episode": self._prompt_episode,
                "condition": condition,
                "prompt": prompt,
                "scene_graph": sg.to_dict(),
            }
        )
        self._prompt_episode += 1
        return out

    LiberoEnv.reset = reset
