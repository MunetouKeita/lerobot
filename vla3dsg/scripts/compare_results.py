"""複数の評価結果（run_eval.py の results/<name>/）を、タスクごと・全体の成功率の表にまとめる。

    uv run python vla3dsg/scripts/compare_results.py --root exp1/libero_spatial_n5 --names A B1 B2 B3 C D

--root の下の各 name の summary.json と prompts.jsonl を読み、Markdown の表を表示して <root>/comparison.md に保存する。
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vla3dsg.config import settings  # noqa: E402
from vla3dsg.prompting.prompt_condition import count_tokens  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="results/ 以下の親ディレクトリ")
    parser.add_argument("--names", nargs="+", required=True, help="比較する結果（root の下のディレクトリ名）")
    args = parser.parse_args()

    root = settings.RESULTS_DIR / args.root
    summaries = {n: json.loads((root / n / "summary.json").read_text()) for n in args.names}
    tasks = [(t["suite"], t["task_id"], t["instruction"]) for t in summaries[args.names[0]]["per_task"]]

    lines = ["## 全体", "", "| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |", "|---|---|---|---|"]
    for n in args.names:
        s = summaries[n]
        prompts_path = root / n / "prompts.jsonl"
        lengths = [count_tokens(json.loads(l)["prompt"]) for l in prompts_path.read_text().splitlines()] if prompts_path.exists() else []
        median = f"{statistics.median(lengths):.0f}" if lengths else "-"
        desc = settings.PROMPT_CONDITIONS.get(n, "")
        lines.append(f"| {n} | {desc} | {s['pc_success']:.1f}%（{s['n_success']}/{s['n_episodes']}） | {median} |")

    lines += ["", "## タスクごと（成功回数）", "", "| task | 指示文 | " + " | ".join(args.names) + " |", "|---|---|" + "---|" * len(args.names)]
    for suite, task_id, instruction in tasks:
        cells = []
        for n in args.names:
            t = next(t for t in summaries[n]["per_task"] if t["suite"] == suite and t["task_id"] == task_id)
            cells.append(f"{sum(t['successes'])}/{len(t['successes'])}")
        lines.append(f"| {suite} {task_id} | {instruction} | " + " | ".join(cells) + " |")

    text = "\n".join(lines) + "\n"
    (root / "comparison.md").write_text(text)
    print(text)
    print(f"saved: {root / 'comparison.md'}")


if __name__ == "__main__":
    main()
