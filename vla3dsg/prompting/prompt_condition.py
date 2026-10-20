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
from vla3dsg.scene_graph.relevant import build_relevant_scene_graph, mark_hidden, target_is_hidden

_installed = False
# 実際に使ったプロンプトの記録（run_eval.py が prompts.jsonl に保存する）
records: list[dict[str, Any]] = []


@cache
def _tokenizer() -> Any:
    return AutoTokenizer.from_pretrained(settings.MOLMOACT2_CHECKPOINT)


def count_tokens(text: str) -> int:
    """MolmoAct2 のトークナイザーでのトークン数（特殊トークンを除く）。"""
    return len(_tokenizer()(text, add_special_tokens=False)["input_ids"])


def _wrong_relevant(env: Any, sg: SceneGraph) -> SceneGraph:
    """同じ種類の別の物体（おとり）の小さな SG を、掴む対象の名前で書いたもの（条件 P5）。"""
    target_id = next(i for i in env.obj_of_interest if i in env.objects_dict)
    category = next(c for c, ids in env.parsed_problem["objects"].items() if target_id in ids)
    others = [i for i in env.parsed_problem["objects"][category] if i != target_id]
    if not others:
        raise ValueError("条件 P5 には、掴む対象と同じ種類の別の物体が必要")
    wrong = build_relevant_scene_graph(env, subject=sorted(others)[0])
    rename = {wrong.relations[0][0]: sg.target, sg.target: wrong.relations[0][0]}
    relations = [tuple(rename.get(x, x) for x in r) for r in wrong.relations]
    return SceneGraph(nodes=[rename.get(n, n) for n in wrong.nodes], relations=relations, target=sg.target)


def compose_prompt(instruction: str, condition: str, sg: SceneGraph, env: Any) -> str:
    """条件に応じた指示文を返す。条件 A は元の指示文の正規化のみ（モデルへの入力はこれまでと同一）。

    P1〜P5 では、小さな SG を作るために env（LIBERO の BDDL 環境）を使う。末尾の h（P1h〜P5h）は、対象が隠れていれば
    その事実を加える（場所の情報とは独立。P5h は「場所は誤り、隠れていることは正しい」）。
    """
    if condition == "A":
        return _normalize_question_text(instruction)
    if condition not in settings.PROMPT_CONDITIONS:
        raise ValueError(f"Unknown prompt condition {condition!r}. Expected one of {list(settings.PROMPT_CONDITIONS)}")
    kind, hidden = condition[:2], condition.endswith("h") and target_is_hidden(env)
    if kind == "P1":
        # SG の小さな関係から、場所を書いた指示文（LIBERO の指示文と同じ形）を作る
        return textify.to_instruction(build_relevant_scene_graph(env, hidden=hidden), hidden=hidden)
    if kind == "P2":
        # 場所を書かず、対象を SG のノード名で指す
        return f"pick up the {sg.target}{' that is hidden' if hidden else ''} and place it on the plate"
    if kind == "P3":
        given = build_relevant_scene_graph(env)
    elif kind == "P4":
        given = sg
    else:
        given = _wrong_relevant(env, sg)
    extra = textify.to_triples(mark_hidden(given) if hidden else given)
    return f"pick up the {sg.target} and place it on the plate. {settings.PROMPT_SG_LABEL}: {extra}"


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
