"""run.sh の評価結果を、学習前（公式の指示文・SG あり）、SG なし・SG ありの更新 1,000 回・3,000 回の表にまとめて results.md に保存する。"""

import json
from pathlib import Path

REC = Path(__file__).resolve().parent
ZEROSHOT = REC.parents[1] / "zeroshot/kitchen4"
# (シーン, task_id)。vla3dsg_kitchen4 の task の順
ROWS = [("ボウル1個,ボウルランダム", 2), ("ボウル1個,隠れ（ワインラックの裏）", 0), ("ボウル1個,隠れ（キャビネットの裏）", 1)]
COLUMNS = [("学習前", ZEROSHOT / "base"), ("学習前 SG あり", ZEROSHOT / "base_short"),
           *[(f"SG {'なし' if m == 'nosg' else 'あり'} {n} 回", REC / m / f"step{s}")
             for m in ("nosg", "sg") for s, n in (("004000", "1,000"), ("012000", "3,000"))]]


def rate(res_dir: Path, task_id: int) -> tuple[int, int] | None:
    path = res_dir / "summary.json"
    if not path.exists():
        return None
    t = next((t for t in json.loads(path.read_text())["per_task"] if t["task_id"] == task_id), None)
    return None if t is None else (sum(t["successes"]), len(t["successes"]))


def fmt(r: tuple[int, int] | None) -> str:
    return "—" if r is None else f"{r[0]}/{r[1]}"


lines = ["| シーン | " + " | ".join(c for c, _ in COLUMNS) + " |", "|---" * (len(COLUMNS) + 1) + "|"]
for name, task_id in ROWS:
    lines.append(f"| {name} | " + " | ".join(fmt(rate(d, task_id)) for _, d in COLUMNS) + " |")
# 隠れた 2 シーンは画像がほぼ同じで SG だけが違う。SG を使わなければ合わせて半分程度が上限
hidden = []
for _, d in COLUMNS:
    rs = [rate(d, t) for _, t in ROWS[1:]]
    hidden.append(None if None in rs else (sum(r[0] for r in rs), sum(r[1] for r in rs)))
lines.append("| ボウル1個,隠れ（2シーン） | " + " | ".join(fmt(h) for h in hidden) + " |")
(REC / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
