"""SG のテキスト化（三つ組の列と、場所を書いた指示文）。"""

from vla3dsg.scene_graph.builder import SceneGraph


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





