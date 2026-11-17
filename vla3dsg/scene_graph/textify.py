"""SG のテキスト化（三つ組の列）。"""

from vla3dsg.scene_graph.builder import SceneGraph


def to_triples(sg: SceneGraph) -> str:
    return "; ".join("(" + ", ".join(r) + ")" for r in sg.relations)
