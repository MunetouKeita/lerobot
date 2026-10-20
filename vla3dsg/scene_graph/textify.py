"""SG のテキスト化と、対照条件（無関係な文・関係を入れ替えた SG）の生成。"""

import json
from collections.abc import Callable

import numpy as np

from vla3dsg.config import settings
from vla3dsg.scene_graph.builder import SceneGraph


def to_json(sg: SceneGraph) -> str:
    return json.dumps(sg.to_dict(), ensure_ascii=False)


def to_triples(sg: SceneGraph) -> str:
    return "; ".join("(" + ", ".join(r) + ")" for r in sg.relations)


# 関係を、指示文の中の場所の言い方にする（"the black bowl behind the wooden cabinet" の "behind the wooden cabinet"）
_PLACE_PHRASES = {
    "on": "on the {o}",
    "in": "in the {o}",
    "behind": "behind the {o}",
    "in front of": "in front of the {o}",
    "left of": "to the left of the {o}",
    "right of": "to the right of the {o}",
    "next to": "next to the {o}",
}


def to_instruction(sg: SceneGraph, hidden: bool = False) -> str:
    """掴む対象の小さな SG（relevant.build_relevant_scene_graph）から、場所を書いた指示文を作る。

    例: (black bowl 1, behind, wooden cabinet) → "pick up the black bowl behind the wooden cabinet and place it on the plate"。
    場所で対象を特定するため、名前の番号（"black bowl 1" の 1）は付けない。hidden=True で関係に hidden が付いていれば、
    "the black bowl that is hidden behind the wooden cabinet" のように、見えないことも書く。
    """
    name = " ".join(w for w in sg.target.split() if not w.isdigit())
    # 領域の名前（例: "top drawer of wooden cabinet"）は、指示文では "of the" にする
    places = [_PLACE_PHRASES[r[1]].format(o=r[2].replace(" of ", " of the ")) for r in sg.relations]
    is_hidden = hidden and any(r[3:] == ("hidden",) for r in sg.relations)
    where = " and ".join(places)
    target = f"the {name} that is hidden {where}" if is_hidden else f"the {name} {where}"
    return f"pick up {target} and place it on the plate"


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
    return SceneGraph(nodes=[mapping[n] for n in nodes], relations=relations, target=sg.target)


def filler(n_tokens: int, count_tokens: Callable[[str], int]) -> str:
    """指定したトークン数（以上で最小）の、タスクと無関係な文。単語の途中では切らない。"""
    words = settings.FILLER_TEXT.split()
    out: list[str] = []
    i = 0
    while count_tokens(" ".join(out)) < n_tokens:
        out.append(words[i % len(words)])
        i += 1
    return " ".join(out)
