# 追加学習なしで SG を指示文に加える（libero_goal「put the bowl on the plate」の 4 シーン）

- 日時: 2026-10-21。学習サーバ（RTX 6000 Ada）の GPU 0〜3 でジョブ（シーン × 条件）を並列に実行
- スイート: `custom_tasks/vla3dsg_goal/`（task 0 標準、1 場所シャッフル、2 標準＋隠れ、3 標準＋隠れ（おとりあり））。各 20 エピソード、最大ステップ数は標準・場所シャッフル 300、隠れた 2 シーン 400（2026-10-26 にこのPCで評価し直した。300 のときも成功率は同じ 0%）
- 実行: `run_eval.py --name zeroshot/<シーン>/<条件> --suite vla3dsg_goal --task-ids <task> --n-episodes 20 --prompt-condition <条件> --annotated-video`
- 集計: `summarize_results.py --root zeroshot --scenes standard shuffle hidden hidden_decoy --names base base_short base_wrong`（`comparison.md`）。シーンごとの表と「何をどこに置いたか」は `<シーン>/comparison.md`・`outcomes.md`
- 評価前の確認資料: `conditions/scenes.png`（各シーンの初期状態と対象の赤丸）、`conditions/prompts.md`（全シーン × 全条件の指示文）。`show_conditions.py --suite vla3dsg_goal --out zeroshot/conditions` で作る
- コミット: `c0b9b780` に未コミットの変更（条件・SG の修正）を載せて実行した（`conditions.json` の `git.dirty` は true）
- 2026-11-17: 結論に効かない条件（SG の JSON・自然文の書き方、すべての SG、同じ長さの無関係な文、SG から作った指示文）の結果を削除し、3 条件にした

## シーン

| シーン | 配置 |
|---|---|
| 標準 | libero_goal task 8 の公式の初期状態のまま（学習時と同じシーン） |
| 場所シャッフル | 皿→クリームチーズの位置、ボウル→手前左、クリームチーズ→皿の位置、ワイン瓶→ボウルの位置（学習にない配置） |
| 標準＋隠れ | ボウルをワインラックの裏（-0.47, -0.26）に置く。agentview から見える割合 0%。ほかは標準のまま |
| 標準＋隠れ（おとりあり） | 上に加え、見えるボウル 2 を標準のボウルの位置に置く |

## 指示文の条件

| 条件 | 指示文（標準＋隠れ（おとりあり）の例） |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet)（おとりの場所。おとりがなければ前後左右を逆にする。SG の中身が使われているかの対照） |

- 隠れていることは伝えない（ユーザーの方針）
- 短い SG の手がかりには、同じ種類の物体（black bowl 2）と行き先（plate）を使わない。行き先を使うと「put the black bowl behind the plate on the plate」のような文になるため
- 標準・場所シャッフルでは見分ける相手がいないため、短い SG は最も近い固定物との関係（left of wooden cabinet）になる。誤った SG の「right of wooden cabinet」は、キャビネットがテーブルの右端にあるため物理的にありえない関係

## 結果

| 条件 | 標準 | 場所シャッフル | 標準＋隠れ | 標準＋隠れ（おとりあり） |
|---|---|---|---|---|
| base | 95%（19/20） | 10%（2/20） | 0% | 0% |
| base_short | 100% | 45%（9/20） | 0% | 0% |
| base_wrong | 100% | 40%（8/20） | 0% | 0% |

- 場所シャッフルで base と比べた Fisher の正確検定: base_short p = 0.03、base_wrong p = 0.06。base_short と base_wrong の差は p = 1.0
- 何をどこに置いたか（`<シーン>/outcomes.md`）:
  - 場所シャッフル: 失敗の多くは、ボウルを掴んで皿の上まで運ぶが、離さずに時間切れ（終了時の SG では "black bowl on plate" だが成功判定にならない）か、掴む前に止まる。base は 20 回中 12 回が何も置かずに終わった
  - 標準＋隠れ: クリームチーズを皿に置く（base 9 回）か、何も置かずに終わる
  - 標準＋隠れ（おとりあり）: 全条件で、ほぼ毎回見えているボウル 2 を皿に置いた

読み取れること:

- 標準のシーンでは、どの条件でもほぼ 100%。SG を付けても（誤った SG でも）邪魔にならない
- 場所シャッフルでは、公式の指示文のままだと 10% まで下がるが、SG を付けると 45% に上がる。ただし誤った SG も 40% で、正しい SG と差がない。上がったのは SG の中身のためではなく、公式の文に何かを付け足すことによる（原因は不明）
- 隠れたボウルは、どの条件でも取りに行かない。おとりがあれば見えている方を取り、なければ見えている別の物体（クリームチーズ）を置くか止まる。追加学習なしでは、SG の場所の情報は隠れた物体の操作に使われない
