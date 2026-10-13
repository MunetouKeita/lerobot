# LeRobot が LIBERO のタスクを読み込む流れと、カスタムスイートの登録方法

調査日: 2026-10-13。LeRobot `200ee535`（`src/lerobot/envs/libero.py`、`src/lerobot/envs/configs.py`）。

## 1. 読み込みの流れ

```
lerobot-eval --env.type=libero(_vla3dsg) --env.task=<スイート> --env.task_ids=[...]
  └ LiberoEnv（設定, configs.py）.create_envs()
      └ create_libero_envs()（libero.py）
          ├ _get_suite(name): libero.benchmark.get_benchmark_dict()[name]() でスイートを作る
          │    登録されていない名前はエラー（"Unknown LIBERO suite"）
          ├ _select_task_ids(): task_ids を検証（省略時は全タスク）
          └ タスクごとに LiberoEnv（gym.Env, libero.py）を n_envs 個作る
              ├ task = suite.get_task(task_id)
              │    task.name → ログ・動画のタスク名、task.language → ポリシーに渡す指示文
              ├ BDDL のパス = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
              ├ 初期状態 = torch.load(Path(get_libero_path("init_states")) / task.problem_folder / ファイル名)
              └ 最大ステップ数 = TASK_SUITE_MAX_STEPS[スイート名]（未登録の名前は 500）。episode_length で上書きできる
```

reset（`LiberoEnv.reset`）:

1. 初回だけ `OffScreenRenderEnv(bddl_file_name=..., camera_heights/widths=観測サイズ, control_freq=20)` を作る
2. `env.seed(seed)` → `env.reset()`（BDDL に従って配置）
3. `init_states=True` なら `env.set_init_state(init_states[episode_index % 50])` で初期状態に上書き
4. 何もしない動作を `num_steps_wait` 回（`libero_vla3dsg` では 50）進めて物体を落ち着かせる

step（`LiberoEnv.step`）: 行動を適用し、`env.check_success()`（BDDL の `:goal`）が真になったら終了。

指示文は `observation["task"] = env.call("task_description")`（= `task.language`）としてポリシーの前処理に渡る（`lerobot_eval.py` の `rollout`）。SG をプロンプトに加える場合の差し替え候補はここ（または前処理の `ProcessorStep`）。

## 2. カスタムスイートの登録方法（確認済み）

LIBERO 本体のファイル（site-packages）は変更せず、`vla3dsg/` 側で次のようにすれば、`--env.task=<自作スイート名>` で評価できる。

1. `libero.libero.benchmark.Benchmark` を継承したクラスを作り、`tasks` に `Task(...)` を並べる
2. `Task.problem_folder` に、BDDL と初期状態ファイルを置いた **絶対パス** を指定する
   - `os.path.join(root, "/abs/dir", file)` と `Path(root) / "/abs/dir"` は、どちらも絶対パス側が優先されるため、LIBERO のパスの外のファイルを読める
3. `register_benchmark` で登録する。登録は `create_envs` より前に必要なので、`lerobot-eval` が読み込むプラグイン（`vla3dsg/envs/`）の import 時に行う
4. 最大ステップ数は未登録の名前だと 500 になるため、`--env.episode_length` で指定する（元のスイートの値: spatial・object 280、goal 300、libero_10 520）

確認したコード（scratch で実行、2026-10-13）:

```python
from libero.libero.benchmark import Benchmark, Task, register_benchmark

class VLA3DSG_TEST(Benchmark):
    def __init__(self, task_order_index=0):
        super().__init__(task_order_index)
        self.name = "vla3dsg_test"
        n = "put_the_wine_bottle_on_top_of_the_cabinet"
        self.tasks = [Task(name=n, language="put the wine bottle on top of the cabinet", problem="Libero",
                           problem_folder="/abs/path/to/custom_suite", bddl_file=n + ".bddl",
                           init_states_file=n + ".pruned_init")]
        self.n_tasks = 1

register_benchmark(VLA3DSG_TEST)
# LiberoEnv(task="vla3dsg_test", task_ids=[0]).create_envs(n_envs=1) で、指定した BDDL・初期状態（50, 79）が読み込まれた
```

- `Benchmark._make_benchmark()` は LIBERO のスイート名を前提にするため呼ばず、`tasks` と `n_tasks` を直接設定する
- `Task.language` を自由に指定できるため、指示文をファイル名から切り離せる（隠れあり／隠れなしで同じ指示文にできる）

## 3. カスタムタスクを作る手順（案）

1. 既存の BDDL を元に、物体の配置範囲（`:regions`）や物体の構成を変えた BDDL を `vla3dsg/` 側に置く
2. 初期状態ファイルを生成する（`docs/libero_task_definition.md` の 4 節）。物体が倒れた・重なった配置を除く
3. `vla3dsg/envs/` でスイートとして登録する
4. 初期画像（agentview・手首）を保存し、対象物体が隠れているかを目視で確認する
5. `run_eval.py --suite <自作スイート名>` で評価する（`episode_length` の指定を `run_eval.py`・`settings.py` に追加する）
