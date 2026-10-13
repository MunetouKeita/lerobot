"""SG のテキスト化と、対照条件（無関係な文・関係を入れ替えた SG）の生成。"""

import json
from collections.abc import Callable

import numpy as np

from vla3dsg.config import settings
from vla3dsg.scene_graph.builder import SceneGraph


def to_json(sg: SceneGraph) -> str:
    return json.dumps(sg.to_dict(), ensure_ascii=False)


def to_triples(sg: SceneGraph) -> str:
    return "; ".join(f"({s}, {r}, {o})" for s, r, o in sg.relations)


def to_natural(sg: SceneGraph) -> str:
    return " ".join(f"the {s} is {r} the {o}." for s, r, o in sg.relations)


def shuffled(sg: SceneGraph, rng: np.random.Generator) -> SceneGraph:
    """関係の構造はそのままに、物体名を入れ替える（どの物体も元の名前にならないようにする）。"""
    nodes = list(sg.nodes)
    if len(nodes) < 2:
        return sg
    while True:
        perm = list(rng.permutation(len(nodes)))
        if all(perm[i] != i for i in range(len(nodes))):
            break
    mapping = {nodes[i]: nodes[perm[i]] for i in range(len(nodes))}

    def rename(text: str) -> str:
        # 領域の名前（例: "top drawer of wooden cabinet"）に含まれる物体名も置き換える
        for name in sorted(mapping, key=len, reverse=True):
            if text == name or text.endswith(f" {name}"):
                return text[: len(text) - len(name)] + mapping[name]
        return text

    relations = [(rename(s), r, rename(o)) for s, r, o in sg.relations]
    return SceneGraph(nodes=[mapping[n] for n in nodes], relations=relations)


def filler(n_tokens: int, count_tokens: Callable[[str], int]) -> str:
    """指定したトークン数（以上で最小）の、タスクと無関係な文。単語の途中では切らない。"""
    words = settings.FILLER_TEXT.split()
    out: list[str] = []
    i = 0
    while count_tokens(" ".join(out)) < n_tokens:
        out.append(words[i % len(words)])
        i += 1
    return " ".join(out)
