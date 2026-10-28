# LeRobot のアーキテクチャ（`src/lerobot/`）と、本体を変更する場合のルール

本研究では LeRobot 本体は原則として変更しない。本体のコードを読む・やむを得ず変更するときに参照する（`CLAUDE.md` から移した）。

## `src/lerobot/`

- **`scripts/`**: CLI のエントリーポイント（`lerobot-train`、`lerobot-eval`、`lerobot-record` など）。`pyproject.toml` の `[project.scripts]` で対応付け
- **`configs/`**: draccus で解析される dataclass の設定。`train.py` に最上位の `TrainPipelineConfig`、`policies.py` に基底の `PreTrainedConfig`。`draccus.ChoiceRegistry` と `@register_subclass("name")` で多態性を実現
- **`policies/`**: ポリシーごとのサブディレクトリ。すべて `pretrained.py` の `PreTrainedPolicy`（`nn.Module` + `HubMixin`）を継承。`factory.py` に遅延 import 付きのファクトリ。MolmoAct2 は `molmoact2` にある
- **`processor/`**: データ変換パイプライン。`ProcessorStep` 基底クラスとレジストリ。`DataProcessorPipeline` / `PolicyProcessorPipeline` でステップをつなぐ。タスク指示文へのSG追加の候補箇所
- **`datasets/`**: `LeRobotDataset`（エピソード単位のサンプリング + 動画デコード）と `LeRobotDatasetMetadata`
- **`envs/`**: `configs.py` に基底の `EnvConfig`、`factory.py` にファクトリ。各環境のサブクラスが `gym_kwargs` と `create_envs()` を定義。LIBERO は `libero.py`
- **`robots/`、`motors/`、`cameras/`、`teleoperators/`**: ハードウェア抽象化層（本研究では使わない）
- **`types.py`、`configs/types.py`**: 主要な型エイリアスと特徴量の型定義

## `src/` 以外の主な構成

- **`tests/`**: モジュール別の pytest 一式。フィクスチャは `tests/fixtures/`、モックは `tests/mocks/`
- **`docs/source/`**: 公式ドキュメント（`.mdx`）。`molmoact2.mdx`、`libero.mdx` を特に参照する
- **`examples/`**: 用途別のチュートリアルとスクリプト
- **ルートのファイル**: `pyproject.toml`（依存関係・ビルド・ツール設定の唯一の情報源）、`Makefile`（E2Eテスト）、`uv.lock`

## 本体（`src/lerobot/`）を変更する場合の公式のルール

- 変更したコードには型アノテーションを付ける。mypy は `pre-commit run mypy --all-files` で実行する（`lerobot.rl`、同梱の `molmoact2_hf_model`、生成された `*_pb2` は対象外）
- import はトップレベルで行う。同じモジュール内の兄弟ファイル間は相対 import、モジュールをまたぐ場合は絶対 import
- オプション依存は、モジュール先頭で `TYPE_CHECKING or _foo_available` によりガードし、使用時に `require_package(...)` で確認する。`utils/import_utils.py` の `_foo_available` フラグを再利用し、`is_package_available` は呼ばない
- 本体のテストは `uv run pytest tests -svv --maxfail=10`
- 変更した理由と差分は `progress_management.md` の作業記録に残す
