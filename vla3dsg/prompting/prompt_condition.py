"""プロンプト条件に従って、エピソードごとに指示文を差し替える。

LeRobot の LiberoEnv.reset を差し替え、reset 後（物体が落ち着いた後）のシミュレータの状態から SG を作り、
`task_description`（lerobot-eval がポリシーに渡す指示文）を書き換える。LeRobot 本体のファイルは変更しない。
エピソードの終了時（成功または最大ステップ数）の SG も記録し、どの物体をどこに置いたかを後から分類できるようにする。

MolmoAct2 の前処理の正規化は SG のテキスト（三つ組の括弧など）を壊すため、評価では
`--policy.normalize_language=false` とし、元の指示文だけをここで同じ関数で正規化する。
"""

from functools import cache
from typing import Any

from transformers import AutoTokenizer

from lerobot.envs.libero import LiberoEnv
from lerobot.policies.molmoact2.processor_molmoact2 import _normalize_question_text

from vla3dsg.config import settings
from vla3dsg.scene_graph import textify
from vla3dsg.scene_graph.builder import SceneGraph, build_scene_graph
from vla3dsg.scene_graph.relevant import build_relevant_scene_graph, build_wrong_scene_graph

_installed = False
# 実際に使ったプロンプトの記録（run_eval.py が prompts.jsonl に保存する）
records: list[dict[str, Any]] = []


@cache
def _tokenizer() -> Any:
    return AutoTokenizer.from_pretrained(settings.MOLMOACT2_CHECKPOINT)


def count_tokens(text: str) -> int:
    """MolmoAct2 のトークナイザーでのトークン数（特殊トークンを除く）。"""
    return len(_tokenizer()(text, add_special_tokens=False)["input_ids"])


def compose_prompt(instruction: str, condition: str, sg: SceneGraph, env: Any) -> str:
    """条件に応じた指示文を返す。base は元の指示文の正規化のみ（モデルへの入力は公式の評価と同一）。

    SG を加える条件では、小さな SG を作るために env（LIBERO の BDDL 環境）を使う。隠れていることは伝えない。
    """
    if condition not in settings.PROMPT_CONDITIONS:
        raise ValueError(f"Unknown prompt condition {condition!r}. Expected one of {list(settings.PROMPT_CONDITIONS)}")
    base = _normalize_question_text(instruction)
    if condition == "base":
        return base
    if condition == "target":
        return f"put the {sg.target} on the plate"
    if condition == "sg_command":
        return textify.to_instruction(build_relevant_scene_graph(env))
    given = {"base_short": build_relevant_scene_graph, "base_full": lambda _: sg, "base_wrong": build_wrong_scene_graph}[condition](env)
    return f"{base}. {settings.PROMPT_SG_LABEL}: {textify.to_triples(given)}"


def install(condition: str) -> None:
    """LiberoEnv を差し替える。環境を作る前に呼ぶこと。"""
    global _installed
    if condition not in settings.PROMPT_CONDITIONS:
        raise ValueError(f"Unknown prompt condition {condition!r}. Expected one of {list(settings.PROMPT_CONDITIONS)}")
    if _installed:
        return
    _installed = True
    orig_reset, orig_step = LiberoEnv.reset, LiberoEnv.step

    def reset(self: LiberoEnv, *args: Any, **kwargs: Any) -> Any:
        out = orig_reset(self, *args, **kwargs)
        if not hasattr(self, "_orig_task_description"):
            self._orig_task_description = self.task_description
            self._prompt_episode = 0
        sg = build_scene_graph(self._env.env)
        prompt = compose_prompt(self._orig_task_description, condition, sg, self._env.env)
        self.task_description = prompt
        self._prompt_step = 0
        self._prompt_record = {
            "task": self.task,
            "task_id": self.task_id,
            "episode": self._prompt_episode,
            "condition": condition,
            "prompt": prompt,
            "scene_graph": sg.to_dict(),
            "target": sg.target,
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

    LiberoEnv.reset = reset
    LiberoEnv.step = step
