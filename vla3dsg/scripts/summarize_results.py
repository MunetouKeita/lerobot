"""複数の評価結果（run_eval.py の results/<root>/<name>/）を表にまとめる。

- comparison.md: 条件ごと・タスクごとの成功率と、プロンプトの長さ（summary.json と prompts.jsonl から）
- outcomes.md: 各エピソードで何をどこに置いたか。開始時と終了時の SG を比べ、終了時に新しくできた on / in の関係
  （例: "black bowl 2 on plate"）を数える。終了時の SG がない結果では作らない

--scenes を付けると、<root>/<シーン>/<条件>/ の結果をシーンごとにまとめ、<root>/comparison.md にシーン × 条件の
成功率の表を作る。

    uv run python vla3dsg/scripts/summarize_results.py --root zeroshot --scenes standard shuffle hidden hidden_decoy \
        --names base base_short base_full base_wrong target sg_command
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402
from vla3dsg.prompting.prompt_condition import count_tokens  # noqa: E402

SUPPORT_RELATIONS = ("on", "in")


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def comparison(summaries: dict[str, dict], records: dict[str, list[dict]]) -> str:
    names = list(summaries)
    lines = ["## 全体", "", "| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |", "|---|---|---|---|"]
    for n, s in summaries.items():
        lengths = [count_tokens(r["prompt"]) for r in records[n]]
        median = f"{statistics.median(lengths):.0f}" if lengths else "-"
        desc = settings.PROMPT_CONDITIONS.get(n, "")
        lines.append(f"| {n} | {desc} | {s['pc_success']:.1f}%（{s['n_success']}/{s['n_episodes']}） | {median} |")

    lines += ["", "## タスクごと（成功回数）", "", "| task | 指示文 | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for t0 in summaries[names[0]]["per_task"]:
        cells = []
        for n in names:
            t = next(t for t in summaries[n]["per_task"] if t["suite"] == t0["suite"] and t["task_id"] == t0["task_id"])
            cells.append(f"{sum(t['successes'])}/{len(t['successes'])}")
        lines.append(f"| {t0['suite']} {t0['task_id']} | {t0['instruction']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def placements(sg: dict) -> set[str]:
    return {f"{s} {r} {o}" for s, r, o in sg["relations"] if r in SUPPORT_RELATIONS}


def outcome(record: dict) -> str:
    new = sorted(placements(record["final_scene_graph"]) - placements(record["scene_graph"]))
    return ", ".join(new) if new else "変化なし"


def outcomes(summaries: dict[str, dict], records: dict[str, list[dict]]) -> str:
    lines = ["# エピソードの結果（終了時に新しくできた on / in の関係）", ""]
    for n, s in summaries.items():
        lines += [f"## {n}", "", "| task | プロンプト（先頭） | 成功 | 結果（回数） |", "|---|---|---|---|"]
        for t in s["per_task"]:
            recs = [r for r in records[n] if r["task_id"] == t["task_id"]]
            counts = Counter(outcome(r) for r in recs)
            cell = "<br>".join(f"{v} × {k}" for k, v in counts.most_common())
            prompt = recs[0]["prompt"][:90].replace("|", "/")
            lines.append(f"| {t['task_id']} | {prompt} | {sum(t['successes'])}/{len(t['successes'])} | {cell} |")
        lines.append("")
    return "\n".join(lines)


def matrix(root: Path, scenes: list[str], names: list[str]) -> str:
    """シーン × 条件の成功率の表。"""
    lines = ["| 条件 | 内容 | " + " | ".join(settings.SCENE_LABELS.get(s, s) for s in scenes) + " |", "|---|---|" + "---|" * len(scenes)]
    for n in names:
        cells = []
        for scene in scenes:
            s = json.loads((root / scene / n / "summary.json").read_text())
            cells.append(f"{s['pc_success']:.0f}%（{s['n_success']}/{s['n_episodes']}）")
        lines.append(f"| {n} | {settings.PROMPT_CONDITIONS.get(n, '')} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def summarize(root: Path, names: list[str]) -> None:
    summaries = {n: json.loads((root / n / "summary.json").read_text()) for n in names}
    records = {n: load_records(root / n / "prompts.jsonl") for n in names}

    outputs = {"comparison.md": comparison(summaries, records)}
    if all(recs and all("final_scene_graph" in r for r in recs) for recs in records.values()):
        outputs["outcomes.md"] = outcomes(summaries, records)
    else:
        print("終了時の SG がない結果を含むため、outcomes.md は作らない")
    for filename, text in outputs.items():
        (root / filename).write_text(text)
        print(text)
        print(f"saved: {root / filename}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="results/ 以下の親ディレクトリ")
    parser.add_argument("--names", nargs="+", required=True, help="比較する結果（root の下のディレクトリ名）")
    parser.add_argument("--scenes", nargs="+", help="シーンごとのディレクトリ（root/<シーン>/<条件>/）")
    args = parser.parse_args()

    root = settings.RESULTS_DIR / args.root
    if not args.scenes:
        summarize(root, args.names)
        return
    for scene in args.scenes:
        summarize(root / scene, args.names)
    text = matrix(root, args.scenes, args.names)
    (root / "comparison.md").write_text(text)
    print(text)
    print(f"saved: {root / 'comparison.md'}")


if __name__ == "__main__":
    main()
