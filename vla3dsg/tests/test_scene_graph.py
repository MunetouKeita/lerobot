"""SG の生成（scene_graph/）とプロンプト条件（prompting/prompt_condition.py）を確認する。

libero_spatial の各タスクで reset 後の SG を作り、agentview 画像と各条件のプロンプトを tmp/ に保存する。

    uv run python vla3dsg/tests/test_scene_graph.py [--suite libero_spatial] [--task-ids 0 1 ...]
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

settings.apply_runtime_env()

import draccus  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from lerobot.configs.parser import load_plugin  # noqa: E402
from lerobot.envs.configs import EnvConfig  # noqa: E402

from vla3dsg.prompting import prompt_condition  # noqa: E402
from vla3dsg.scene_graph import textify  # noqa: E402
from vla3dsg.scene_graph.builder import build_scene_graph  # noqa: E402


@dataclass
class _Wrapper:
    env: EnvConfig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_spatial")
    parser.add_argument("--task-ids", type=int, nargs="*", default=list(range(10)))
    args = parser.parse_args()

    load_plugin("vla3dsg.envs")
    prompt_condition.install("B1")
    out_dir = settings.TMP_DIR / "test_scene_graph"
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    for task_id in args.task_ids:
        argv = ["--env.type=libero_vla3dsg", f"--env.task={args.suite}", f"--env.task_ids=[{task_id}]"]
        cfg = draccus.parse(_Wrapper, args=argv).env
        vec_env = cfg.create_envs(n_envs=1, use_async_envs=False)[args.suite][task_id]
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
        c = prompt_condition.compose_prompt(instruction, "C", sg, rng)
        d = prompt_condition.compose_prompt(instruction, "D", sg, rng)
        n_b1, n_c = prompt_condition.count_tokens(inner.task_description), prompt_condition.count_tokens(c)
        assert 0 <= n_c - n_b1 <= 3, (n_b1, n_c)
        assert d != inner.task_description
        assert prompt_condition.compose_prompt(instruction, "A", sg, rng) == instruction  # LIBERO の指示文は正規化しても同じ
        assert prompt_condition.compose_prompt(instruction, "L0", sg, rng) == "pick up the black bowl and place it on the plate"
        assert prompt_condition.compose_prompt(instruction, "L1", sg, rng, inner._other_task_description) != instruction

        prompts = {
            k: prompt_condition.compose_prompt(instruction, k, sg, np.random.default_rng(1), inner._other_task_description)
            for k in settings.PROMPT_CONDITIONS
        }
        (out_dir / f"{args.suite}_{task_id}.json").write_text(
            json.dumps({"instruction": instruction, "scene_graph": sg.to_dict(), "prompts": prompts}, indent=2, ensure_ascii=False)
        )
        Image.fromarray(np.ascontiguousarray(obs["pixels"]["image"][0][::-1, ::-1])).save(out_dir / f"{args.suite}_{task_id}.png")
        print(f"task {task_id}: {instruction}")
        print(f"  {textify.to_triples(sg)}")
        vec_env.close()

    print(f"saved: {out_dir}")
    print("OK")


if __name__ == "__main__":
    main()
