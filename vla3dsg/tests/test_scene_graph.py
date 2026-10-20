"""SG の生成（scene_graph/）とプロンプト条件（prompting/prompt_condition.py）を確認する。

スイート（既定は libero_spatial）の各タスクで reset 後の SG を作り、agentview 画像と各条件のプロンプトを tmp/ に保存する。
最小の実験の条件（P1〜P5）の指示文と、掴む対象についての小さな SG（scene_graph/relevant.py）も確かめる。

    uv run python vla3dsg/tests/test_scene_graph.py [--suite libero_spatial|vla3dsg_occluded] [--task-ids 0 1 ...]
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
from vla3dsg.scene_graph.relevant import build_relevant_scene_graph, target_is_hidden  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_spatial")
    parser.add_argument("--task-ids", type=int, nargs="*", help="省略するとスイートの全タスク")
    args = parser.parse_args()

    load_plugin("vla3dsg.envs")
    prompt_condition.install("B1")
    out_dir = settings.TMP_DIR / "test_scene_graph"
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    task_ids = args.task_ids if args.task_ids else list(range(benchmark.get_benchmark_dict()[args.suite]().n_tasks))
    for task_id in task_ids:
        vec_env = make_env(args.suite, task_id)
        obs, _ = vec_env.reset(seed=settings.SEED)
        inner = vec_env.envs[0]
        sg = build_scene_graph(inner._env.env)

        assert len(sg.nodes) == len(set(sg.nodes)), f"ノード名が重複している: {sg.nodes}"
        assert sg.relations, "関係が 1 つもない"
        assert all(s in sg.nodes for s, _, _ in sg.relations), "関係の主語がノードにない"
        # 条件 B1 の指示文が書き換わり、記録されていること
        assert inner.task_description.endswith(textify.to_json(sg)), inner.task_description
        assert prompt_condition.records[-1]["task_id"] == task_id
        # 対照条件
        instruction = inner._orig_task_description
        env = inner._env.env
        c = prompt_condition.compose_prompt(instruction, "C", sg, rng)
        d = prompt_condition.compose_prompt(instruction, "D", sg, rng)
        n_b1, n_c = prompt_condition.count_tokens(inner.task_description), prompt_condition.count_tokens(c)
        assert 0 <= n_c - n_b1 <= 3, (n_b1, n_c)
        assert d != inner.task_description
        if args.suite.startswith("libero_"):
            assert prompt_condition.compose_prompt(instruction, "A", sg, rng) == instruction  # LIBERO の指示文は正規化しても同じ
            assert prompt_condition.compose_prompt(instruction, "L0", sg, rng) == "pick up the black bowl and place it on the plate"
            assert prompt_condition.compose_prompt(instruction, "L1", sg, rng, inner._other_task_description) != instruction

        # 最小の実験の条件（P1〜P5）
        def compose(k: str) -> str:
            return prompt_condition.compose_prompt(
                instruction, k, sg, np.random.default_rng(1), inner._other_task_description, env
            )

        assert compose("P1") == textify.to_instruction(build_relevant_scene_graph(env))
        assert compose("P2") == f"pick up the {sg.target} and place it on the plate"
        relevant = build_relevant_scene_graph(env)
        assert 1 <= len(relevant.relations) <= settings.SG_RELEVANT_MAX and all(r[0] == sg.target for r in relevant.relations)
        assert ("hidden" in compose("P3h")) == ("hidden" in textify.to_triples(build_relevant_scene_graph(env, hidden=True)))
        assert compose("P1").startswith("pick up the black bowl ") and compose("P1").endswith(" and place it on the plate")
        # h の条件は、対象が隠れているときだけ文が変わる
        for k in ("P1", "P2", "P3", "P4"):
            assert ("hidden" in compose(f"{k}h")) == target_is_hidden(env), (k, compose(f"{k}h"))
            if not target_is_hidden(env):
                assert compose(f"{k}h") == compose(k)
        n_bowls = sum(1 for n in sg.nodes if n.startswith("black bowl"))
        if n_bowls > 1:
            assert compose("P5") != compose("P3")
        prompts = {}
        for k in settings.PROMPT_CONDITIONS:
            try:
                prompts[k] = compose(k)
            except ValueError as e:  # このタスクでは作れない条件（例: おとりのないシーンの P5、自作タスクの L0）
                prompts[k] = f"（なし: {e}）"
        (out_dir / f"{args.suite}_{task_id}.json").write_text(
            json.dumps({"instruction": instruction, "scene_graph": sg.to_dict(), "prompts": prompts}, indent=2, ensure_ascii=False)
        )
        Image.fromarray(np.ascontiguousarray(obs["pixels"]["image"][0][::-1, ::-1])).save(out_dir / f"{args.suite}_{task_id}.png")
        print(f"task {task_id}: {instruction}")
        for k in ("P1", "P1h", "P2", "P2h", "P3", "P3h", "P4h", "P5", "P5h"):
            print(f"  {k}: {prompts[k]}")
        print(f"  P4 の関係の数: {len(sg.relations)}")
        vec_env.close()

    print(f"saved: {out_dir}")
    print("OK")


if __name__ == "__main__":
    main()
