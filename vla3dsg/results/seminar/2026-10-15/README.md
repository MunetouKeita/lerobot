# ゼミ報告（2026-10-15）: VLA×3DSG の進捗

モデルは MolmoAct2（LIBERO 向けにファインチューニング済みの `allenai/MolmoAct2-LIBERO`）。ここまではすべて **追加学習なし**（ゼロショット）。動画は `videos/`（git 管理外。`scripts/make_comparison_video.py` で作成）。

## 1. 環境を変えずに、関係性を言語指示に加えた結果（実験1）

### 方法

- タスク: LIBERO の libero_spatial 10 タスク（同じ黒いボウルが 2 つあり、「皿とラメキンの間のボウル」のように位置関係で対象を指定する）× 各 5 エピソード × 6 条件
- 言語指示: 元の指示文の後ろに `. scene information: <追加テキスト>` を付ける

| 条件 | 追加したもの |
|---|---|
| A | なし（元の指示文のみ） |
| B1 | SG を JSON で |
| B2 | SG を三つ組の列挙で |
| B3 | SG を自然文で |
| C | B1 と同じトークン数の、タスクと無関係な文（長さの影響を切り分ける対照） |
| D | 物体名をでたらめに入れ替えた SG（内容を使っているかを確かめる対照） |

- 関係性（SG）の作り方: エピソードの開始時（物体が落ち着いた後）に、シミュレータの正解の状態から作る（`vla3dsg/scene_graph/builder.py`）。知覚の誤差を切り離し、「SG が正しく与えられた場合」を先に測るため
  - ノード: 物体（読みやすい名前。同じ種類は "black bowl 1/2" のように番号）
  - 支える関係（on / in）: LIBERO の成功判定と同じ述語で判定（引き出しの中・棚の上面・コンロの上、物体どうしは接触と高さ）
  - 前後左右: agentview（テーブルの反対側からロボットの方を向いたカメラ）から見た向き。各物体について近い 2 物体との関係を付け、3cm 未満なら "next to"
  - 1 シーンあたり 10 本前後の関係
- プロンプトの例（task 7「コンロの上のボウルを皿へ」）:
  - A: `pick up the black bowl on the stove and place it on the plate`
  - B2: `... on the plate. scene information: (black bowl 1, on, stove); (black bowl 2, on, top of wooden cabinet); (black bowl 1, behind, wooden cabinet); (black bowl 2, right of, cookie box); (cookie box, right of, plate); ...`
  - B3: `... scene information: the black bowl 1 is on the stove. the black bowl 2 is on the top of wooden cabinet. ...`

### 結果

| 条件 | 成功率（50 エピソード） | A との差（Fisher の正確検定） |
|---|---|---|
| A 元の指示文のみ | 96% | — |
| B1 ＋SG（JSON） | 90% | p = 0.44 |
| B2 ＋SG（三つ組） | 86% | p = 0.16 |
| B3 ＋SG（自然文） | 82% | p = 0.051 |
| C ＋無関係な文 | 92% | p = 0.68 |
| D ＋誤った SG | 94% | p = 1.00 |

- SG を加えても成功率は上がらず、どの形式でもやや下がった（有意差はない）
- 無関係な文（C）や誤った SG（D）でも正しい SG と同程度 → **モデルは SG の内容を使っていない**。学習時と違う形の指示文になったこと自体で、少し乱れる
- 失敗は、正しい対象の近くで止まる・置き終わらない形で、違うボウルを掴む失敗はなかった

### 動画

- `videos/1_exp1_conditions_task7_ep4.mp4`: 同じエピソード（task 7 episode 4）を 6 条件で並べた比較。A・C・D は成功し、正しい SG を加えた B1〜B3 は失敗する
- 各条件の全エピソード: `results/exp1/libero_spatial_n5/<条件>/videos/`

## 2. 環境の作成方法

### LIBERO のタスクの作り方

- LIBERO のタスクは BDDL ファイルで定義される（物体・固定物の種類、配置範囲（region）、初期条件、成功条件）。評価では、BDDL と、物体の配置を固定した初期状態 50 件（MuJoCo の状態ベクトル）を読み込む
- 自作タスクは `vla3dsg/custom_tasks/<スイート>/` に置き、LeRobot の評価（`lerobot-eval`）にプラグインとして登録する（LeRobot 本体は変更しない）

### 作成の手順（`scripts/make_custom_task.py`）

1. 元の BDDL（LIBERO のタスク、または手で書いたシーン）の配置範囲を書き換え、対象物体の置き場所を変える
2. 配置をランダムにサンプリングし、評価と同じく 50 ステップ待って落ち着かせる。固定物と重なって押し出された・倒れた配置は捨て、問題のない 50 件を初期状態として保存する
3. 対象物体が隠れているかを測る: カメラから対象物体の表面の点（最大 400 点）へ光線を飛ばし、遮る物体をどけた場合に対して何 % が直接見えるか
4. 6 視点（ポリシーの入力の agentview・手首カメラと、確認用の真上・横・正面・斜め）の画像を保存する

### 作った環境

| スイート | 内容 | 使った実験 |
|---|---|---|
| `vla3dsg_hidden` | libero_spatial task 0 の対象のボウルを、木のキャビネットの裏（隠れ）と横（見える）に置いた 2 タスク。指示文に場所を書く（"... behind the wooden cabinet ..."） | 実験2 |
| `vla3dsg_occluded`（新） | 電子レンジを加え、ボウル 1 を木のキャビネット・電子レンジの裏（隠れ）と横（見える）に置いた 4 タスク。指示文は共通（"pick up the black bowl 1 and place it on the plate"）で、**場所は SG にだけ書く**。見えている別のボウル（おとり）もある | 追加学習（準備中） |

- 画像: `custom_tasks/vla3dsg_hidden/previews/overview.png`、`custom_tasks/vla3dsg_occluded/previews/overview.png`
- `vla3dsg_occluded` を作った理由: `vla3dsg_hidden` は指示文に場所があり、隠れ場所も 1 か所なので、追加学習すれば SG なしでも解けてしまい、SG の効果を測れない。隠れ場所を 2 つにし、2 つの場合の agentview の画像はほぼ同じなので、画像からはどちらに隠れているかわからない

### 追加学習のための教師データ（スクリプト制御によるデモ）

- シミュレータの正解の位置を使って手先を動かすスクリプト制御（`vla3dsg/demos/scripted.py`）で、隠れたボウルを取り出して皿に置くデモを自動生成した（`scripts/generate_demos.py`）。`vla3dsg_occluded` の 4 タスク × 50 本 = 200 本
- 公式の人によるデモと同じ形式（画像・状態・動作）で保存し、学習が回ることを確認した
- 機械的な動きにならないよう、速さ・加速の制限、手先の向きの補正、小さな揺らぎ、経由点のばらつきを入れた。公式デモとの比較は `results/demos/occluded_v1/README.md`

### 動画

- `videos/2_custom_env_scripted_demos.mp4`: `vla3dsg_occluded` の 4 タスクで、スクリプト制御が隠れた／見えるボウルを皿に置く様子
- ポリシー（MolmoAct2）が自作環境で動く様子は 3 の動画

## 3. 隠れた物体の環境での実験結果（実験2）

### 方法

- スイート `vla3dsg_hidden`: task 0 はボウルがキャビネットの裏（agentview から見える割合 0%）、task 1 はキャビネットの横（100%、対照）
- 実験1 と同じ 6 条件 × 各 20 エピソード

### 結果

| 条件 | 隠れ（task 0） | 見える（task 1） |
|---|---|---|
| A 元の指示文のみ | 0/20 | 20/20 |
| B1〜B3 ＋SG | 0/20 | 20/20 |
| C・D（対照） | 0/20 | 20/20 |

- **見えていれば成功し、見えていなければ失敗する。SG の有無・形式は関係ない**
- 隠れているときは、20 回中 19 回、見えている方の別のボウルを皿に置いた（エピソード終了時の SG で自動集計）。キャビネットの方へ向かうことは一度もない
- 原因の切り分け（Phase 4）:
  - 指示文を別のタスクのものに差し替えると、MolmoAct2 はその指示に従って動く（libero_goal）。見えている 2 つのボウルからは、指示文の場所の指定に合う方を選べる（libero_spatial）
  - つまり言語は読んでいるが、**見えない物体を探しに行く動作を学習していない**
  - 隠れたボウルは、スクリプト制御なら 50/50 で掴める（物理的にはできるタスク）

### 動画

- `videos/3_exp2_hidden_vs_visible.mp4`: 隠れ／見える × SG なし／あり。隠れでは SG があっても見えている方のボウルを置き、見えれば SG の有無によらず成功する
- `videos/3_hidden_policy_vs_scripted.mp4`: 同じ隠れたボウルを、MolmoAct2（失敗）とスクリプト制御（成功）で比べたもの

## まとめと次の予定

- 追加学習なしでは、SG をテキストで与えても効果はない（標準タスクではやや悪化、隠れた物体では変化なし）
- 次: `vla3dsg_occluded` で追加学習なしの基準を取り、スクリプト制御のデモ（＋公式デモ）で SG なし／SG ありの 2 モデルを追加学習して比べる。学習は、このPC（RTX 5090）または学習サーバ（RTX 6000 Ada）で行う
