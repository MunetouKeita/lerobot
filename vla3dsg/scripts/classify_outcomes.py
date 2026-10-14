"""評価結果（run_eval.py の results/<name>/prompts.jsonl）から、各エピソードで何をどこに置いたかを集計する。

エピソードの開始時と終了時の SG を比べ、終了時に新しくできた on / in の関係（例: "black bowl 2 on plate"）を
エピソードの結果とする。何も新しくできていなければ「変化なし」。

    uv run python vla3dsg/scripts/classify_outcomes.py --root phase4/language/hidden_cabinet_n20 --names A L1

結果は <root>/outcomes.md に保存する。終了時の SG がない結果（2026-10-13 の実験2 以前）は集計できない。
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402

SUPPORT_RELATIONS = ("on", "in")


def placements(sg: dict) -> set[str]:
    return {f"{s} {r} {o}" for s, r, o in sg["relations"] if r in SUPPORT_RELATIONS}


def outcome(record: dict) -> str:
    if "final_scene_graph" not in record:
        raise ValueError(f"終了時の SG がない: {record['task']} episode {record['episode']}")
    new = sorted(placements(record["final_scene_graph"]) - placements(record["scene_graph"]))
    return ", ".join(new) if new else "変化なし"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="results/ 以下の親ディレクトリ")
    parser.add_argument("--names", nargs="+", required=True)
    args = parser.parse_args()

    root = settings.RESULTS_DIR / args.root
    lines = ["# エピソードの結果（終了時に新しくできた on / in の関係）", ""]
    for name in args.names:
        records = [json.loads(line) for line in (root / name / "prompts.jsonl").read_text().splitlines()]
        summary = json.loads((root / name / "summary.json").read_text())
        lines += [f"## {name}", "", "| task | プロンプト（先頭） | 成功 | 結果（回数） |", "|---|---|---|---|"]
        for t in summary["per_task"]:
            recs = [r for r in records if r["task_id"] == t["task_id"]]
            counts = Counter(outcome(r) for r in recs)
            cell = "<br>".join(f"{v} × {k}" for k, v in counts.most_common())
            prompt = recs[0]["prompt"][:90].replace("|", "/")
            lines.append(f"| {t['task_id']} | {prompt} | {sum(t['successes'])}/{len(t['successes'])} | {cell} |")
        lines.append("")
    text = "\n".join(lines)
    (root / "outcomes.md").write_text(text)
    print(text)
    print(f"saved: {root / 'outcomes.md'}")


if __name__ == "__main__":
    main()
