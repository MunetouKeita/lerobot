# ローカル PC（RTX 5090）

研究室の自分の PC。評価・データ作り・短い学習・可視化に使う。3 つの環境の使い分けは `CLAUDE.md` の「実行環境」。

## 構成

| 項目 | 内容 |
|---|---|
| OS | Ubuntu 22.04 |
| CPU・メモリ | 20 コア、62GB |
| GPU | NVIDIA GeForce RTX 5090 × 1（VRAM 32GB、Blackwell / sm_120）。ドライバ 580.178.04 |
| CUDA | nvcc 12.8。PyTorch は `uv.lock` で固定される CUDA 12.8 ビルド（torch 2.11.0+cu128） |
| Python | 3.12（uv の仮想環境 `.venv/`、リポジトリの直下） |
| リポジトリ | `/home/common/github/lerobot`（`vla3dsg` ブランチ） |
| データ・チェックポイント | `~/.cache/huggingface/hub`（`allenai/MolmoAct2-LIBERO` など）、学習の出力は `outputs/train/`（1 チェックポイント 18GB） |
| ディスク | 853GB（2026-11-10 時点で空き約 400GB）。学習の出力がほとんどを占めるため、評価が済んだチェックポイントは消す |

## ルール

- この PC の GPU は ollama も使っている。ollama は止めない（メモリが足りなければ、空くまで待つか、サーバで評価する）
- PC 内の他のプロジェクトに影響する作業（共有の設定・ディレクトリの変更、sudo など）は、事前にユーザーの許可を得る
- 研究テーマ2（習慣考慮型3DSG）用の Python 3.10 の環境とは混ぜない

## セットアップ

- `torch.cuda.get_arch_list()` に `sm_120` が含まれることを確かめる（`no kernel image is available for execution on the device` が出たら古いホイールが入っている）
- 動画のデコード（TorchCodec）とテストに、システムの ffmpeg を使う
- LIBERO の設定 `~/.libero/config.yaml` は既定値で作成済み（初回 import 時の対話を避けるため）。アセットは初回起動時に `~/.cache/libero/assets` へ自動ダウンロードされる
- ヘッドレス描画と再現性のため、実行前に次を設定する（`settings.apply_runtime_env()` でも設定される）

```bash
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```

## 性能の目安

| 処理 | 目安 |
|---|---|
| 推論 | 189ms／回、GPU メモリ約 26GB（`results/baseline/inference/`） |
| 評価 | 20 エピソード × 3 タスク（最大 400 ステップ）で約 20 分 |
| 学習 | MolmoAct2（VLM は LoRA、バッチ 8 × 勾配累積 4）で 1.6 秒／ステップ、12,000 ステップで約 5.3 時間、GPU メモリ 25.5〜29.7GB。学習中はほかの評価ができない |
