# 学習サーバ 6000pro（RTX PRO 6000 Blackwell × 4）

研究室の新しい共有サーバ（2026-11-10 から使用）。GPU 1 枚あたり 96GB と大きく、長い学習や大きなバッチの学習、評価に使う。3 つの環境の使い分けは `CLAUDE.md` の「実行環境」。

## 構成

| 項目 | 内容 |
|---|---|
| 接続 | `ssh munetou-6000pro`（研究室 LAN 内、192.168.4.193）。ホスト名 `s232`、一般ユーザー `munetou`（sudo なし） |
| OS | Ubuntu 24.04 |
| GPU | NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition × 4（VRAM 96GB、Blackwell / sm_120）。ドライバ 610.57.04（CUDA 13.3）。`uv.lock` の torch 2.11.0+cu128 がそのまま動く |
| CPU・メモリ・ディスク | 24 コア、251GB。`/` は 1.8TB（2026-11-10 時点で空き 1.4TB） |
| コンテナ | Apptainer 1.5.4。イメージ `~/containers/lerobot-vla3dsg.sif`（定義 `~/containers/lerobot-vla3dsg.def`、Ubuntu 24.04 ＋ 描画・ffmpeg・ビルド用のライブラリ ＋ uv） |
| リポジトリ | `~/lerobot`（`vla3dsg` ブランチを https で clone。公開リポジトリのため取ってくるだけなら認証は不要。GitHub への ssh の鍵は未登録で、サーバからは push しない） |
| 仮想環境 | `~/environments/lerobot-vla3dsg`（Python 3.12 は uv が `~/.local/share/uv/python` に入れたもの）。コンテナの中から使う |
| データ・チェックポイント | `~/.cache/huggingface/hub`（`allenai/MolmoAct2-LIBERO` はローカル PC から LAN でコピーした）。LIBERO の設定 `~/.libero/config.yaml` は 6000ada と同じ内容 |
| NAS | SensingGroupDB が管理者ユーザーでマウントされている（本研究では使っていない） |

## ルール（サーバの運用ルール。必ず守る）

- sudo は管理者ユーザーに限定されている。一般ユーザーを sudo グループに入れる変更は行わない
- 各自のプロジェクトは Apptainer（または Docker）でコンテナ化して使う。CUDA や Python ライブラリはコンテナの中（とホーム）に入れ、システムには入れない
- sudo が必要なシステムへのインストールや新規ユーザーの作成は、管理者に依頼する
- どのサーバ・GPU を誰が使うかは、当面は口頭で調整する。使う前に `nvidia-smi` で空きを確かめ、`CUDA_VISIBLE_DEVICES` で指定する（2026-11-10 時点で 0・1 番は他のユーザーが使用中）
- 破壊的な操作（ユーザーの削除、パーミッションの変更、マウントの変更、ドライバの更新）は、実行前に必ず人間に確認する
- パスワードや認証情報をファイルやログに書き出さない（管理者・KVM スイッチのパスワードは、必要なときに人間に確認する）
- ホームディレクトリ（`/home/munetou`）の中は自由に変更してよい

## 使い方

コマンドは、ラッパー `~/containers/run.sh` を通してコンテナの中で実行する（作業場所は `~/lerobot`、GPU を使う `--nv`、ロケールと描画の環境変数を設定済み）。

```bash
CUDA_VISIBLE_DEVICES=3 ~/containers/run.sh uv run --no-sync python vla3dsg/scripts/run_eval.py --name ... --suite ...
~/containers/run.sh uv sync --locked --extra molmoact2 --extra libero --extra viz   # 依存関係を入れ直すとき
```

- コンテナの中では `UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg`・`MUJOCO_GL=egl` などが設定される（定義ファイルの `%environment`）
- 描画: NVIDIA の EGL の設定（`10_nvidia.json`）をイメージの中に入れてあり、`--nv` でホストから入る `libEGL_nvidia` を使う
- イメージの作り直し: `cd ~/containers && apptainer build --fakeroot lerobot-vla3dsg.sif lerobot-vla3dsg.def`（約 16 分。研究室 LAN からの Ubuntu のパッケージのダウンロードが遅い）。`munetou` には subuid が割り当てられていて、sudo なしで作れる
- コードの同期: 手元で push したコミットを `git pull` で取ってくる。コミットしていない変更は `rsync` で送る
- 長い処理は `setsid nohup ~/containers/run.sh <コマンド> > run.log 2>&1 < /dev/null &` で起動する（ssh が切れても続く）
- Hugging Face からの大きなファイルのダウンロード（Xet）が途中で止まることがあった（2026-11-10）。モデルはローカル PC から `rsync` で送るほうが速い（LAN で約 230MB/s。ローカルの HF キャッシュの大きなファイルは共有の保存場所へのリンクなので、`blobs/` は `--copy-links` を付けて送る）

## 性能の目安

| 処理 | 目安 |
|---|---|
| 評価 | 1 枚あたり約 14〜17 ステップ/秒（6000ada とほぼ同じ。libero_spatial task 0 で 2/2 成功、2026-11-10）。GPU メモリ約 26GB のため、96GB の 1 枚に評価を 3 つまで並べられる見込み（未確認） |
| 学習 | 未計測。メモリに余裕があるので、勾配累積を減らしてバッチを大きくできる見込み |
