"""vla3dsg/custom_tasks/ にある自作スイートを、LIBERO のベンチマークとして登録する。

スイートごとに custom_tasks/<スイート名>/tasks.json を置く（scripts/make_custom_task.py が作る）:
    {"max_steps": 300, "tasks": [{"name": ..., "language": ..., "bddl_file": ..., "init_states_file": ...}]}

Task.problem_folder に絶対パスを指定すると、LeRobot は LIBERO のパスの外の BDDL・初期状態を読める
（docs/lerobot_libero_loading.md）。登録はこのモジュールの import 時（lerobot-eval のプラグイン読み込み時）に行う。
"""

import json
from pathlib import Path

from libero.libero.benchmark import BENCHMARK_MAPPING, Benchmark, Task

from vla3dsg.config import settings


def load_suite_spec(suite_dir: Path) -> dict:
    return json.loads((suite_dir / "tasks.json").read_text())


def _make_benchmark_class(suite_name: str, suite_dir: Path) -> type[Benchmark]:
    spec = load_suite_spec(suite_dir)

    def __init__(self: Benchmark, task_order_index: int = 0) -> None:
        Benchmark.__init__(self, task_order_index=task_order_index)
        self.name = suite_name
        # LIBERO の _make_benchmark は元のスイート名を前提にするため使わない
        self.tasks = [
            Task(
                name=t["name"],
                language=t["language"],
                problem="Libero",
                problem_folder=str(suite_dir.resolve()),
                bddl_file=t["bddl_file"],
                init_states_file=t["init_states_file"],
            )
            for t in spec["tasks"]
        ]
        self.n_tasks = len(self.tasks)

    return type(suite_name.upper(), (Benchmark,), {"__init__": __init__})


def location_language(task: Task) -> str:
    """場所を書いた指示文（プロンプト条件 P1）。自作タスクは tasks.json の language_with_location、LIBERO のタスクは元の指示文。"""
    folder = Path(task.problem_folder)
    if folder.is_absolute() and (folder / "tasks.json").exists():
        entry = next(t for t in load_suite_spec(folder)["tasks"] if t["name"] == task.name)
        return entry.get("language_with_location", task.language)
    return task.language


def custom_suite_max_steps() -> dict[str, int]:
    """自作スイート名 → 最大ステップ数。"""
    if not settings.CUSTOM_TASKS_DIR.exists():
        return {}
    return {
        d.name: int(load_suite_spec(d)["max_steps"])
        for d in sorted(settings.CUSTOM_TASKS_DIR.iterdir())
        if (d / "tasks.json").exists()
    }


def register_custom_suites() -> list[str]:
    names = []
    for suite_name in custom_suite_max_steps():
        # LIBERO の登録名は小文字のクラス名
        BENCHMARK_MAPPING[suite_name.lower()] = _make_benchmark_class(suite_name, settings.CUSTOM_TASKS_DIR / suite_name)
        names.append(suite_name)
    return names


register_custom_suites()
