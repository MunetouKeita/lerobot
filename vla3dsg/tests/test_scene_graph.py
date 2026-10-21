"""SG の生成（scene_graph/）とプロンプト条件（prompting/prompt_condition.py）を確認する。

スイート（既定は vla3dsg_goal）の各タスクで reset 後の SG を作り、agentview 画像と各条件のプロンプトを tmp/ に保存する。
掴む対象についての小さな SG（scene_graph/relevant.py）と、誤った SG・各条件の指示文も確かめる。

    uv run python vla3dsg/tests/test_scene_graph.py [--suite vla3dsg_goal|libero_spatial] [--task-ids 0 1 ...]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

from libero.libero import benchmark  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.configs.parser import load_plugin  # noqa: E402

from vla3dsg.envs.libero_vla3dsg import make_env  # noqa: E402
from vla3dsg.prompting import prompt_condition  # noqa: E402
from vla3dsg.scene_graph import textify  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402
from vla3dsg.scene_graph.relevant import build_relevant_scene_graph, build_wrong_scene_graph  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="vla3dsg_goal")
    parser.add_argument("--task-ids", type=int, nargs="*", help="省略するとスイートの全タスク")
    args = parser.parse_args()

    load_plugin("vla3dsg.envs")
    prompt_condition.install("base_short")
    out_dir = settings.TMP_DIR / "test_scene_graph"
    out_dir.mkdir(parents=True, exist_ok=True)

    task_ids = args.task_ids if args.task_ids else list(range(benchmark.get_benchmark_dict()[args.suite]().n_tasks))
    for task_id in task_ids:
        vec_env = make_env(args.suite, task_id)
        obs, _ = vec_env.reset(seed=settings.SEED)
        inner = vec_env.envs[0]
        env = inner._env.env
        sg = build_scene_graph(env)
        relevant = build_relevant_scene_graph(env)

        assert len(sg.nodes) == len(set(sg.nodes)), f"ノード名が重複している: {sg.nodes}"
        assert sg.relations, "関係が 1 つもない"
        assert all(r[0] in sg.nodes for r in sg.relations), "関係の主語がノードにない"
        assert 1 <= len(relevant.relations) <= settings.SG_RELEVANT_MAX and all(r[0] == sg.target for r in relevant.relations)
        # 条件 base_short の指示文が書き換わり、記録されていること
        assert inner.task_description.endswith(textify.to_triples(relevant)), inner.task_description
        assert prompt_condition.records[-1]["task_id"] == task_id

        instruction = inner._orig_task_description
        prompts = {k: prompt_condition.compose_prompt(instruction, k, sg, env) for k in settings.PROMPT_CONDITIONS}
        assert prompts["base"] == instruction.lower()  # LIBERO の指示文は正規化（小文字化など）以外そのまま
        assert prompts["sg_command"] == textify.to_instruction(relevant)
        assert prompts["sg_command"].startswith("put the ") and prompts["sg_command"].endswith(" on the plate")
        # 手がかりに同じ種類の物体と行き先を使わない
        same = [n for n in sg.nodes if n.split()[:2] == sg.target.split()[:2]]
        assert all(r[2] not in same and r[2] != "plate" for r in relevant.relations), relevant.relations
        # 誤った SG は、正しい小さな SG と重ならない
        wrong = build_wrong_scene_graph(env)
        assert wrong.relations and not set(wrong.relations) & set(relevant.relations), (wrong.relations, relevant.relations)
        (out_dir / f"{args.suite}_{task_id}.json").write_text(
            json.dumps({"instruction": instruction, "scene_graph": sg.to_dict(), "prompts": prompts}, indent=2, ensure_ascii=False)
        )
        Image.fromarray(np.ascontiguousarray(obs["pixels"]["image"][0][::-1, ::-1])).save(out_dir / f"{args.suite}_{task_id}.png")
        print(f"task {task_id}: {instruction}")
        for k in ("base_short", "base_wrong", "sg_command"):
            print(f"  {k}: {prompts[k]}")
        print(f"  base_full の関係の数: {len(sg.relations)}")
        vec_env.close()

    print(f"saved: {out_dir}")
    print("OK")


if __name__ == "__main__":
    main()
