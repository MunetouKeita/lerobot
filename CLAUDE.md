# CLAUDE.md — VLA×3DSG（研究テーマ1）

このリポジトリは、本家 LeRobot（`huggingface/lerobot`）をフォークしたリポジトリ（`MunetouKeita/lerobot`）で、情報系修士課程のロボット研究「VLA×3DSG」の実験に使う作業場所です。
LeRobot 公式の `AGENTS.md`（upstream の `CLAUDE.md` のリンク先）の内容を統合しています（本体のアーキテクチャと本体を変更する場合のルールは `vla3dsg/docs/lerobot_architecture.md`）。
計画と進捗は `vla3dsg/progress_management.md` にあります。作業開始時に必ず読み、作業後に更新してください。各実験の詳しい設定と結果は `vla3dsg/experiments.md`（必要なときに読む）。

## 研究概要

- 目的: VLAの言語指示に3D Scene Graph（3DSG）の情報を加え、環境コンテキストを把握したVLAを実現する
- 解決したい問題: 2D画像のみに依存するVLAは、隠れた物体・見えにくい物体（オクルージョン）の操作が苦手
- 手法の核: 3DSGのノード（物体）とエッジ（空間関係）をテキスト化し、言語プロンプトの一部としてVLAに入力する
  - モデル構造を大きく変えずに「Aの裏にあるB」のような位置関係をVLAに与える
- 最終的な目標: 移動ロボットがSGの情報をもとに、隠れた物体でも掴めるようになる（現段階ではテーブル上の隠れた物体のみを対象とする）

## 大きな方針

1. LIBERO環境を構築し、MolmoAct2（LIBERO向けファインチューニング済みモデル）が動くことを確認する
2. SG の与え方と環境を変えた次の 3 つの実験を、追加学習なし（ゼロショット）とありで比較する。まず追加学習なしで色々な条件を比較する（詳細は `progress_management.md` の「現在の設計方針」）
   - 実験1: 環境は変えず、SG のような関係性を JSON・テキストにして指示文に加える
   - 実験2: 隠れた物体のあるシーンに環境を変え、SG をテキストで加える
   - 実験3: テキストではなく、SG エンコーダーを追加して入力する（学習なしでは意味をなさないため、追加学習ありのみ）
3. 結果を踏まえ、UMI型ハンドヘルド教示デバイスを作成し、実機の教師データの取得へ進む

## これまでの経緯（再発防止のため）

- LeIsaac（LeRobot × IsaacLab）+ SmolVLA / MolmoAct2 で実験していたが、学習が安定せず中止した
  - LeRobot v0.5.0 から関節角度の基準が変更されており、MolmoAct2-SO100_101 の挙動悪化の原因になった
- 現在はロボット操作タスク評価に特化した LIBERO で体系的に検証する方針に切り替えた
- LIBEROのロボットは Franka Panda であり、SO-ARM（SO100/SO101）は含まれない。SO101リーダーアームとの連携は行わない
- LeIsaac・SO101 関連のコードは扱わない。LeRobot 公式の `AGENT_GUIDE.md` は SO-101 向けのため、本研究では参照不要

## リポジトリ構成とコードの置き場所

各スクリプトの詳しい使い方・オプションは、ファイルの先頭の説明にある。

| 場所 | 内容 |
|---|---|
| `src/lerobot/` | LeRobot 本体。原則として変更しない |
| `vla3dsg/config/` | `settings.py`: 設定値（パス、シード、評価引数 `molmoact2_eval_args`、デモの設定 `DEMO_TASK_SPECS` など）の一元管理。`instructions_ja.py`: 指示文の日本語訳（テロップ用）。`object_names.py`: SG のノード名 |
| `vla3dsg/scene_graph/` | シミュレータの状態から正解の SG を作る（`builder.py`: 全物体の関係、`relevant.py`: 対象を同じ種類の物体と見分ける最小の関係の短い SG と誤った SG）、テキスト化（`textify.py`） |
| `vla3dsg/prompting/` | プロンプト条件に従ってエピソードごとに指示文を差し替える（`prompt_condition.py`） |
| `vla3dsg/envs/` | `lerobot-eval` のプラグインの環境タイプ `libero_vla3dsg`、自作スイートの登録（`custom_suites.py`）、自作タスクを作る処理（`custom_task_builder.py`: 配置範囲の書き換え・配置のサンプリングと除外・見え方の計測） |
| `vla3dsg/custom_tasks/<スイート>/` | 自作タスク（BDDL・初期状態 `.pruned_init`・`tasks.json`・確認用の画像 `previews/overview.png`）。`--suite <スイート>` で評価できる |
| `vla3dsg/demos/` | スクリプト制御（`scripted.py`: シミュレータの正解の位置を使った pick-and-place） |
| `vla3dsg/visualization/` | ロールアウトの動画（`rollout_video.py`: agentview と手首カメラ、各タスク先頭 10 本＋失敗）、自作スイートの 6 視点の画像（`scene_overview.py`） |
| `vla3dsg/scripts/` | `run_eval.py`: 評価と結果の保存、`make_custom_task.py`: 自作タスクの作成、`generate_demos.py`: デモの自動生成（`--check` でできるかの確認、`--report` で公式デモと比較）、`summarize_results.py`: 条件の比較表、`show_conditions.py`: 評価前の確認資料、`make_demo_video.py`: テロップ付きデモ動画、`make_comparison_video.py`: ゼミ用の比較動画（並べ方は JSON）、`measure_inference.py`: 推論時間と GPU メモリ |
| `vla3dsg/tests/test_<対象>.py` | モジュール単位のテスト（`test_envs.py`・`test_scene_graph.py`・`test_rollout_video.py`） |
| `vla3dsg/results/<名前>/` | 1 実験分の結果。`README.md`・`summary.json`・`conditions.json`・`eval_info.json` は git 管理、`videos/` と `eval.log` は管理外（ゼミ報告 `results/seminar/<日付>/videos/` の比較動画だけは git 管理） |
| `vla3dsg/data/<名前>/` | 生成したデータセット（git 管理外）。生成の記録は `vla3dsg/results/demos/<名前>/` |
| `vla3dsg/tmp/` | テスト・計測の使い捨て出力（git 管理外。いつ消してもよい） |
| `vla3dsg/docs/` | 調査メモ（LIBERO のタスク定義、LeRobot の LIBERO の読み込み、LeRobot 本体のアーキテクチャ、学習サーバの使い方） |
| `vla3dsg/progress_management.md`・`vla3dsg/experiments.md` | 計画と進捗・各実験の設定と結果 |

- カスタムシーンの登録やプロンプト改変は、`vla3dsg/` 側のコード（ラッパー、`ProcessorStep` の追加、LIBEROへのベンチマーク登録処理など）で実現する
- やむを得ず `src/lerobot/` を変更する場合は、`vla3dsg/docs/lerobot_architecture.md` のルールに従い、理由と差分を `progress_management.md` の作業記録に残す
- ブランチ: 作業は `vla3dsg` ブランチで行い、`main` は upstream（`huggingface/lerobot`）の追従用にする。remote は `origin`（フォーク）と `upstream`（本家）
  - upstream の取り込み: `git fetch upstream` → `main` を `upstream/main` に早送りして `origin` に push → `vla3dsg` を `main` にリベース → `uv sync` とテスト・1 エピソード評価で動作確認
- 使用した LeRobot のコミットを記録する。このファイルは upstream の `CLAUDE.md`（`AGENTS.md` へのシンボリックリンク）を通常ファイルで置き換えているため、upstream を取り込むと競合しうる。その場合は `AGENTS.md` 側の更新内容を確認して反映する

## 使用するソフトウェア

| 項目 | 内容 |
|---|---|
| 評価・学習基盤 | 本家 LeRobot のフォーク（main、v0.6系）。`molmoact2`・`libero`・`viz`（Rerun）の extra を使う |
| シミュレータ | LIBERO（MuJoCo / robosuite ベース、`hf-libero` パッケージ経由） |
| VLA | MolmoAct2。元の HF チェックポイント `allenai/MolmoAct2-LIBERO`（`norm_tag=libero`、float32、約21GB、推論時の VRAM ピーク約26GB）に統一する。LeRobot 形式の `allenai/MolmoAct2-LIBERO-LeRobot` は `config.json` が現在の LeRobot と非互換のため使わない |
| 主要ライブラリ | PyTorch、Hugging Face（datasets、Hub、accelerate）、draccus（設定・CLI）、Gymnasium（環境） |
| パッケージ管理 | uv（`uv.lock` に従ってインストール） |

- LeRobot は Python 3.12 以上が必要。Ubuntu 22.04 標準の Python は 3.10 のため、uv で Python 3.12 を取得して仮想環境を作る。研究テーマ2（習慣考慮型3DSG）用の Python 3.10 venv とは混ぜない
- 本家 LeRobot では MolmoAct2-Think は未対応（通常の MolmoAct2 のみ）
- Ai2 のフォーク（`allenai/lerobot` の `molmoact2-hf-inference`、v0.5.1固定）は論文値の厳密な再現用。ベースラインが論文値と大きくずれたときの切り分けにだけ使う
- LIBERO の設定 `~/.libero/config.yaml` は既定値で作成済み（初回 import 時の対話を避けるため。評価にデモデータは不要）。アセットは初回起動時に `~/.cache/libero/assets` へ自動ダウンロードされる

## OS・GPU・開発環境

| 項目 | 内容 |
|---|---|
| OS | Ubuntu 22.04 |
| GPU | NVIDIA GeForce RTX 5090（VRAM 32GB、Blackwell / sm_120） |
| CUDA | nvcc 12.8。PyTorch は `uv.lock` で固定される CUDA 12.8 ビルド（torch 2.11.0+cu128）を使う |
| Python | 3.12（uv 仮想環境 `.venv/`） |

- `torch.cuda.get_arch_list()` に `sm_120` が含まれることを確認する（`no kernel image is available for execution on the device` が出たら古いホイールが入っている）
- 動画のデコード（TorchCodec）とテストに、システムの ffmpeg を使う
- このPCの GPU は ollama も使っている。ollama は止めない
- ヘッドレス描画と再現性のため、実行前に以下を設定する

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

### 学習サーバ（RTX 6000 Ada × 4）

長い学習は学習サーバで行い、このPCは評価とデータ作りに使う。接続（`ssh munetou-6000ada`）・仮想環境・描画の設定は `vla3dsg/docs/training_server.md`。

- 共有サーバのため、次を守る
  - GPU は基本的に 2 枚まで使う。他のユーザーが使っていることが多いので、使う前に `nvidia-smi` で空き（メモリ・使用率）を確かめ、`CUDA_VISIBLE_DEVICES` で指定する
  - sudo 権限はあるが、sudo を実行するときは必ず事前にユーザーの許可を得る
- ホームディレクトリ（`/home/munetou`）の中は自由に変更してよい

## セットアップと主要コマンド

```bash
uv python pin 3.12                                  # .python-version は .gitignore 対象のため、クローンごとに実行する
uv sync --locked --extra molmoact2 --extra libero --extra viz   # 本研究で使う依存関係
uv sync --locked --extra molmoact2 --extra libero --extra viz --extra test --extra dev   # テスト・開発ツールも必要な場合（本研究の extra も必ず含める）
git lfs install && git lfs pull                     # LeRobot のテスト用アーティファクト（テストを回す場合のみ）
```

```bash
uv run python vla3dsg/tests/test_<対象>.py          # 本研究のモジュールテスト
uv run python vla3dsg/scripts/run_eval.py --name baseline/xxx --suite libero_spatial,libero_goal --task-ids 0 5 --n-episodes 20 --annotated-video   # 評価（結果は results/<name>/）
uv run python vla3dsg/scripts/run_eval.py --name zeroshot/hidden/base_short --suite vla3dsg_goal --task-ids 2 --n-episodes 20 --prompt-condition base_short --annotated-video   # プロンプト条件（settings.PROMPT_CONDITIONS）
uv run python vla3dsg/scripts/make_custom_task.py --suite vla3dsg_goal --name <タスク名> --base libero_goal/put_the_bowl_on_the_plate --language "<指示文>" --region <領域名>=x0,y0,x1,y1 --target <物体> --occluder <遮る物体>   # 自作タスク（--preview・--remove-object・--add-object・--copy-init・--min-distance は先頭の説明）
uv run python vla3dsg/scripts/generate_demos.py --name <名前> --suite vla3dsg_goal_train --task-ids 0 1 2 3 --n-episodes 50   # デモの自動生成（設定は settings.DEMO_TASK_SPECS）
uv run python vla3dsg/scripts/summarize_results.py --root zeroshot --scenes standard shuffle hidden hidden_decoy --names base base_short base_full base_wrong sg_command   # シーン × 条件の比較表
uv run python vla3dsg/scripts/show_conditions.py --suite vla3dsg_goal --out zeroshot/conditions   # 評価前の確認資料
uv run python vla3dsg/scripts/make_demo_video.py --name baseline/xxx --keep-failures-only   # デモ動画と失敗動画だけを残す
pre-commit run --all-files                          # Lint・フォーマット（ruff、typos、bandit など）
```

- Python の実行は `uv run` を優先する（素の `python` や `pip` は使わない）
- `uv sync` で extra の指定を変えると、指定しなかった extra のパッケージは削除される。毎回同じ extra を指定する

## 開発方針

本研究のコード（`vla3dsg/`）:

- 設定値は `vla3dsg/config/settings.py` にまとめ、スクリプトからは `from vla3dsg.config import settings` で参照する（`vla3dsg` はパッケージとして扱う）
- テストは `vla3dsg/tests/test_<対象>.py` に置く
- 評価は `vla3dsg/scripts/run_eval.py` で行い、結果は条件（チェックポイント、スイート、タスクID、シード、プロンプト条件、git コミット）とともに `vla3dsg/results/<名前>/` に保存する
- 評価結果は成功率だけでなく、動画で確認できるように保存する（`run_eval.py --annotated-video`）
- LIBERO評価では `policy.per_episode_seed=true` と `policy.eval_seed` を使い、シードを固定する
- LIBERO評価では環境タイプ `libero_vla3dsg` を使う（`num_steps_wait` の既定値が 50。MolmoAct2 の報告値と同じ条件）
  - `run_eval.py` はこの指定を自動で行う。`lerobot-eval` を直接使う場合は、リポジトリのルートで `PYTHONPATH=. uv run lerobot-eval --env.discover_packages_path=vla3dsg.envs --env.type=libero_vla3dsg ...`
- 評価では MolmoAct2 の指示文の正規化を切り（`--policy.normalize_language=false`）、元の指示文だけを `prompting/prompt_condition.py` で正規化する。SG のテキスト（JSON の括弧など）を壊さないため。系列長の上限も `--policy.max_sequence_length=1024` に広げる（`settings.molmoact2_eval_args` で自動）
- LeRobot の import は絶対 import（`from lerobot.module import X`）を使う

## 共通の方針

他のプロジェクトでも共通の方針。このリポジトリでの具体的な場所やコマンドは、上の各節を参照する。

### 安全と影響範囲

- 違法行為は行わない
- 共有サーバの他のユーザーや、PC 内の他のプロジェクトに影響する可能性のある作業は、事前にユーザーの許可を得る（例: 他のユーザー・他のプロジェクトのプロセスを止める、共有の設定・ディレクトリを変える、sudo を使う、GPU を多く使う）

### 設定の一元管理

- パス、モデル名、しきい値、接続情報などの設定値は `config/settings.py` に一元的にまとめる（このリポジトリでは `vla3dsg/config/settings.py`）
- モジュールやスクリプトに設定値を直接書かず、settings から参照する
- 接続情報などの秘匿情報は `.env` から読み込む（`.env` は git 管理外）

### コメント

- コメントは日本語で、簡単に書く
- 処理の意図が分かりにくい箇所にだけ付け、コードを読めば分かることは書かない

### 変更の進め方

- 不明点や方針に関わる判断は、勝手に決めずに確認を求める
- 既存モジュールの大きな変更や設計の変更は、方針をユーザーに相談してから行う
- フォルダ構成やファイル名の変更は、案を示して確認を取ってから行う
- 時間のかかる実験や新しい検証は、目的・方法・所要時間の見込みを示した計画を立ててから進める
- フォルダ構成や実験設定は、なるべくシンプルにする。実験は、条件を変えながら何度も行うより、複数の条件をまとめた少ない回数の実験にする。複雑になる場合は数回の実験に分けてもよいが、上位互換となる実験や結果が得られたら、古いほうは削除する
- モジュールなど小さなまとまりごとにテストしてから、全体の処理に組み込む
- 実験結果は条件（設定・データ・シード・git のコミットなど）とともに保存し、再現できるようにする。同じ名前の結果は上書きしない

### Git

- コミットは内容ごと（コード、ドキュメント、整理など）に分け、メッセージは既存に合わせて日本語の `feat:` / `fix:` / `docs:` / `chore:` 形式にする（このリポジトリでは `feat(vla3dsg): ...` のようにスコープを付ける）
- コミットや push は、ユーザーに指示されたときだけ行う
- コミットメッセージや PR に、Claude を共同制作者として書かない（`Co-Authored-By: Claude ...` や「Generated with Claude Code」などの行を付けない）

### ドキュメント（進捗管理）のまとめ方

- 進捗管理のファイルは、このリポジトリでは `vla3dsg/progress_management.md`（各実験の詳細は `vla3dsg/experiments.md`）。作業の区切りごとにチェックボックスと作業記録を更新する
- CLAUDE.md には進捗に依存しない情報だけを書き、方針・進捗・実験結果は進捗管理のファイルに書く
- 実験結果は、大きなまとまりごと（例: 抽出、翻訳、描画）に分け、各実験を「概要、目的、結果、読み取れること」の順に書く
- 上位互換の実験やデータが得られたら、古いほうの表や記述は削除する。重複する表はまとめ、方針や決定事項以外の重要度が低い記録は圧縮する
- 解決した課題は、概要とユーザーの方針（決定事項）だけを残し、そこに至るまでの不要な過程（試行錯誤、途中の数値など）は削除する。ただし、どうしてそうしたか（判断の理由）と、今後課題になりそうな検証結果（うまくいかなかった方法とその原因、残っている制約など）は消さない
- 専門用語には「用語の補足」の ※ を付ける
- 日付ごとの作業記録は、1 日 1 行の表にまとめる
- 背景を知らない人にも分かる書き方にする

### コミュニケーション

- 回答は敬語・日本語で行う
- 外部の資料を引用する場合は、存在を確認したうえで URL を示す
- 処理を実行するときは、所要時間の概算を先に伝える。長い処理では、途中でも残り時間の見込みを伝える
- 現状を聞かれたときは、目的・方式・結果（表）・分かっていること・未解決の課題・次の候補の順に、簡潔にまとめる

## 参考リンク

- LeRobot（本家）: https://github.com/huggingface/lerobot
- LeRobot のインストール手順: https://github.com/huggingface/lerobot/blob/main/docs/source/installation.mdx
- LeRobot の MolmoAct2 ドキュメント: https://github.com/huggingface/lerobot/blob/main/docs/source/molmoact2.mdx
- LeRobot の LIBERO ドキュメント: https://github.com/huggingface/lerobot/blob/main/docs/source/libero.mdx
- LeRobot の LIBERO 環境の実装: https://github.com/huggingface/lerobot/blob/main/src/lerobot/envs/libero.py
- LIBERO: https://github.com/Lifelong-Robot-Learning/LIBERO
- MolmoAct2: https://github.com/allenai/molmoact2
- Ai2 のフォーク（論文値の再現用）: https://github.com/allenai/lerobot/tree/molmoact2-hf-inference
- UMI: https://umi-gripper.github.io/
