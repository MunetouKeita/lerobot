# progress_management.md — VLA×3DSG 詳細計画と進捗

研究の概要・環境・リポジトリ構成は、LeRobot のルートにある `CLAUDE.md` を参照。
本ファイルのパスは、特に断りがない限り `vla3dsg/` からの相対パス。
各タスクは完了したらチェックを付け、末尾の作業ログに日付・内容・結果を追記する。

## 全体の流れ

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | LIBERO + MolmoAct2 の環境構築 | 未着手 |
| 1 | 標準LIBEROでのMolmoAct2ベースライン再現 | 未着手 |
| 2 | 隠れた物体のあるカスタムシーンの作成 | 未着手 |
| 3 | Scene Graphのテキスト化とプロンプト追加（ゼロショット評価） | 未着手 |
| 4 | 結果の分析と次の方針決定 | 未着手 |
| 5 | UMI作成・教師データ取得・ファインチューニング | 未着手（Phase 4の結果次第） |

---

## Phase 0: 環境構築

目的: LIBEROでMolmoAct2が1エピソードでも動く状態にする

- [x] uv をインストールする（uv 0.12.23、`~/.local/bin`）
- [x] 本家 LeRobot（`huggingface/lerobot` の main）をフォーク（`MunetouKeita/lerobot`）してクローンし、使用したコミットを記録する（初回 `8c920c42`。2026-10-07 に upstream main `200ee535` へ更新。以降の更新は作業ログに記録）
- [x] 公式の `CLAUDE.md`（`AGENTS.md` へのシンボリックリンク）を本研究用の `CLAUDE.md` に置き換え、`vla3dsg/` ディレクトリと本ファイルを配置する
- [x] `uv sync --locked --extra molmoact2 --extra libero` で Python 3.12 の仮想環境を作る（extra の組み合わせでエラーが出たら報告）（Python 3.12.15、`.python-version` で 3.12 に固定）
- [x] PyTorch が CUDA 12.8 ビルドで、`get_arch_list()` に `sm_120` が含まれることを確認する（torch 2.11.0+cu128、RTX 5090 で行列積も確認）
- [x] システムに ffmpeg が入っており、TorchCodec から使えることを確認する（ffmpeg 4.4.2、torchcodec 0.11.1+cpu で H.264 をデコードできた）
- [x] EGL のヘッドレス描画でLIBEROの環境が起動し、カメラ画像（agentview、手首）が保存できることを確認する（`scripts/test_libero_env.py`、libero_goal task0 で確認）
- [x] `allenai/MolmoAct2-LIBERO-LeRobot` をダウンロードする（10.9GB、bf16 の単一 safetensors。読み込み時に `checkpoint_path` の `allenai/MolmoAct2-LIBERO`（21GB）も自動でダウンロードされる）
- [x] 1タスク・1エピソードで `lerobot-eval` が最後まで走ることを確認する（元の HF チェックポイント `MolmoAct2-LIBERO`、libero_goal task0 で成功。`results/phase0_smoke/`）
- [ ] 推論時のVRAM使用量と1ステップあたりの推論時間を記録する
  - VRAM: float32 でピーク約 26.0GB（デスクトップ表示分を除く）
  - 推論時間: `lerobot-eval` は推論1回あたりの時間を出さないため未計測（126 環境ステップで約 6.5 秒、チャンク長 10）。可視化ツールか計測用スクリプトで測る
- [x] `lerobot-eval` が保存するロールアウト動画（`<output_dir>/videos/<スイート>_<タスクID>/eval_episode_*.mp4`）を確認する（引き出しが開くことを確認。80fps で保存されるため実時間の4倍速で再生される）

完了条件: エラーなく1エピソードが終了し、ロールアウト動画を保存できる

## Phase 1: ベースライン再現

目的: 環境構築が正しいことを公式の数値との比較で確認し、以降の比較の基準にする

- [ ] LeRobot の MolmoAct2 ドキュメントの評価コマンドに合わせて設定する
  - `--policy.inference_action_mode=continuous`、`--policy.per_episode_seed=true`、`--policy.eval_seed=1000`、`--seed=1000`
  - `--env.camera_name_mapping='{"agentview_image":"image","robot0_eye_in_hand_image":"wrist_image"}'`
- [ ] まず `libero_goal` など1スイートを少数エピソードで評価する
- [ ] 4スイート（`libero_spatial`、`libero_object`、`libero_goal`、`libero_10`）を評価し、公式の報告値と比較する
- [ ] LeRobot 形式のチェックポイント（`MolmoAct2-LIBERO-LeRobot`）と元のHFチェックポイント（`MolmoAct2-LIBERO` + `--policy.norm_tag=libero`）で差がないか確認する
- [ ] 評価結果（成功率、条件、所要時間）を `results/baseline/` に保存する
- [ ] 論文値と大きくずれる場合は、Ai2 のフォーク（v0.5.1固定）で同じ評価を行って原因を切り分ける
- [ ] `num_steps_wait`（reset 後に物体を落ち着かせる no-op ステップ数）を 50 にして評価する方法を決める
  - MolmoAct2 のドキュメントでは、LIBERO の報告値はすべて `num_steps_wait=50` で測ったとされている（10 では成功率が下がりうる）
  - 現在の LeRobot では `LiberoEnv`（`src/lerobot/envs/libero.py`）の引数に既定値 10 があるだけで、`--env.*` の設定からは変えられない

完了条件: 公式の報告値に近い成功率が再現できる（大きくずれる場合は原因を調べてから先へ進む）

## Phase 2: 隠れた物体のあるカスタムシーン作成

目的: オクルージョンにより、画像だけでは対象物体が見えない（見えにくい）評価用タスクを作る

- [ ] LIBEROのタスク定義（BDDLファイル）とシーン生成の仕組みを調べ、`docs/` にまとめる
- [ ] LeRobot の LIBERO 環境（`src/lerobot/envs/libero.py`）がタスクを読み込む流れを調べ、`docs/` にまとめる
  - `benchmark.get_benchmark_dict()` からスイートを取得し、BDDLファイルと初期状態ファイルを LIBERO のパスから読み込む実装になっている
  - カスタムスイートを LIBERO 側にベンチマークとして登録し、`--env.task` で指定できるようにする方法を決める
- [ ] 既存タスクを1つ複製し、物体配置だけを変えたタスクがカスタムスイートとして `lerobot-eval` から動くことを確認する
- [ ] 隠れた物体のパターンを設計する（例: 箱の裏、棚の中、他の物体の陰）
  - カメラ（エージェント視点・手首視点）から対象物体が見えない／一部だけ見える状態を作る
- [ ] 初期状態分布（配置のばらつき）を指定し、初期状態ファイルを生成する
- [ ] 成功条件とタスク指示文を定義する
- [ ] 各タスクの初期画像を保存し、本当に隠れているかを目視で確認する
- [ ] 隠れていない版（対照条件）も同じ物体構成で用意する

完了条件: 隠れあり／隠れなしのペアになったカスタムタスク群が評価スクリプトから実行できる

## Phase 3: Scene Graph のプロンプト追加（ゼロショット評価）

目的: 追加学習なしで、SGをプロンプトに入れるだけで成功率が上がるかを確認する

### 3-1. Scene Graph の生成

- [ ] まずはシミュレータの内部状態（MuJoCoの物体位置・姿勢）から正解のSGを生成する
  - 知覚（検出・認識）の誤差を切り離し、「SGが正しく与えられた場合の上限」を先に測るため
- [ ] ノード: 物体名、位置（必要なら）、属性
- [ ] エッジ: 空間関係（on、in、behind、left_of など）。視点依存の関係（behind など）の定義を決める
- [ ] SG生成を `scripts/test_scene_graph.py` で単体テストする

### 3-2. テキスト化とプロンプト設計

- [ ] SGのテキスト化形式を複数用意する（例: 自然文、三つ組の列挙、対象物体に関係する部分だけ抜き出した形式）
- [ ] MolmoAct2のプロンプト構築処理（`normalize_language` で何が変わるか、最大系列長）を確認する
- [ ] タスク指示文をSG付きに差し替える場所を決める（環境側のタスク文を書き換えるか、`ProcessorStep` を追加してポリシーの前処理で付け足すか）。LeRobot 本体は直接書き換えず、`vla3dsg/` 側で実現する
- [ ] プロンプト形式は `config/settings.py` で切り替えられるようにする

### 3-3. 評価

比較条件:

| 条件 | 内容 |
|---|---|
| A | 元のタスク指示のみ |
| B | タスク指示 + SGテキスト |
| C | タスク指示 + SGと同程度の長さの無関係なテキスト（プロンプトが長くなる影響を切り分けるため） |

- [ ] 標準LIBEROのタスクで条件A〜Cを比較し、SGを入れても性能が落ちないかを確認する
- [ ] カスタムシーン（隠れあり／隠れなし）で条件A〜Cを比較する
- [ ] 失敗エピソードの動画を保存し、失敗の種類（探さない、違う物体を掴む、掴み損ねる など）を分類する

完了条件: 条件ごとの成功率と失敗分類の表ができている

## Phase 4: 分析と方針決定

- [ ] Phase 3 の結果をまとめ、SGがゼロショットで効くかを判断する
- [ ] 効かない場合の原因を切り分ける（LIBEROの指示文に過学習していてプロンプトの変化を無視する、そもそも見えない物体への動作が学習されていない など）
- [ ] Phase 5 に進むか、プロンプト設計・シーン設計の見直しを行うかを決める（ユーザーと相談）

## Phase 5: UMI作成・教師データ取得・ファインチューニング

Phase 4 の結果を受けて詳細化する。現時点の予定のみ記載。

- [ ] UMI型ハンドヘルド教示デバイスを3Dプリントで作成する
- [ ] 隠れた物体を扱うタスクの教師データを取得する
- [ ] SGテキスト付きのデータでMolmoAct2をファインチューニングする
- [ ] Phase 3 と同じ条件で評価し、ゼロショットとの差を確認する

---

## 共通ツール: ロールアウトの可視化

目的: LIBEROでの動作の様子を、動画またはストリーミングで確認できるようにする（失敗分類や、SGの有無による挙動の違いの確認に使う）

LeRobot 本体の現状（2026-10-06 時点、`8c920c42`）:

- `lerobot-eval` は1タスクあたり最大10エピソードをMP4で `<output_dir>/videos/` に保存する（本数はコード内で固定。`--eval.recording=true` のときは保存しない）
- 動画の中身は `LiberoEnv.render()` の出力で、agentview カメラの1視点のみ（観測と同じ解像度、既定 360x360）。手首カメラ、指示文、成功判定などの表示はない
- 評価中にリアルタイムで見るストリーミング機能はない（Rerun / Foxglove による可視化は `lerobot-record`・`lerobot-teleoperate`・`lerobot-dataset-viz` 向けで、`lerobot-eval` には組み込まれていない）
- `--eval.recording=true` でロールアウトを LeRobot データセットとして保存すれば、両カメラを `lerobot-dataset-viz`（Rerun）で後から見られる

方針: 不足分は `vla3dsg/` 側で作る（LeRobot 本体は変更しない）

- [ ] 動画: agentview と手首カメラを横に並べ、指示文（SG付きプロンプトを含む）、ステップ数、成功・失敗を重ねて表示した MP4 を保存する
- [ ] 保存する本数・対象（全エピソード／失敗のみ など）を `config/settings.py` で指定できるようにする
- [ ] ストリーミング: 評価中の映像を Rerun ビューアでリアルタイムに確認できるようにする（このPCのローカル画面で見る。両カメラ、指示文、行動の値をステップごとに記録し、`.rrd` に保存して後から見直せるようにする）
- [ ] 実装の場所（`lerobot-eval` を呼ぶラッパーか、独自の評価ループか）を、Phase 1 で `lerobot-eval` の処理の流れを調べたうえで決める

## 未決事項

- `MolmoAct2-LIBERO-LeRobot` の `config.json` が現在の LeRobot と非互換な件の対処（作業ログ 2026-10-07 参照）。Phase 0 は元の HF チェックポイントで実施。Phase 1 の比較時に、項目名を直したローカルコピーで試すか決める
- `num_steps_wait=50` の指定方法（`vla3dsg/` 側で LIBERO の環境設定を継承したクラスを登録するか、`src/lerobot/` を最小限変更するか）
- 隠れた物体の具体的なパターンと、どの程度隠すか
- SGのテキスト化形式（どこまでの情報を入れるか）
- 視点依存の空間関係（behind など）をどの座標系で定義するか
- Phase 5 のファインチューニングの対象（シミュレーション上の Franka Panda か、実機か）と、UMIで取得したデータをどの形で使うか
- 将来的にSGをシミュレータの正解ではなく知覚から構築する場合の手法

## 作業ログ

| 日付 | 内容 | 結果・メモ |
|---|---|---|
| 2026-10-06 | 計画作成 | — |
| 2026-10-06 | 評価基盤を本家 LeRobot（のフォーク）、仮想環境を uv に変更 | Ai2 フォークは論文値の再現用として残す |
| 2026-10-06 | LeRobot 公式の CLAUDE.md と統合 | 研究コードは `vla3dsg/` に置く構成に変更 |
| 2026-10-06 | CLAUDE.md の記述をリポジトリの実態に合わせて修正 | フォーク（`MunetouKeita/lerobot`）である旨と、統合元が `AGENTS.md` である旨を明記 |
| 2026-10-06 | 使用コミットを記録、`upstream` remote を追加 | ベースコミット `8c920c42`（upstream main、2026-10-03）。`upstream` = `https://github.com/huggingface/lerobot.git` |
| 2026-10-06 | uv をインストール | 公式インストーラで uv 0.12.23 を `~/.local/bin` に導入。作業は `vla3dsg` ブランチで行う（`main` は upstream 追従用） |
| 2026-10-06 | `uv sync --locked --extra molmoact2 --extra libero` | 初回は `.python-version` がなくシステムの Python 3.13 が選ばれたため、`uv python pin 3.12` で固定して作り直した（3.12.15）。torch 2.11.0+cu128、`sm_120` あり、lerobot 0.6.2・libero の import を確認。extra の組み合わせでエラーなし |
| 2026-10-06 | ffmpeg を apt でインストールし TorchCodec を確認 | ffmpeg 4.4.2（Ubuntu 22.04 標準）。TorchCodec 0.11.1（CPU 版）で H.264 のテスト動画をデコードできた。システムの ffmpeg には libsvtav1 がないが、eval のロールアウト動画は PyAV（同梱 FFmpeg、libsvtav1 あり）の libx264 で書き出すため影響なし |
| 2026-10-06 | `config/settings.py` と `scripts/test_libero_env.py` を作成し、LIBERO の起動を確認 | 初回 import 時の対話プロンプトに N で答え `~/.libero/config.yaml` を既定値で作成。アセットは初回起動時に HF Hub から `~/.cache/libero/assets` に自動ダウンロード（約70秒）。libero_goal task0 で reset 2.1秒（2回目）、no-op step 6.5ms、360x360 の agentview・手首画像を保存し目視で確認。出力先 `outputs/` は git 管理外 |
| 2026-10-06 | ロールアウト可視化機能の有無を調査 | `lerobot-eval` は agentview のみの MP4 を1タスク最大10本保存。手首カメラ・指示文の表示やストリーミングはないため、`vla3dsg/` 側で作る方針を「共通ツール」節に追記 |
| 2026-10-06 | ストリーミングの視聴環境を確認 | 評価・確認ともこのPCで行う（リモート不要）。方式は Rerun（要 `viz` extra）か OpenCV ウィンドウかで未決 |
| 2026-10-06 | ストリーミング方式を Rerun に決定し、`viz` extra を追加 | rerun-sdk 0.33.1・foxglove-sdk 0.25.3 を導入（他パッケージの削除なし）。以降の `uv sync` は `--extra molmoact2 --extra libero --extra viz` で行う |
| 2026-10-07 | `num_steps_wait` の設定可否を調査 | MolmoAct2 の報告値は `num_steps_wait=50` 前提だが、LeRobot の `--env.*` からは変えられず既定値 10 のまま。Phase 0 の動作確認は既定値で行い、Phase 1 までに指定方法を決める |
| 2026-10-07 | チェックポイントをダウンロードし `lerobot-eval` を試行 | `MolmoAct2-LIBERO-LeRobot`（10.9GB）と、読み込み時に自動取得される `MolmoAct2-LIBERO`（21GB）を `~/.cache/huggingface/hub` に保存。`lerobot-eval` は `The fields enable_lora_vlm, enable_lora_action_expert, train_action_expert_only, model_dtype are not valid for MolmoAct2Config` で失敗。Hub の config.json が、LeRobot 側の設定項目の変更（c13d79e6 で LoRA 関連を `train_mode_vlm` に統合、ff71cae1 で `model_dtype` を `dtype` に統一）に追従していないため。upstream main（2026-10-07 時点）にも修正なし。config.json の項目名だけ直した一時コピーでは設定と前後処理の読み込みが通ることを確認（推論は未実施） |
| 2026-10-07 | 元の HF チェックポイントで 1 エピソード評価 | `--policy.checkpoint_path=allenai/MolmoAct2-LIBERO --policy.norm_tag=libero --policy.dtype=float32`。libero_goal task0 で成功（126 ステップ）。評価 8.9 秒、コマンド全体 36.6 秒、VRAM ピーク約 26.0GB。結果と条件を `results/phase0_smoke/` に保存 |
| 2026-10-07 | フォークを upstream に同期 | `main`（ローカル・GitHub の `origin`）を `8c920c42` から `200ee535` に早送り（7コミット、DM05・FineART-VLA の追加など。molmoact2・libero・viz の依存関係、MolmoAct2・LIBERO・eval のコードに変更なし）。`vla3dsg` ブランチを新しい `main` にリベース（競合なし）。`uv sync` 後に `test_libero_env.py` と 1 エピソード評価を再実行し、同じく成功（評価 8.5 秒） |
