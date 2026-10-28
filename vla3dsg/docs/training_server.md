# 学習サーバ（RTX 6000 Ada）の使い方

追加学習はこのPCでも回るが（`results/training/train_check/`）、長い学習は学習サーバで行い、このPCは評価とデータ作りに使う。共有サーバのため、使うときの規則（GPU は 2 枚まで・`nvidia-smi` で空きを確かめる・sudo は事前に許可を得る）は `CLAUDE.md` の「学習サーバ」に従う（`CLAUDE.md` から移した）。

| 項目 | 内容 |
|---|---|
| 接続 | `ssh munetou-6000ada`（鍵認証、パスワード不要）。ホスト名 `ws-rtx6000adax4-01`、ユーザー `munetou` |
| GPU | NVIDIA RTX 6000 Ada × 4（VRAM 48GB、Ada / sm_89）。ドライバ 550.163.01（CUDA 12.4）。`uv.lock` の torch 2.11.0+cu128 がそのまま動く |
| リポジトリ | `~/lerobot`（`vla3dsg` ブランチを clone。GitHub に ssh で接続できる） |
| 仮想環境 | `~/environments/lerobot-vla3dsg`。venv は `~/environments/` に置くため、uv のコマンドの前に `export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg` を設定する |
| データ・チェックポイント | `~/.cache/huggingface/hub`（`lerobot/libero`、`allenai/MolmoAct2-LIBERO` など） |
| 描画（評価） | システムの EGL の設定（`/usr/share/glvnd/egl_vendor.d/`）に NVIDIA の分がなく、そのままでは LIBERO の画面なし描画が失敗する。ホームの `~/.config/egl/10_nvidia.json` を作ってあり、評価の前に `export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json` を設定する（sudo 不要）。LIBERO の設定 `~/.libero/config.yaml` は既定値で作成済み |

- ホームディレクトリ（`/home/munetou`）の中は自由に変更してよい
- GPU は他のユーザーが使用率 100% 近くで使っていることが多く、1 枚あたり 5090 の 1/4 程度の速さしか出ないことがある
