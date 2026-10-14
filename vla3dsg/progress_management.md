# progress_management.md — VLA×3DSG 詳細計画と進捗

研究の概要・環境・リポジトリ構成は、LeRobot のルートにある `CLAUDE.md` を参照。
本ファイルのパスは、特に断りがない限り `vla3dsg/` からの相対パス。
各タスクは完了したらチェックを付け、末尾の作業ログに日付・内容・結果を追記する。実施しないと決めた項目は `[-]` とし、理由を書く。
## 現在の状況（2026-10-13 時点）

- Phase 0〜3（実験1・2、学習なし）と Phase 4 の分析が完了。追加学習なしでは SG のテキストは効かない。MolmoAct2 は見えている候補からは指示文で対象を選べるが、見えない物体は探さない（隠れたボウルは物理的には掴める）。次は追加学習ありの計画を決める
- LeRobot: upstream main `200ee535` をベースにした `vla3dsg` ブランチ（LeRobot 本体の変更なし）
- 評価条件: 元の HF チェックポイント `allenai/MolmoAct2-LIBERO`（float32）、環境タイプ `libero_vla3dsg`（`num_steps_wait=50`）、シード 1000

| 実験 | 結果 | 場所 |
|---|---|---|
| ベースライン: 4 スイート全 40 タスク × 5 エピソード | 97.0%（194/200）。報告値の平均 97.2%。成功率 0 のタスクなし | `results/baseline/all40_n5/` |
| デモ: 4 スイート × task 0・5 × 20 エピソード | 99.4%（159/160）。デモ動画と失敗エピソードの動画あり | `results/samples/four_suites_t0_t5_n20/` |
| 推論時間・GPU メモリ | チャンク推論 189ms（10 ステップ分）、VRAM ピーク約 26GB | `results/phase0_inference/` |
| 実験1（学習なし）: libero_spatial 10 タスク × 5 エピソード × 6 条件 | A 96% / B1（JSON）90% / B2（三つ組）86% / B3（自然文）82% / C（無関係な文）92% / D（誤った SG）94%。A との差は有意でない（B3 は p = 0.051） | `results/exp1/libero_spatial_n5/` |
| 実験2（学習なし）: キャビネットの裏に隠れたボウル（task 0）と見える対照（task 1）× 20 エピソード × 6 条件 | 全条件で task 0 は 0/20、task 1 は 20/20。task 0 ではキャビネットへ向かわず、見えている方のボウルを皿に置く | `results/exp2/hidden_cabinet_n20/` |
| Phase 4: 指示文の切り分け（L0・L1）と隠れたボウルのスクリプト制御 | libero_spatial L0 88% / L1 76%、libero_goal L1 0%（別タスクの指示に従う）。隠れシーンでは 19/20 で見えている方のボウルを置く。スクリプト制御なら 50/50 | `results/phase4/` |

## 実験の方針（2026-10-13、ユーザーと決定）

SG を VLA に与える方法と環境の組み合わせで、3 つの実験を行う。それぞれ追加学習なし（ゼロショット）とありで比較する。まずは追加学習なしで色々な条件を比較する。

| 実験 | 環境 | SG の与え方 | 追加学習なし | 追加学習あり |
|---|---|---|---|---|
| 1 | 標準 LIBERO（変更なし） | SG のような関係性を JSON・テキストにして指示文に加える | 実施（最初に行う） | 実施 |
| 2 | 隠れた物体のあるカスタムシーン | SG をテキストで指示文に加える | 実施 | 実施 |
| 3 | 1・2 と同じ | テキストではなく、SG エンコーダーを追加して埋め込みとして入力する | 意味をなさない（下記） | 実施 |

- 実験 3 の追加学習なし: 新しく足すエンコーダー（または既存のグラフエンコーダーを VLA の埋め込み空間へつなぐ変換層）は学習しないと重みがランダムで、VLA にはノイズが加わるだけになる。そのため実験 3 は追加学習ありでのみ比較する
- SG は、まずシミュレータの内部状態（物体の位置・接触）から正解の関係を作る。知覚の誤差を切り離し、「SG が正しく与えられた場合の上限」を先に測るため
- 評価結果は成功率に加えて、動画で確認できるように保存する（`run_eval.py --annotated-video`。各タスク先頭 10 本＋失敗エピソード）

## 全体の流れ

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | LIBERO + MolmoAct2 の環境構築 | 完了 |
| 1 | 標準LIBEROでのMolmoAct2ベースライン再現 | 完了 |
| 2 | 実験1（学習なし）: 標準 LIBERO で SG をテキストとして指示文に追加 | 完了 |
| 3 | 実験2（学習なし）: 隠れた物体のあるカスタムシーンで SG をテキストとして追加 | 完了 |
| 4 | 追加学習なしの結果の分析と、追加学習ありの計画 | 完了 |
| 5 | 追加学習あり: 実験 1・2 のファインチューニングと、実験 3（SG エンコーダー） | 作業中（学習が回ることを確認済み） |
| 6 | UMI 作成・実機の教師データ取得 | 未着手（Phase 4 の結果次第） |

---

## Phase 0: 環境構築（完了）

目的: LIBEROでMolmoAct2が1エピソードでも動く状態にする

- [x] uv をインストールする（uv 0.12.23、`~/.local/bin`）
- [x] 本家 LeRobot をフォーク（`MunetouKeita/lerobot`）してクローンし、使用したコミットを記録する（現在のベースは `200ee535`。更新は作業ログに記録）
- [x] 公式の `CLAUDE.md`（`AGENTS.md` へのシンボリックリンク）を本研究用に置き換え、`vla3dsg/` と本ファイルを配置する
- [x] Python 3.12 の仮想環境を作る（3.12.15。`uv python pin 3.12` で固定）
- [x] PyTorch が CUDA 12.8 ビルドで `sm_120` を含むことを確認する（torch 2.11.0+cu128）
- [x] ffmpeg を入れ、TorchCodec から使えることを確認する（ffmpeg 4.4.2、torchcodec 0.11.1）
- [x] EGL のヘッドレス描画で LIBERO が起動し、カメラ画像を保存できることを確認する（`tests/test_envs.py`）
- [x] チェックポイントをダウンロードする（`allenai/MolmoAct2-LIBERO`、21GB）
- [x] 1タスク・1エピソードで `lerobot-eval` が最後まで走り、ロールアウト動画を保存できることを確認する
- [x] 推論時のVRAM使用量と推論時間を記録する（`scripts/measure_inference.py`、`results/phase0_inference/`）

## Phase 1: ベースライン再現（完了）

目的: 環境構築が正しいことを公式の数値との比較で確認し、以降の比較の基準にする

- [x] LeRobot の MolmoAct2 ドキュメントの評価コマンドに合わせて設定する（`config/settings.py` の `molmoact2_eval_args`、評価は `scripts/run_eval.py`）
- [x] `num_steps_wait` を報告値と同じ 50 にする（環境タイプ `libero_vla3dsg`、`envs/libero_vla3dsg.py`）
- [x] 4スイートを評価し、公式の報告値と比較する（全 40 タスク × 5 エピソードで 97.0%、報告値の平均 97.2%。`results/baseline/all40_n5/`）
- [-] 報告値と同じ規模（各スイート 500 エピソード）で評価する（実施しない。下の判断を参照）
- [-] LeRobot 形式のチェックポイント（`MolmoAct2-LIBERO-LeRobot`）と比較する（実施しない。下の判断を参照）
- [-] 論文値と大きくずれる場合に Ai2 のフォークで切り分ける（大きなずれがないため不要）

判断（2026-10-07、ユーザーと合意）:

- 報告値の再現は達成したとみなし、Phase 1 を完了とする。根拠は、全 40 タスク × 5 エピソードで 97.0%（報告値の平均 97.2%）、4 スイート × 2 タスク × 20 エピソードで 99.4%。シード固定で同じエピソードが同じように失敗することも確認した
- 500 エピソード規模の評価は行わない。比較の基準（条件 A: 元の指示のみ）は、Phase 3 で実際に比較するタスクについて同じ条件で取り直す
- チェックポイントは元の HF チェックポイント `allenai/MolmoAct2-LIBERO` に統一する
## Phase 2: 実験1（学習なし）— 標準 LIBERO で SG をテキストとして追加

目的: 環境は変えず、SG のような関係性を指示文に加えるだけで、MolmoAct2 の挙動・成功率が変わるかを確かめる

条件（2026-10-13 決定）: `libero_spatial` の 10 タスク × 各 5 エピソード × 6 条件（計 300 エピソード）

| 条件 | プロンプト |
|---|---|
| A | 元の指示文のみ |
| B1 | 指示文 + SG（JSON） |
| B2 | 指示文 + SG（三つ組の列挙） |
| B3 | 指示文 + SG（自然文） |
| C | 指示文 + SG と同程度の長さの無関係な文（プロンプトが長くなる影響を切り分ける） |
| D | 指示文 + 関係をでたらめに入れ替えた SG（内容を使っているかを確かめる） |

- libero_spatial を選んだ理由: 同じ黒いボウルが 2 つあり、「皿とラメキンの間のボウル」のように位置関係で対象を特定するため、関係の情報が意味を持ちやすい

実装上の制約（調査済み）:

- MolmoAct2 は指示文を `The task is to {指示文}. The setup is ...` に埋め込む（`processor_molmoact2.py` の `_build_robot_text`）
- 前処理の正規化（`normalize_language`）は、小文字化・文の区切りを `; ` に置換・末尾の括弧や引用符の削除を行うため、JSON が壊れる。全条件で `--policy.normalize_language=false` とし、元の指示文だけを同じ関数（`_normalize_question_text`）で正規化してから SG をつなぐ。条件 A ではモデルへの入力がこれまでと同一になる
- 指示文の長さは約 32 トークンしか見込まれておらず、超えるとエラーになる。全条件で `--policy.max_sequence_length` を広げる

作業:

- [x] シミュレータの状態から SG を作る（`scene_graph/builder.py`）。ノード: 物体（読みやすい名前は `config/object_names.py`、同種は番号付き）。エッジ: on / in（LIBERO の成功判定と同じ述語。引き出し・棚の上面・コンロ）、agentview から見た前後左右（各物体の近い 2 物体）
- [x] SG のテキスト化（JSON・三つ組・自然文）、トークン数を合わせた無関係な文、物体名を入れ替えた SG を作る（`scene_graph/textify.py`）
- [x] エピソードの開始時に SG を作って指示文に加える処理を、`run_eval.py --prompt-condition` で切り替えられるようにする（`prompting/prompt_condition.py`）。実際に使ったプロンプトを `prompts.jsonl` に保存する
- [x] `tests/test_scene_graph.py` で単体テストする（libero_spatial の全 10 タスクで SG を画像と照らして目視確認。コンロの上・引き出しの中も正しく出る）
- [x] SG 付きの文が MolmoAct2 のプロンプト（`The task is to ... scene information: ...`）に入ることを確認する
- [x] 条件 A が、正規化を切り替えてもベースライン（`all40_n5` の libero_spatial）と同じ結果になることを確認する（全 50 エピソードの成否が一致）
- [x] 6 条件を評価し、成功率と動画で比較する（`results/exp1/libero_spatial_n5/README.md`、表は `comparison.md`）

結果（2026-10-13）:

- 成功率: A 96% / B1 90% / B2 86% / B3 82% / C 92% / D 94%（各 50 エピソード）。A との差は有意でない（B3 は p = 0.051）
- 無関係な文（C）や誤った SG（D）でも B1 と同程度で、MolmoAct2（追加学習なし）は SG の内容を行動に活かしていない。プロンプトが長くなる・形が変わること自体で少し乱れる
- 失敗は、正しい対象の近くまで行って止まる・置き終わらない形で、違うボウルを掴む失敗は見られなかった
- 標準タスクは画像だけで対象を特定できるため、SG が助けになる余地が小さい。効果を見るには実験2（隠れた物体）が必要

完了条件: 条件ごとの成功率の表と、条件ごとの動画（成功・失敗の様子）がそろっている

## Phase 3: 実験2（学習なし）— 隠れた物体のあるカスタムシーンで SG をテキストとして追加

目的: オクルージョンにより画像だけでは対象物体が見えない（見えにくい）シーンで、SG のテキストが助けになるかを確かめる

- [x] LIBEROのタスク定義（BDDLファイル）とシーン生成の仕組みを調べ、`docs/` にまとめる（`docs/libero_task_definition.md`）
- [x] LeRobot の LIBERO 環境（`src/lerobot/envs/libero.py`）がタスクを読み込む流れを調べ、`docs/` にまとめる（`docs/lerobot_libero_loading.md`）
  - カスタムスイートは、`Benchmark` を継承したクラスの `Task.problem_folder` に絶対パスを指定し、`register_benchmark` で登録すれば `--env.task` で指定できる（scratch で確認済み）。登録は `vla3dsg/envs/` のプラグイン読み込み時に行う
- [x] 既存タスクを1つ複製し、物体配置だけを変えたタスクがカスタムスイートとして評価スクリプトから動くことを確認する
  - `custom_tasks/<スイート>/tasks.json` のあるフォルダを、プラグイン読み込み時にスイートとして登録する（`envs/custom_suites.py`）。最大ステップ数は `tasks.json` の `max_steps` を `episode_length` に使う（`envs/libero_vla3dsg.py`）
  - `tests/test_envs.py` で、登録・最大ステップ数・指示文・初期状態・SG を確認
- [x] 隠れた物体のパターンを設計する（2026-10-13、ユーザーと決定: ボウル 2 つ・場所を指示文で指定・まずキャビネットの裏のみ）
  - libero_spatial task 0 を元に、対象のボウルだけをキャビネットの裏に置く（`vla3dsg_hidden` task 0）
- [x] 初期状態分布（配置のばらつき）を指定し、初期状態ファイルを生成する（`scripts/make_custom_task.py`。BDDL の配置範囲を書き換え、reset と待機で落ち着いた配置 50 件を `.pruned_init` に保存。押し出し・転倒した配置は除く）
- [x] 成功条件とタスク指示文を定義する（成功条件は元と同じ。指示文は "pick up the black bowl behind the wooden cabinet and place it on the plate"）
- [x] 各タスクの初期画像を保存し、本当に隠れているかを目視で確認する（`custom_tasks/vla3dsg_hidden/previews/`。光線を飛ばして見える割合も測り、agentview から 50 件すべてで 0）
  - セグメンテーション描画は、この環境（numpy 2、EGL）では robosuite・`mujoco.Renderer` とも動かないため、`mujoco.mj_ray` で判定する
- [x] 隠れていない版（対照条件）も同じ物体構成で用意する（task 1: "next to the wooden cabinet"。キャビネットの裏で見える位置は agentview の画角の外になるため、横に置いた。指示文と位置も違うため厳密な対照ではない）
- [x] 隠れあり／隠れなしのシーンで、実験1 と同じ条件（A〜D）を比較する（`results/exp2/hidden_cabinet_n20/README.md`）

結果（2026-10-13）:

- 隠れあり（task 0）は全条件で 0/20、隠れなし（task 1）は全条件で 20/20。SG の有無・形式による差はない
- task 0 では、どの条件でもキャビネットへ向かわず、見えている方のボウルを皿に置く（または近くの物体を触って時間切れ）。指示文の場所の指定も SG も使っていない
- キャビネットの裏のボウルが物理的に掴めるかは未確認（追加学習のデータを作る前に確認する）

完了条件: 隠れあり／隠れなしのカスタムタスク群で、条件ごとの成功率と動画がそろっている

## Phase 4: 追加学習なしの結果の分析と、追加学習ありの計画

- [x] 実験1・2 の結果をまとめ、SG がゼロショットで効くかを判断する（効かない。`results/phase4/README.md`）
- [x] 効かない場合の原因を切り分ける
  - プロンプト条件 L0（場所の指定を除く）・L1（別タスクの指示文）を追加（`settings.PROMPT_CONDITIONS`）。libero_spatial L0 88%・L1 76%、libero_goal L1 0%（別タスクの指示どおりに動く）。見えている候補からは指示文の場所の指定で選べるが、見えない物体は探さない
  - 隠れたボウルはスクリプト制御で 50/50 掴めた（`scripts/generate_demos.py --check`、`results/phase4/scripted_hidden_cabinet/`）。物理的にはできるタスク
- [x] 失敗エピソードから、失敗の種類を分類する（エピソード終了時の SG を `prompts.jsonl` に記録し、`scripts/summarize_results.py` で集計）。実験2 の隠れありでは 20 回中 19 回、見えている方のボウルを皿に置いた。実験1 では違うボウルを掴む失敗はなく、対象の近くで止まる
- [x] 追加学習ありの計画を決める（2026-10-14: 隠れた物体のデモはスクリプト制御で自動生成。案は `results/phase4/README.md` の 5 節。実験 3 のエンコーダーの構成はテキストの結果を見てから）

## Phase 5: 追加学習あり

Phase 4 の結果を受けて詳細化する。

方針（2026-10-14、ユーザーと合意）: 隠れた物体のデモは、スクリプト制御（`demos/scripted.py`）を広げて自動で作る。データを作る前に、学習が回るかを確かめる。回らなければ、学習だけ RTX A6000 のサーバ（ssh）で行う

- [x] 学習が回るかを確かめる（`results/phase5/train_check/README.md`）。`lerobot/libero` から `MolmoAct2-LIBERO` を LoRA・bf16・勾配チェックポイントで学習し、バッチ 8 で GPU メモリのピーク 29.7GB（32.6GB 中）、1.63 秒/マイクロバッチ。勾配累積・チェックポイントの保存・評価での読み込みも確認。このPCで学習できる（SG で指示文が長くなると余裕が減るため、足りなければバッチを下げるか A6000 を使う）
- [x] 隠れた物体のデモを自動生成する（`scripts/generate_demos.py`、`vla3dsg/demos/`）。`vla3dsg_hidden` の task 0・1 で各 50 本（`data/hidden_cabinet_v1/`、記録は `results/demos/hidden_cabinet_v1/`）。形式は `lerobot/libero` と同じで、学習が回ることを確認。ただし動作の分布が公式デモと違う（上限に張り付く割合が 13〜23%、回転なし）
- [ ] 実験1・2: SG テキスト付きの指示文で MolmoAct2 をファインチューニングし、追加学習なしと比較する
- [ ] 実験3: SG エンコーダーを追加して学習し、テキストで与える場合と比較する

## Phase 6: UMI 作成・実機の教師データ取得

- [ ] UMI型ハンドヘルド教示デバイスを3Dプリントで作成する
- [ ] 隠れた物体を扱うタスクの教師データを取得する
- [ ] シミュレーションと同じ条件で評価する

---

## 共通ツール: ロールアウトの可視化

目的: LIBEROでの動作の様子を確認できるようにする（失敗分類や、SGの有無による挙動の違いの確認に使う）。LeRobot 本体は変更せず、`run_eval.py` から `lerobot-eval` の処理を差し替えて実現する

- [x] 動画: agentview と手首カメラを横に並べた MP4 を実時間（20fps）で保存する（`visualization/rollout_video.py`、`run_eval.py --annotated-video`）
- [x] 保存対象: 各タスクの先頭 `VIDEO_SAVE_FIRST_N`（10）本と、それ以降の失敗エピソード（`config/settings.py`）
- [x] デモ動画: 各タスク 1 エピソードを等倍で連結し、下部に「指示：<日本語訳>」「成功率：<成功回数>/<実行数>」を表示する（`scripts/make_demo_video.py`、訳は `config/instructions_ja.py`）。`--keep-failures-only` でデモ動画と失敗動画だけを残す
- [ ] ストリーミング: 評価中の映像を Rerun ビューアでリアルタイムに確認できるようにする（このPCのローカル画面で見る。両カメラ、指示文、行動の値をステップごとに記録し、`.rrd` に保存して後から見直せるようにする）

## LeRobot 側の既知の問題（`200ee535` 時点、本体は変更せず `vla3dsg/` 側で対処）

| 問題 | 影響 | 対処 |
|---|---|---|
| `allenai/MolmoAct2-LIBERO-LeRobot` の `config.json` が現在の `MolmoAct2Config` と非互換（LoRA 関連の項目と `model_dtype` の名前変更に未追従） | LeRobot 形式のチェックポイントを読み込めない | 元の HF チェックポイントを使用 |
| `num_steps_wait` が `--env.*` から指定できない（既定値 10） | MolmoAct2 の報告値（50 で測定）と条件がずれる | 環境タイプ `libero_vla3dsg` で指定 |
| `lerobot-eval` の動画は 1 タスクあたり先頭 10 本に固定 | 11 本目以降の失敗エピソードの動画が残らない | `rollout_video.py` で全エピソードを描画させ、先頭 10 本＋失敗を保存 |
| `lerobot-eval` が動画の書き出し時に終了ステップのフレームを落とす（`stacked_frames[: done_index + 1]`） | 動画の最後に成功の瞬間が映らない | `rollout_video.py` で補う |
| LIBERO の動画が `render_fps=80` で保存される（制御周期は 20Hz） | 実時間の 4 倍速で再生される | `rollout_video.py` で 20fps にする |

いずれも upstream に報告・修正提案できる候補。

## 未決事項

- 隠れた物体の具体的なパターンと、どの程度隠すか（agentview から見て背の高い物体の奥に置くと隠れることは確認済み。`docs/libero_task_definition.md` の 6 節）
- SGのテキスト化形式（どこまでの情報を入れるか）。実験1 では JSON・三つ組・自然文の 3 形式を比較する
- 視点依存の空間関係（behind など）をどの座標系で定義するか
- 追加学習の対象（シミュレーション上の Franka Panda か、実機か）と、UMIで取得したデータをどの形で使うか
- 実験3 の SG エンコーダーの構成（グラフニューラルネット、既存の学習済みエンコーダー＋変換層 など）
- 将来的にSGをシミュレータの正解ではなく知覚から構築する場合の手法

## 作業ログ

| 日付 | 内容 | 結果・メモ |
|---|---|---|
| 2026-10-06 | 計画作成と環境の方針決定 | 評価基盤を本家 LeRobot のフォーク（`MunetouKeita/lerobot`、作業は `vla3dsg` ブランチ）、仮想環境を uv に。LeRobot 公式の `AGENTS.md` を `CLAUDE.md` に統合。Ai2 フォークは論文値の再現用として残す |
| 2026-10-06 | 環境構築 | uv 0.12.23、Python 3.12.15（初回はシステムの 3.13 が選ばれたため `uv python pin 3.12` で固定）、torch 2.11.0+cu128（`sm_120` あり）、ffmpeg 4.4.2。LIBERO の初回 import で `~/.libero/config.yaml` を既定値で作成し、アセットは `~/.cache/libero/assets` に自動ダウンロード |
| 2026-10-06 | 可視化の方針決定 | `lerobot-eval` の動画は agentview のみでストリーミングもないため、`vla3dsg/` 側で作る。評価・確認はこのPCで行い、ストリーミングは Rerun（`viz` extra を追加） |
| 2026-10-07 | チェックポイントの選定 | `MolmoAct2-LIBERO-LeRobot` は `config.json` が非互換で読み込めない（c13d79e6・ff71cae1 の項目名変更に未追従、upstream main に修正なし）。元の HF チェックポイント `MolmoAct2-LIBERO`（`norm_tag=libero`、float32）で libero_goal task 0 の 1 エピソードが成功 |
| 2026-10-07 | フォークを upstream に同期 | `main` を `8c920c42` から `200ee535` に更新し、`vla3dsg` をリベース（競合なし、本研究の依存関係とコードに影響なし） |
| 2026-10-07 | 環境タイプ `libero_vla3dsg` を追加 | `num_steps_wait=50`（報告値と同じ条件）を指定するため。`lerobot-eval` のプラグイン機能で読み込む。reset 直後の最大関節速度は 10 ステップで 1.0e-2、50 ステップで 1.8e-4 |
| 2026-10-07 | 推論時間と GPU メモリを計測 | チャンク推論 中央値 189ms（初回は CUDA graph のキャプチャ込みで 861ms）、前処理 9ms/ステップ、VRAM ピーク約 26GB。Phase 0 完了 |
| 2026-10-07 | 評価・可視化ツールを作成 | `run_eval.py`（条件・git 情報つきで `results/<名前>/` に保存）、`rollout_video.py`（2 視点・実時間、先頭 10 本＋失敗を保存、終了フレームの欠落を補正）、`make_demo_video.py`（日本語の指示と成功率のテロップ） |
| 2026-10-07 | デモ用サンプル | 4 スイート × task 0・5 × 20 エピソードで 159/160。失敗は libero_goal task 0 の episode 12（引き出しの取っ手付近で停止し時間切れ）で、2 回の実行で同じエピソードが失敗（シード固定で再現） |
| 2026-10-07 | ベースライン評価と Phase 1 の完了 | 全 40 タスク × 5 エピソードで 194/200（97.0%）。spatial 96.0%・object 100%・goal 98.0%・libero_10 94.0%（報告値 97.8・100・97.8・93.2%）。失敗 6 件はすべて時間切れ。500 エピソード規模の評価と LeRobot 形式チェックポイントとの比較は行わずに Phase 1 を完了とした（ユーザーと合意） |
| 2026-10-07 | 記録の整理 | 出力を `results/<名前>/` に一本化（`videos/` と `eval.log` は git 管理外、テスト出力は `tmp/`）。重複・途中経過の実験記録（phase0_smoke、libero_goal_n5、2 エピソードのサンプル）を削除し、本ファイルを整理 |
| 2026-10-13 | Phase 2 の調査: LIBERO のタスク定義と LeRobot の読み込みの流れ | `docs/libero_task_definition.md`、`docs/lerobot_libero_loading.md` を作成。指示文は BDDL の `(:language)` ではなくファイル名から作られる。初期状態は MuJoCo の状態ベクトル 50 件（例: 50×79）で、カスタムタスクでは生成が必要（生成方法を確認済み）。`Task.problem_folder` に絶対パスを指定した自作スイートを LeRobot から読み込めることを確認。ワインボトルをキャビネットの奥に動かすと agentview から隠れることを確認（ただしキャビネットと重なり押し出されたため、配置は要修正） |
| 2026-10-13 | 実験の方針を決定 | 実験1（標準 LIBERO＋SG テキスト）・実験2（カスタムシーン＋SG テキスト）・実験3（SG エンコーダー）を、追加学習なし／ありで比較する。まず追加学習なしの実験1 から行う（libero_spatial 10 タスク × 5 エピソード × 6 条件）。実験3 は学習なしでは意味をなさないため学習ありのみ。評価結果は動画で確認できるように保存するルールを追加。Phase の構成をこれに合わせて組み替えた |
| 2026-10-13 | 実験1（学習なし）を実施 | SG 生成（`scene_graph/`）とプロンプト条件（`prompting/`、`run_eval.py --prompt-condition`）、集計（`compare_results.py`）を作成。libero_spatial 10 タスク × 5 エピソード × 6 条件で、A 96% / B1 90% / B2 86% / B3 82% / C 92% / D 94%。SG を加えても上がらず、内容によらずやや低下（有意差なし）。A はベースラインと成否が完全一致。所要約 64 分 |
| 2026-10-13 | 実験2（学習なし）を実施 | 自作スイートの登録（`envs/custom_suites.py`）と作成ツール（`make_custom_task.py`、`test_custom_suite.py`）を作成。`vla3dsg_hidden`: キャビネットの裏に隠れたボウル（task 0）と見える対照（task 1）。20 エピソード × 6 条件で、task 0 は全条件 0/20、task 1 は全条件 20/20。task 0 では見えている方のボウルを皿に置く。初回の実行は `run_eval.py` がスイート登録前にタスク数を数えて全条件エラーになったため、修正して取り直した。所要約 76 分 |
| 2026-10-14 | Phase 4: 追加学習なしの分析 | プロンプト条件 L0・L1、終了時の SG の記録と集計（`classify_outcomes.py`）、スクリプト制御（`scripted_pick_place.py`）を追加。SG の物体どうしの on に LIBERO の On も使うよう修正（皿の上のボウルを取りこぼしていた。実験1・2 の開始時の SG は全エピソードで変化なしを確認）。結果は `results/phase4/README.md`。途中で中断し、翌日に残りの評価を実行 |
| 2026-10-14 | 追加学習が回るかを確認 | `lerobot/libero`（1.9GB）で `MolmoAct2-LIBERO` を LoRA・bf16 で 40 マイクロバッチ学習。バッチ 8 で GPU メモリのピーク 29.7GB、1.63 秒/マイクロバッチ、チェックポイント 12GB。学習後のチェックポイントを `lerobot-eval --policy.path` で読み込み 2/2 成功。このPCで学習できるため、A6000 のサーバは当面使わない |
| 2026-10-14 | 学習サーバ（RTX 6000 Ada × 4、`ssh munetou-6000ada`）の準備 | 以前の作業の `~/lerobot` と不要なキャッシュ（W&B の成果物 168GB、旧モデル・データ約 60GB、古い venv、pip のキャッシュ）を削除し、`vla3dsg` ブランチを clone。venv は `~/environments/lerobot-vla3dsg`。ドライバ 550（CUDA 12.4）で torch 2.11.0+cu128 が動作。学習は 1 枚 6.06 秒、2 枚 7.14 秒/マイクロバッチ（他のユーザーが GPU を使用率 100% 近くで使っていたため、5090 の 1.63 秒より遅い）。サーバの使い方を CLAUDE.md に追記 |
| 2026-10-14 | デモの自動生成 | スクリプト制御を `vla3dsg/demos/` に切り出し（`make_custom_task.py`・`scripted_pick_place.py` も共通の処理を使う。隠れたボウルは引き続き 50/50）。`generate_demos.py` で `vla3dsg_hidden` の task 0・1 を各 50 本、13 分で生成。見えるボウル（task 1）はキャビネットに当たるため反対側の縁を掴む、掴む点のずらしは 0、1 エピソードの指令は 600 ステップで打ち切る（robosuite の horizon を超えるとエラーになるため）。学習の最初の損失は約 1.0（公式デモでは約 0.08） |
| 2026-10-14 | プログラムとフォルダの整理 | テストを `tests/` に移し、環境まわりの 3 本（`test_libero_env`・`test_libero_vla3dsg_env`・`test_custom_suite`）を `tests/test_envs.py` に統合。`compare_results.py` と `classify_outcomes.py` を `summarize_results.py` に、`scripted_pick_place.py` を `generate_demos.py --check` に統合。自作タスクを作る処理（配置範囲の書き換え・配置のサンプリング・見え方の計測）を `envs/custom_task_builder.py` に、シーンの画像を `visualization/scene_overview.py` にまとめ、`make_custom_task.py` がスイート全体の確認用画像（`previews/overview.png`、6 視点）を作るようにした（タスクごとの 2 視点の画像は削除）。既存の表は統合後も同じ内容になることを確認 |
