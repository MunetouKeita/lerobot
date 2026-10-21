# 追加学習なしで SG を指示文に加える（libero_goal「put the bowl on the plate」の 4 シーン）

SG の形式の比較（標準・場所シャッフル）と、4 シーン × 5 条件の比較の 2 つ。同じスイート・同じシードで評価したため、三つ組の条件は両方で共通の結果を使う。

- 日時: 2026-10-21。学習サーバ（RTX 6000 Ada）の GPU 0〜3 でジョブ（シーン × 条件）を並列に実行（4 シーン × 5 条件は約 50 分、形式の比較は約 20 分）
- スイート: `custom_tasks/vla3dsg_goal/`（task 0 標準、1 場所シャッフル、2 標準＋隠れ、3 標準＋隠れ（おとりあり））。各 20 エピソード、最大 300 ステップ
- 実行: `run_eval.py --name zeroshot/<シーン>/<条件> --suite vla3dsg_goal --task-ids <task> --n-episodes 20 --prompt-condition <条件> --annotated-video`
- 集計:
  - 4 シーン × 5 条件: `summarize_results.py --root zeroshot --scenes standard shuffle hidden hidden_decoy --names base base_short base_full base_wrong sg_command`（`comparison.md`）
  - 形式の比較: `summarize_results.py --root zeroshot --scenes standard shuffle --table formats.md --names base base_short base_short_json base_short_nl base_full base_full_json base_full_nl base_irrelevant base_wrong base_wrong_json base_wrong_nl`（`formats.md`）
  - シーンごとの表と「何をどこに置いたか」は `<シーン>/comparison.md`・`outcomes.md`
- 評価前の確認資料: `conditions/scenes.png`（各シーンの初期状態と対象の赤丸）、`conditions/prompts.md`（全シーン × 全条件の指示文）。`show_conditions.py --suite vla3dsg_goal --out zeroshot/conditions` で作る
- コミット: 4 シーン × 5 条件は `c0b9b780`、形式の比較は `8c959c58` に、それぞれ未コミットの変更（条件・SG の修正、形式の追加）を載せて実行した（`conditions.json` の `git.dirty` は true）

## シーン

| シーン | 配置 |
|---|---|
| 標準 | libero_goal task 8 の公式の初期状態のまま（学習時と同じシーン） |
| 場所シャッフル | 皿→クリームチーズの位置、ボウル→手前左、クリームチーズ→皿の位置、ワイン瓶→ボウルの位置（学習にない配置） |
| 標準＋隠れ | ボウルをワインラックの裏（-0.47, -0.26）に置く。agentview から見える割合 0%。ほかは標準のまま |
| 標準＋隠れ（おとりあり） | 上に加え、見えるボウル 2 を標準のボウルの位置に置く |

## 1. SG の形式の比較（標準・場所シャッフル）

| 形式 | 短い SG の例（場所シャッフル） | すべての SG の長さ（場所シャッフル、中央値） |
|---|---|---|
| 三つ組 | scene information: (black bowl, left of, wooden cabinet) | 76 トークン |
| JSON | scene information: [{"subject": "black bowl", "relation": "left of", "object": "wooden cabinet"}] | 168 トークン |
| 自然文 | scene information: the black bowl is to the left of the wooden cabinet. | 84 トークン |
| 無関係な文（対照） | scene information: the weather was sunny in the morning and ...（すべての SG と同じ長さに切り出す） | 75 トークン |

| 条件 | 標準 | 場所シャッフル |
|---|---|---|
| base（公式の指示文のみ） | 95%（19/20） | 10%（2/20） |
| ＋短い SG（三つ組 / JSON / 自然文） | 100 / 100 / 100% | 45 / 20 / 45% |
| ＋すべての SG（三つ組 / JSON / 自然文） | 100 / 100 / 100% | 0 / 0 / 0% |
| ＋誤った SG（三つ組 / JSON / 自然文） | 100 / 100 / 100% | 40 / 45 / 60% |
| ＋同じ長さの無関係な文 | — | 0%（0/20） |

- 場所シャッフルの Fisher の正確検定: 短い SG の三つ組と JSON p = 0.18、誤った SG の自然文と三つ組 p = 0.34、無関係な文と短い SG（三つ組） p = 0.001
- すべての SG（3 形式）と無関係な文は、どれも 20 回中 19〜20 回が何も置かずに終わった

読み取れること:

- 標準のシーンでは、形式・中身によらずすべて 100%（base は 95%）。上限に張り付いており、差は検出できない
- 場所シャッフルでも、形式による一貫した差はない（短い SG は JSON が低く、誤った SG は自然文が高いが、どちらも有意差なし）。4 シーンの比較では、最も短く区切りがはっきりした三つ組を使う
- 誤った SG がどの形式でも正しい SG と同程度以上（40〜60%）のため、SG の中身は使われていない
- すべての SG は形式によらず 0% で、同じ長さの無関係な文も 0%。すべての SG で下がるのは、中身ではなく文の長さによる。標準のシーンでは長くても 100% のため、長い文が見慣れない配置と重なると大きく下がる

## 2. 4 シーン × 5 条件

| 条件 | 指示文（標準＋隠れ（おとりあり）の例） |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
| base_full | put the bowl on the plate. scene information: （全部の関係 8〜10 本） |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet)（おとりの場所。おとりがなければ前後左右を逆にする） |
| sg_command | put the black bowl behind the wine rack on the plate |

- 隠れていることは伝えない（ユーザーの方針）
- 短い SG の手がかりには、同じ種類の物体（black bowl 2）と行き先（plate）を使わない。行き先を使うと「put the black bowl behind the plate on the plate」のような文になるため
- 標準・場所シャッフルでは見分ける相手がいないため、短い SG は最も近い固定物との関係（left of wooden cabinet）になる。誤った SG の「right of wooden cabinet」は、キャビネットがテーブルの右端にあるため物理的にありえない関係

| 条件 | 標準 | 場所シャッフル | 標準＋隠れ | 標準＋隠れ（おとりあり） |
|---|---|---|---|---|
| base | 95%（19/20） | 10%（2/20） | 0% | 0% |
| base_short | 100% | 45%（9/20） | 0% | 0% |
| base_full | 100% | 0%（0/20） | 0% | 0% |
| base_wrong | 100% | 40%（8/20） | 0% | 0% |
| sg_command | 100% | 55%（11/20） | 0% | 0% |

- 場所シャッフルで base と比べた Fisher の正確検定: sg_command p = 0.006、base_short p = 0.03、base_wrong p = 0.06、base_full p = 0.49。base_short と base_wrong の差は p = 1.0
- 何をどこに置いたか（`<シーン>/outcomes.md`）:
  - 場所シャッフル: 失敗の多くは、ボウルを掴んで皿の上まで運ぶが、離さずに時間切れ（終了時の SG では "black bowl on plate" だが成功判定にならない）か、掴む前に止まる。base は 20 回中 12 回が何も置かずに終わった
  - 標準＋隠れ: クリームチーズを皿に置く（base 9 回、base_full 15 回）か、何も置かずに終わる
  - 標準＋隠れ（おとりあり）: 全条件で、ほぼ毎回見えているボウル 2 を皿に置いた（100 回中 98 回）

読み取れること:

- 標準のシーンでは、どの条件でもほぼ 100%。SG を付けても（誤った SG でも）邪魔にならない
- 場所シャッフルでは、公式の指示文のままだと 10% まで下がるが、SG を付けると 40〜55% に上がる。ただし base_wrong（中身の誤った SG。ボウルが 1 つなので実質的に中身が役に立たない文）は 40% で、正しい短い SG の 45% と差がない（1 の 3 形式でも同じ）。上がったのは SG の中身のためではなく、公式の文に何かを付け足すことによる。付け足すとなぜ上がるのか、公式の文のままだとなぜ 10% まで下がるのかは原因不明
- 隠れたボウルは、どの条件でも取りに行かない。おとりがあれば見えている方を取り、なければ見えている別の物体（クリームチーズ）を置くか止まる。追加学習なしでは、SG の場所の情報は隠れた物体の操作に使われない
- 追加学習では、隠れたシーンで SG の情報を使えるようにすることが主な目的になる。場所シャッフルの結果から、学習時と違う配置への弱さも合わせて見る必要がある
