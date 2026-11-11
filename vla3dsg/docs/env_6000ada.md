# 学習サーバ 6000ada（RTX 6000 Ada × 4）

研究室の共有サーバ。GPU を何枚も使う評価（条件 × タスクを並べて回す）と長い学習に使う。3 つの環境の使い分けは `CLAUDE.md` の「実行環境」。

## 構成

| 項目 | 内容 |
|---|---|
| 接続 | `ssh munetou-6000ada`（鍵認証、パスワード不要）。ホスト名 `ws-rtx6000adax4-01`、ユーザー `munetou` |
| GPU | NVIDIA RTX 6000 Ada × 4（VRAM 48GB、Ada / sm_89）。ドライバ 550.163.01（CUDA 12.4）。`uv.lock` の torch 2.11.0+cu128 がそのまま動く |
| CPU・メモリ・ディスク | 32 コア、125GB。`/home` は 2.6TB（共有、2026-11-10 時点で空き約 900GB） |
| リポジトリ | `~/lerobot`（`vla3dsg` ブランチを clone。GitHub に ssh で接続できる） |
| 仮想環境 | `~/environments/lerobot-vla3dsg`（コンテナは使わず、ホストに直接作っている） |
| データ・チェックポイント | `~/.cache/huggingface/hub`（`lerobot/libero`、`allenai/MolmoAct2-LIBERO` など） |

## ルール

- 共有サーバのため、他のユーザーに影響する作業（他のユーザーのプロセスを止める、共有の設定・ディレクトリを変えるなど）は、事前にユーザーの許可を得る
- GPU は基本的に 2 枚まで使う。使う前に `nvidia-smi` で空き（メモリ・使用率）を確かめ、`CUDA_VISIBLE_DEVICES` で指定する。4 枚使うのは、ユーザーが許可した実験だけ（5 節の段階 1 は許可済み、2026-11-10）
- sudo 権限はあるが、sudo を実行するときは必ず事前にユーザーの許可を得る
- ホームディレクトリ（`/home/munetou`）の中は自由に変更してよい

## 使い方

uv のコマンドの前に、次を設定する（venv をリポジトリの外に置いているため）。

```bash
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```

- 描画: システムの EGL の設定（`/usr/share/glvnd/egl_vendor.d/`）に NVIDIA の分がなく、そのままでは LIBERO の画面なし描画が失敗する。ホームに `~/.config/egl/10_nvidia.json` を作ってあり、上の `__EGL_VENDOR_LIBRARY_FILENAMES` で使う（sudo 不要）。LIBERO の設定 `~/.libero/config.yaml` は既定値で作成済み
- コードの同期: 手元で push したコミットに `git fetch` と `git reset --hard origin/vla3dsg` で合わせ、コミットしていない変更は `rsync` で送る。サーバで作業途中の変更がある場合は、先に `~/backup/` へ退避する（2026-10-21 の変更は `~/backup/` と `git stash` にある）
- 長い処理は `setsid nohup <スクリプト> > run.log 2>&1 < /dev/null &` で起動し、各工程を `status.log` に書く（ssh が切れても続く。例: `results/zeroshot/spatial/run.sh`）
- 結果（`vla3dsg/results/<名前>/`）は、終わったら `rsync` で手元へ持ってくる

## 性能の目安

| 処理 | 目安 |
|---|---|
| 評価 | 空いていれば 1 枚あたり約 14 ステップ/秒。20 エピソード（最大 280 ステップ）で約 5 分半。GPU メモリ約 26GB のため、1 枚に 1 つの評価。学習したモデルの評価（5-2）は 1 本 20〜25 分かかった（時間切れが多く、エピソードが長いため） |
| 学習 | 4 枚で `accelerate launch --multi_gpu --num_processes=4`（1 枚あたりバッチ 8、合計 32、勾配累積なし）にすると 3.4 秒／更新、GPU メモリ 1 枚あたり約 31GB（2026-11-10 計測）。6000pro の 1 枚（6.7 秒）の約 2 倍の速さ。更新 3,000 回で約 2.8 時間（5-2 では 3.2 時間と 5.3 時間。他のユーザーの使用状況で変わる） |
| 混んでいるとき | 他のユーザーが使用率 100% 近くで使っていることが多く、1 枚あたり 5090 の 1/4 程度の速さしか出ないことがある |
