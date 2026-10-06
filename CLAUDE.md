# CLAUDE.md — VLA×3DSG（研究テーマ1）

このリポジトリは、本家 LeRobot（`huggingface/lerobot`）をフォークしたリポジトリ（`MunetouKeita/lerobot`）で、情報系修士課程のロボット研究「VLA×3DSG」の実験に使う作業場所です。
LeRobot 公式の `AGENTS.md`（upstream の `CLAUDE.md` のリンク先）の内容を統合しています。
詳細な計画と進捗は `vla3dsg/progress_management.md` にあります。作業開始時に必ず読み、作業後に更新してください。

## 研究概要

- 目的: VLAの言語指示に3D Scene Graph（3DSG）の情報を加え、環境コンテキストを把握したVLAを実現する
- 解決したい問題: 2D画像のみに依存するVLAは、隠れた物体・見えにくい物体（オクルージョン）の操作が苦手
- 手法の核: 3DSGのノード（物体）とエッジ（空間関係）をテキスト化し、言語プロンプトの一部としてVLAに入力する
  - モデル構造を大きく変えずに「Aの裏にあるB」のような位置関係をVLAに与える
- 最終的な目標: 移動ロボットがSGの情報をもとに、隠れた物体でも掴めるようになる（現段階ではテーブル上の隠れた物体のみを対象とする）

## 大きな方針

1. LIBERO環境を構築し、MolmoAct2（LIBERO向けファインチューニング済みモデル）が動くことを確認する
2. LIBEROの環境をカスタマイズ（隠れた物体のあるシーン）し、Scene Graphをプロンプトに追加した場合に、ゼロショット（追加学習なし）で性能が向上するかを確認する
3. 2の結果を踏まえ、UMI型ハンドヘルド教示デバイスを作成し、教師データの取得とファインチューニングへ進む

## これまでの経緯（再発防止のため）

- LeIsaac（LeRobot × IsaacLab）+ SmolVLA / MolmoAct2 で実験していたが、学習が安定せず中止した
  - LeRobot v0.5.0 から関節角度の基準が変更されており、MolmoAct2-SO100_101 の挙動悪化の原因になった
- 現在はロボット操作タスク評価に特化した LIBERO で体系的に検証する方針に切り替えた
- LIBEROのロボットは Franka Panda であり、SO-ARM（SO100/SO101）は含まれない。SO101リーダーアームとの連携は行わない
- LeIsaac・SO101 関連のコードは扱わない。LeRobot 公式の `AGENT_GUIDE.md` は SO-101 向けのため、本研究では参照不要

## リポジトリ構成とコードの置き場所

| 場所 | 内容 |
|---|---|
| `src/lerobot/` | LeRobot 本体。原則として変更しない |
| `vla3dsg/` | 本研究のコード一式（下記） |
| `vla3dsg/config/settings.py` | 設定値（パス、シード、エピソード数、プロンプト形式など）の一元管理 |
| `vla3dsg/scripts/test_<対象>.py` | モジュール単位のテスト |
| `vla3dsg/results/` | 評価結果 |
| `vla3dsg/docs/` | 調査メモ（LIBEROのタスク定義、LeRobotの処理の流れなど） |
| `vla3dsg/progress_management.md` | 詳細計画と進捗 |

- カスタムシーンの登録やプロンプト改変は、`vla3dsg/` 側のコード（ラッパー、`ProcessorStep` の追加、LIBEROへのベンチマーク登録処理など）で実現する
- やむを得ず `src/lerobot/` を変更する場合は、理由と差分を `progress_management.md` の作業ログに記録する
- 使用した LeRobot のコミットを記録する。このファイルは upstream の `CLAUDE.md`（`AGENTS.md` へのシンボリックリンク）を通常ファイルで置き換えているため、upstream を取り込むと競合しうる。その場合は `AGENTS.md` 側の更新内容を確認して反映する

## 使用するソフトウェア

| 項目 | 内容 |
|---|---|
| 評価・学習基盤 | 本家 LeRobot のフォーク（main、v0.6系）。`molmoact2` と `libero` の extra を使う |
| シミュレータ | LIBERO（MuJoCo / robosuite ベース、`hf-libero` パッケージ経由） |
| VLA | MolmoAct2（`allenai/MolmoAct2-LIBERO-LeRobot`、または元のHFチェックポイント `allenai/MolmoAct2-LIBERO`） |
| 主要ライブラリ | PyTorch、Hugging Face（datasets、Hub、accelerate）、draccus（設定・CLI）、Gymnasium（環境） |
| パッケージ管理 | uv（`uv.lock` に従ってインストール） |

- LeRobot は Python 3.12 以上が必要。Ubuntu 22.04 標準の Python は 3.10 のため、uv で Python 3.12 を取得して仮想環境を作る
- 研究テーマ2（習慣考慮型3DSG）用の Python 3.10 venv とは混ぜない
- 本家 LeRobot では MolmoAct2-Think は未対応（通常の MolmoAct2 のみ）
- Ai2 のフォーク（`allenai/lerobot` の `molmoact2-hf-inference`、v0.5.1固定）は論文値の厳密な再現用。ベースラインが論文値と大きくずれたときの切り分けにだけ使う
- チェックポイントは1つあたり約22GB

## OS・GPU・開発環境

| 項目 | 内容 |
|---|---|
| OS | Ubuntu 22.04 |
| GPU | NVIDIA GeForce RTX 5090（VRAM 32GB、Blackwell / sm_120） |
| CUDA | nvcc 12.8。PyTorch は `uv.lock` で固定される CUDA 12.8 ビルド（torch 2.11.0+cu128）を使う |
| Python | 3.12（uv 仮想環境 `.venv/`） |

- `torch.cuda.get_arch_list()` に `sm_120` が含まれることを確認する
  - `no kernel image is available for execution on the device` が出たら古いホイールが入っている
- 動画のデコード（TorchCodec）とテストに ffmpeg が必要。システムの ffmpeg を使う
- ヘッドレス描画と再現性のため、実行前に以下を設定する

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

## セットアップと主要コマンド

```bash
uv sync --locked --extra molmoact2 --extra libero   # 本研究で使う依存関係
uv sync --locked --extra test --extra dev           # LeRobot のテスト・開発ツールが必要な場合
git lfs install && git lfs pull                     # LeRobot のテスト用アーティファクト（テストを回す場合のみ）
```

```bash
uv run python vla3dsg/scripts/test_<対象>.py        # 本研究のモジュールテスト
uv run pytest tests -svv --maxfail=10               # LeRobot 本体のテスト（本体を変更した場合）
pre-commit run --all-files                          # Lint・フォーマット（ruff、typos、bandit など）
```

- Python の実行は `uv run` を優先する（素の `python` や `pip` は使わない）
- `uv sync` で extra の指定を変えると、指定しなかった extra のパッケージは削除される。毎回同じ extra を指定する

## LeRobot のアーキテクチャ（`src/lerobot/`）

- **`scripts/`**: CLI のエントリーポイント（`lerobot-train`、`lerobot-eval`、`lerobot-record` など）。`pyproject.toml` の `[project.scripts]` で対応付け
- **`configs/`**: draccus で解析される dataclass の設定。`train.py` に最上位の `TrainPipelineConfig`、`policies.py` に基底の `PreTrainedConfig`。`draccus.ChoiceRegistry` と `@register_subclass("name")` で多態性を実現
- **`policies/`**: ポリシーごとのサブディレクトリ。すべて `pretrained.py` の `PreTrainedPolicy`（`nn.Module` + `HubMixin`）を継承。`factory.py` に遅延 import 付きのファクトリ。MolmoAct2 は `molmoact2` にある
- **`processor/`**: データ変換パイプライン。`ProcessorStep` 基底クラスとレジストリ。`DataProcessorPipeline` / `PolicyProcessorPipeline` でステップをつなぐ。タスク指示文へのSG追加の候補箇所
- **`datasets/`**: `LeRobotDataset`（エピソード単位のサンプリング + 動画デコード）と `LeRobotDatasetMetadata`
- **`envs/`**: `configs.py` に基底の `EnvConfig`、`factory.py` にファクトリ。各環境のサブクラスが `gym_kwargs` と `create_envs()` を定義。LIBERO は `libero.py`
- **`robots/`、`motors/`、`cameras/`、`teleoperators/`**: ハードウェア抽象化層（本研究では使わない）
- **`types.py`、`configs/types.py`**: 主要な型エイリアスと特徴量の型定義

`src/` 以外の主な構成:

- **`tests/`**: モジュール別の pytest 一式。フィクスチャは `tests/fixtures/`、モックは `tests/mocks/`
- **`docs/source/`**: 公式ドキュメント（`.mdx`）。`molmoact2.mdx`、`libero.mdx` を特に参照する
- **`examples/`**: 用途別のチュートリアルとスクリプト
- **ルートのファイル**: `pyproject.toml`（依存関係・ビルド・ツール設定の唯一の情報源）、`Makefile`（E2Eテスト）、`uv.lock`

## 開発方針

本研究のコード（`vla3dsg/`）:

- 設定値は `vla3dsg/config/settings.py` に一元管理する
- コメントは日本語で、最低限必要なものだけ簡潔に書く
- モジュールなど小さなまとまりごとに `vla3dsg/scripts/test_<対象>.py` でテストしてから評価パイプラインに組み込む
- 評価結果は条件（チェックポイント、スイート、タスクID、シード、プロンプト条件）とともに `vla3dsg/results/` に保存し、再現できるようにする
- LIBERO評価では `policy.per_episode_seed=true` と `policy.eval_seed` を使い、シードを固定する
- LeRobot の import は絶対 import（`from lerobot.module import X`）を使う

LeRobot 本体（`src/lerobot/`）を変更する場合は、公式のルールに従う:

- 変更したコードには型アノテーションを付ける。mypy は `pre-commit run mypy --all-files` で実行する（`lerobot.rl`、同梱の `molmoact2_hf_model`、生成された `*_pb2` は対象外）
- import はトップレベルで行う。同じモジュール内の兄弟ファイル間は相対 import、モジュールをまたぐ場合は絶対 import
- オプション依存は、モジュール先頭で `TYPE_CHECKING or _foo_available` によりガードし、使用時に `require_package(...)` で確認する。`utils/import_utils.py` の `_foo_available` フラグを再利用し、`is_package_available` は呼ばない

共通:

- 不明点や方針に関わる判断は、勝手に決めずに確認を求めること
- 作業の区切りごとに `vla3dsg/progress_management.md` のチェックボックスと作業ログを更新すること

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
