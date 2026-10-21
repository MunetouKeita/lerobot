"""掴む対象についての関係だけを残した、小さな SG（タスクに関係する部分）。

全物体どうしの関係（builder.build_scene_graph）は 10 本前後あり、タスクに関係ないものが大半になる。ここでは、
掴む対象を、同じ種類の別の物体（例: おとりのボウル）と見分けられる最小の関係だけを選ぶ（最大 SG_RELEVANT_MAX 本）。

候補の関係（優先順）:
  1. 支え・中身（on / in）
  2. 隠れ: agentview から見えていない（見える点の割合が SG_HIDDEN_MAX_VISIBLE 未満）とき、遮っている物体の "behind"
  3. 大きくて動かない物体（固定物と、置き場所になる物体 SG_LANDMARK_OBJECTS）との前後左右（近い順）
  4. ほかの物体との前後左右（近い順）
同じ種類の別の物体（例: "black bowl 2"）は見分けたい相手そのもの、置き場所（obj_of_interest の 2 つ目以降。例: plate）は
指示文の中で行き先として出てくるため、手がかりにしない。
1 本目は候補の先頭とし、同じ種類の別の物体にも当てはまる限り、それを最も多く除ける候補を足す。
"""

from collections import Counter
from typing import Any

import numpy as np

from vla3dsg.config import settings
from vla3dsg.envs.custom_task_builder import ray_hits
from vla3dsg.scene_graph.builder import SceneGraph, _direction, _display_names, _position, _support_relations

Relation = tuple[str, ...]


def _category(env: Any, obj_id: str) -> str:
    return next(c for c, ids in env.parsed_problem["objects"].items() if obj_id in ids)


def _occlusion(env: Any, obj_id: str, ids: list[str]) -> tuple[float, str | None]:
    """(agentview から見える点の割合, 遮っている物体の ID)。ロボットに遮られた点は数えない。"""
    hits = ray_hits(env.sim.model._model, env.sim.data._data, obj_id, "agentview")
    hits = [h for h in hits if h is None or not h.startswith(("robot0", "gripper0", "mount0"))]
    if not hits:
        return 1.0, None
    own = [h for h in hits if h is not None and h.startswith(f"{obj_id}_")]
    blockers = Counter(next((i for i in sorted(ids, key=len, reverse=True) if h.startswith(f"{i}_")), None) for h in hits if h not in own)
    blockers.pop(None, None)
    return len(own) / len(hits), (blockers.most_common(1)[0][0] if blockers else None)


def _candidates(env: Any, obj_id: str, names: dict[str, str], support: dict, positions: dict) -> list[tuple[str, str]]:
    """obj_id の候補の関係 (関係, 相手の名前) を優先順に。"""
    out: list[tuple[str, str]] = []
    if obj_id in support:
        out.append(support[obj_id])
    ratio, occluder = _occlusion(env, obj_id, list(names))
    if ratio < settings.SG_HIDDEN_MAX_VISIBLE and occluder is not None:
        out.append(("behind", names[occluder]))
    same = {i for i in env.objects_dict if i in names and _category(env, i) == _category(env, obj_id)}
    same |= {i for i in env.obj_of_interest[1:] if i != obj_id}
    landmarks = [i for i in names if i not in same and (i in env.fixtures_dict or (i in env.objects_dict and _category(env, i) in settings.SG_LANDMARK_OBJECTS))]
    others = [i for i in names if i not in same and i not in landmarks]
    for group in (landmarks, others):
        for i in sorted(group, key=lambda i: np.linalg.norm(positions[obj_id][:2] - positions[i][:2]))[: settings.SG_NEAREST_K]:
            rel = (_direction(positions[obj_id], positions[i]), names[i])
            if rel not in out and names[i] != (support.get(obj_id) or ("", ""))[1]:
                out.append(rel)
    return out


def _holds(env: Any, obj_id: str, rel: tuple[str, str], names: dict[str, str], support: dict, positions: dict) -> bool:
    """obj_id について関係 rel が成り立つか（同じ種類の別の物体と見分けられるかの判定に使う）。"""
    anchor = next((i for i, n in names.items() if n == rel[1] or rel[1].endswith(f" {n}")), None)
    if anchor == obj_id:
        return False
    if support.get(obj_id) == rel:
        return True
    if rel[0] == "behind":
        ratio, occluder = _occlusion(env, obj_id, list(names))
        if ratio < settings.SG_HIDDEN_MAX_VISIBLE and occluder == anchor:
            return True
    return anchor is not None and anchor in positions and _direction(positions[obj_id], positions[anchor]) == rel[0]


def build_relevant_scene_graph(env: Any, subject: str | None = None) -> SceneGraph:
    """掴む対象（subject を省略すると BDDL の obj_of_interest の先頭の物体）についての小さな SG。

    subject に別の物体の ID を渡すと、その物体の関係を作る（誤った SG の対照に使う）。名前は SG のノード名。
    """
    names = _display_names(env)
    support = _support_relations(env, names)
    positions = {i: _position(env, i) for i in names}
    target_id = next(i for i in env.obj_of_interest if i in env.objects_dict)
    subject = subject or target_id
    distractors = [i for i in env.objects_dict if i != subject and i in names and _category(env, i) == _category(env, subject)]

    candidates = _candidates(env, subject, names, support, positions)
    chosen = candidates[:1]
    remaining = [d for d in distractors if all(_holds(env, d, r, names, support, positions) for r in chosen)]
    while remaining and len(chosen) < settings.SG_RELEVANT_MAX:
        rest = [c for c in candidates if c not in chosen]
        if not rest:
            break
        best = max(rest, key=lambda c: sum(not _holds(env, d, c, names, support, positions) for d in remaining))
        chosen.append(best)
        remaining = [d for d in remaining if _holds(env, d, best, names, support, positions)]

    relations: list[Relation] = [(names[subject], rel, other) for rel, other in chosen]
    nodes = [names[subject]] + [o for _, o in chosen]
    return SceneGraph(nodes=nodes, relations=relations, target=names[target_id])


_OPPOSITE = {"behind": "in front of", "in front of": "behind", "left of": "right of", "right of": "left of"}


def build_wrong_scene_graph(env: Any) -> SceneGraph:
    """掴む対象について成り立たない関係だけの小さな SG（誤った SG の条件）。

    同じ種類の別の物体（おとり）があれば、おとりの小さな SG を対象の名前で書き、対象にも当てはまる関係は除く
    （おとりへ誘導する誤り）。おとりがない、または残らなければ、対象の小さな SG の前後左右を逆にする。
    """
    names = _display_names(env)
    support = _support_relations(env, names)
    positions = {i: _position(env, i) for i in names}
    target_id = next(i for i in env.obj_of_interest if i in env.objects_dict)
    target = names[target_id]
    decoys = sorted(i for i in env.objects_dict if i != target_id and i in names and _category(env, i) == _category(env, target_id))
    relations: list[Relation] = []
    if decoys:
        decoy = build_relevant_scene_graph(env, subject=decoys[0])
        relations = [
            (target, *r[1:]) for r in decoy.relations if not _holds(env, target_id, (r[1], r[2]), names, support, positions)
        ]
    if not relations:
        candidates = _candidates(env, target_id, names, support, positions)
        relations = [(target, _OPPOSITE[r], o) for r, o in candidates if r in _OPPOSITE][:1]
    return SceneGraph(nodes=[target] + [r[2] for r in relations], relations=relations, target=target)
