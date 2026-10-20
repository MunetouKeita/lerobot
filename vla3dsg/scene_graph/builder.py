"""シミュレータの内部状態（物体の位置・接触）から、正解の Scene Graph を作る。

ノード: テーブル上の物体と固定物（テーブル自体は除く）。同じ種類は番号を付ける（例: "black bowl 1"）
エッジ:
  - on / in: 物体の領域（引き出し・棚の上面・コンロ）に入っているか、他の物体に接触して上に載っているか
  - 前後左右: agentview カメラから見た向き。各物体について近い順に SG_NEAREST_K 個の物体との関係
    （テーブル座標で x が大きいほど手前、y が小さいほど右）
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from vla3dsg.config import settings
from vla3dsg.config.object_names import OBJECT_NAMES, REGION_RELATIONS

TABLE_PREFIXES = ("main_table", "kitchen_table", "living_room_table", "study_table", "coffee_table", "floor")


@dataclass
class SceneGraph:
    nodes: list[str]
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    target: str | None = None  # 掴む対象のノード名（BDDL の obj_of_interest の先頭の物体）。to_dict には含めない

    def to_dict(self) -> dict[str, Any]:
        return {"objects": self.nodes, "relations": [list(r) for r in self.relations]}


def _display_names(env: Any) -> dict[str, str]:
    """物体 ID（例: akita_black_bowl_1）→ 読みやすい名前。"""
    names: dict[str, str] = {}
    groups = {**env.parsed_problem["fixtures"], **env.parsed_problem["objects"]}
    for category, ids in groups.items():
        ids = [i for i in ids if not i.startswith(TABLE_PREFIXES)]
        base = OBJECT_NAMES.get(category, category.replace("_", " "))
        for k, obj_id in enumerate(sorted(ids)):
            names[obj_id] = f"{base} {k + 1}" if len(ids) > 1 else base
    return names


def _position(env: Any, obj_id: str) -> np.ndarray:
    return np.asarray(env.sim.data.body_xpos[env.obj_body_id[obj_id]], dtype=float)


def _support_relations(env: Any, names: dict[str, str]) -> dict[str, tuple[str, str]]:
    """動かせる物体ごとの (関係, 相手の名前)。

    LIBERO の述語（成功判定に使われるもの）に合わせる:
      - 固定物・物体の領域（引き出し・棚の上面・コンロ）: In = 接触 かつ 領域内、On = 領域の上 かつ 親に接触
      - 動かせる物体どうし: LIBERO の On（相手の原点以上の高さ・接触・中心のずれ 3 cm 未満）、または
        相手より SG_ON_MIN_DZ 以上高く接触している（ずれて載っている場合も拾うため）
    """
    states = env.object_states_dict
    support: dict[str, tuple[str, str]] = {}
    for obj_id in [i for i in env.objects_dict if i in names]:
        obj_state = states[obj_id]
        for region_id, region_state in states.items():
            parent = getattr(region_state, "parent_name", None)
            if parent is None or parent not in names:
                continue
            suffix = region_id[len(parent) + 1 :]
            if suffix not in REGION_RELATIONS:
                continue
            rel, template = REGION_RELATIONS[suffix]
            if rel == "in":
                hit = region_state.check_contact(obj_state) and region_state.check_contain(obj_state)
            else:
                hit = region_state.check_ontop(obj_state)
            if hit:
                support[obj_id] = (rel, template.format(parent=names[parent]))
                break
        if obj_id in support:
            continue
        pos = _position(env, obj_id)
        for other_id in env.objects_dict:
            if other_id == obj_id or other_id not in names:
                continue
            libero_on = states[other_id].check_ontop(obj_state)
            if libero_on or (
                pos[2] > _position(env, other_id)[2] + settings.SG_ON_MIN_DZ
                and env.check_contact(env.get_object(obj_id), env.get_object(other_id))
            ):
                support[obj_id] = ("on", names[other_id])
                break
    return support


def _direction(a: np.ndarray, b: np.ndarray) -> str:
    """a から見た b ではなく、「a は b の〇〇」の〇〇を返す（agentview 基準）。"""
    dx, dy = a[0] - b[0], a[1] - b[1]
    if max(abs(dx), abs(dy)) < settings.SG_NEXT_TO_MAX_DIST:
        return "next to"
    if abs(dy) >= abs(dx):
        return "left of" if dy > 0 else "right of"
    return "in front of" if dx > 0 else "behind"


def build_scene_graph(env: Any) -> SceneGraph:
    """LIBERO の BDDL 環境（OffScreenRenderEnv の .env）から SG を作る。"""
    names = _display_names(env)
    ids = list(names)
    target_id = next((i for i in env.obj_of_interest if i in env.objects_dict), None)
    sg = SceneGraph(nodes=[names[i] for i in ids], target=names.get(target_id))
    support = _support_relations(env, names)
    for obj_id, (rel, target) in support.items():
        sg.relations.append((names[obj_id], rel, target))

    positions = {i: _position(env, i) for i in ids}
    for obj_id in [i for i in ids if i in env.objects_dict]:
        if support.get(obj_id, ("", ""))[0] == "in":
            continue  # 引き出しの中などは前後左右を付けない
        others = sorted(
            (i for i in ids if i != obj_id),
            key=lambda i: np.linalg.norm(positions[obj_id][:2] - positions[i][:2]),
        )
        for other_id in others[: settings.SG_NEAREST_K]:
            target = support.get(obj_id, ("", ""))[1]
            if target == names[other_id] or target.endswith(f" {names[other_id]}"):
                continue  # 載っている・入っている相手との前後左右は付けない
            rel = _direction(positions[obj_id], positions[other_id])
            sg.relations.append((names[obj_id], rel, names[other_id]))
    return sg
