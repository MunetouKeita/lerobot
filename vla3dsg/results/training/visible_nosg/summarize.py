"""run.sh の評価結果を、学習前・更新 1,000 回・3,000 回の表にまとめて results.md に保存する。"""

import json
from pathlib import Path

REC = Path(__file__).resolve().parent
ZEROSHOT = REC.parents[1] / "zeroshot"
ROWS = [  # (シーン, 結果の場所, task_id, 学習前の値の場所)
    ("ボウルだけシャッフル", "train_scenes", 0, None),
    ("ボウルだけシャッフル（隠れたおとりあり）", "train_scenes", 3, None),
    ("ボウルを手前左へ（固定）", "layout_far", 1, ZEROSHOT / "layout_check/bowl_shuffle/base"),
    ("ボウルを遠くへ", "layout_far", 2, ZEROSHOT / "layout_check/bowl_far/base"),
    ("ボウルを遠く、皿から離して", "layout_far", 5, ZEROSHOT / "layout_check/bowl_far_apart/base"),
    ("標準", "standard", 0, ZEROSHOT / "standard/base"),
]
COLUMNS = [("学習前", "before"), ("更新 1,000 回", "step004000"), ("更新 3,000 回", "step012000")]


def rate(res_dir: Path, task_id: int) -> str:
    path = res_dir / "summary.json"
    if not path.exists():
        return "—"
    tasks = json.loads(path.read_text())["per_task"]
    t = next((t for t in tasks if t["task_id"] == task_id), tasks[0] if len(tasks) == 1 else None)
    return "—" if t is None else f"{sum(t['successes'])}/{len(t['successes'])}"


lines = ["| シーン | " + " | ".join(c for c, _ in COLUMNS) + " |", "|---" * (len(COLUMNS) + 1) + "|"]
for name, sub, task_id, before in ROWS:
    cells = [rate(before if (key == "before" and before) else REC / key / sub, task_id) for _, key in COLUMNS]
    lines.append(f"| {name} | " + " | ".join(cells) + " |")
(REC / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
