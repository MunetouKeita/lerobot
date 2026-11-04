"""run.sh の評価結果を、学習前（公式の指示文・SG あり）と SG なし・SG ありの更新 1,000 回・3,000 回の表にまとめて results.md に保存する。"""

import json
from pathlib import Path

REC = Path(__file__).resolve().parent
RESULTS = REC.parents[1]
ZEROSHOT = RESULTS / "zeroshot"
BEFORE_41 = RESULTS / "training/visible_nosg/before/train_scenes"  # 4-1 の学習前（task 0・3、公式の指示文）
# (まとまり, シーン, 結果の場所, task_id, 学習前の公式の指示文, 学習前の SG あり)
ROWS = [
    *[("学習用シーン", name, "train_scenes", i, BEFORE_41 if i in (0, 3) else REC / "before/train_scenes_base", REC / "before/train_scenes_sg")
      for i, name in enumerate(["ボウルだけシャッフル", "隠れ", "隠れた方が正解（おとりは見える）", "見える方が正解（おとりは隠れ）"])],
    *[("2-2 の 4 シーン", name, "goal", i, ZEROSHOT / key / "base", ZEROSHOT / key / "base_short")
      for i, (key, name) in enumerate([("standard", "標準"), ("shuffle", "場所シャッフル"), ("hidden", "標準＋隠れ"), ("hidden_decoy", "標準＋隠れ（おとりあり）")])],
    # 標準＋隠れ（おとりあり）と対になるシーン（2026-11-04 追加、vla3dsg_goal の task 4）
    ("標準の位置のボウル＋裏のおとり", "標準＋見える方が正解（おとりは裏）", "goal_visible_decoy", 4, ZEROSHOT / "visible_decoy" / "base", None),
    *[("2-3 の遠いボウル", name, "layout_far", i, ZEROSHOT / "layout_check" / key / "base", None)
      for i, key, name in [(1, "bowl_shuffle", "ボウルを手前左へ（固定）"), (2, "bowl_far", "ボウルを遠くへ"), (5, "bowl_far_apart", "ボウルを遠く、皿から離して")]],
]
COLUMNS = ["学習前", "学習前 SG あり", "SG なし 1,000 回", "SG なし 3,000 回", "SG あり 1,000 回", "SG あり 3,000 回"]
TRAINED = [f"{m}/step{s}" for m in ("nosg", "sg") for s in ("004000", "012000")]


def rate(res_dir: Path | None, task_id: int) -> tuple[int, int] | None:
    path = res_dir / "summary.json" if res_dir else None
    if path is None or not path.exists():
        return None
    tasks = json.loads(path.read_text())["per_task"]
    t = next((t for t in tasks if t["task_id"] == task_id), tasks[0] if len(tasks) == 1 else None)
    return None if t is None else (sum(t["successes"]), len(t["successes"]))


def fmt(r: tuple[int, int] | None) -> str:
    return "—" if r is None else f"{r[0]}/{r[1]}"


lines = ["| まとまり | シーン | " + " | ".join(COLUMNS) + " |", "|---" * (len(COLUMNS) + 2) + "|"]
totals: dict[tuple[str, int], list[int]] = {}
for group, name, sub, task_id, before, before_sg in ROWS:
    cells = [rate(before, task_id), rate(before_sg, task_id), *[rate(REC / key / sub, task_id) for key in TRAINED]]
    for k, c in enumerate(cells):
        if c is not None:
            t = totals.setdefault((group, k), [0, 0])
            t[0] += c[0]
            t[1] += c[1]
    lines.append(f"| {group} | {name} | " + " | ".join(fmt(c) for c in cells) + " |")
for group in dict.fromkeys(r[0] for r in ROWS):
    lines.append(f"| {group} | 計 | " + " | ".join(fmt(totals.get((group, k))) for k in range(len(COLUMNS))) + " |")
(REC / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
