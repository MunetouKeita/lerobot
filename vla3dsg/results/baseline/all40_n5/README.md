# ベースライン: 4 スイート全 40 タスク × 5 エピソード（簡易チェック）

- 目的: 全タスクで評価が正しく動くか（特定のタスクだけ成功率が極端に低いなどの問題がないか）を確認する。成功率の精密な再現は目的としない
- 日時: 2026-10-07
- 実行: `uv run python vla3dsg/scripts/run_eval.py --name baseline/all40_n5 --suite libero_spatial,libero_object,libero_goal,libero_10 --task-ids 0 1 2 3 4 5 6 7 8 9 --n-episodes 5 --annotated-video`
- 条件: `conditions.json`（チェックポイント `allenai/MolmoAct2-LIBERO`、`norm_tag=libero`、float32、`num_steps_wait=50`、シード 1000、元のタスク指示のみ）
- コミット: `b41a990d`（未コミットの変更なし。upstream ベース `200ee535`）
- 所要時間: 2,729 秒（約 45 分、モデル読み込みを含む）

## 結果

成功率 **97.0%**（194/200）。成功率 0 のタスクはなく、全タスクで評価が正しく動いている

| スイート | 今回（各 50 エピソード） | MolmoAct2 Original（報告値） | LeRobot Implementation（報告値） |
|---|---|---|---|
| libero_spatial | 96.0% | 97.8% | 98.4% |
| libero_object | 100.0% | 100.0% | 100.0% |
| libero_goal | 98.0% | 97.8% | 98.0% |
| libero_10 | 94.0% | 93.2% | 96.6% |
| 平均 | 97.0% | 97.2% | 98.25% |

報告値は各スイート 500 エピソード（`docs/source/molmoact2.mdx`）。今回は各 50 エピソードのため、スイートごとの差は誤差の範囲（50 エピソードで 1 回の失敗が 2 ポイントに相当）。

## 失敗エピソード（6 件、すべて上限ステップでの時間切れ）

| スイート / task | 指示文 | 成功 | 失敗した episode | 最後の様子 |
|---|---|---|---|---|
| libero_spatial / 4 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 4/5 | 3 | ボウルを皿まで運べていない |
| libero_spatial / 8 | pick up the black bowl next to the plate and place it on the plate | 4/5 | 0 | ボウルを皿の上まで運んだが置き終わっていない |
| libero_goal / 2 | put the wine bottle on top of the cabinet | 4/5 | 2 | ワインボトルをキャビネットの上に置けていない |
| libero_10 / 8 | put both moka pots on the stove | 3/5 | 1, 2 | モカポットの 1 つはコンロに載ったが、2 つ目を載せられていない |
| libero_10 / 9 | put the yellow and white mug in the microwave and close it | 4/5 | 4 | マグカップが電子レンジの入口で傾いて止まっている |

上記以外の 35 タスクは 5/5。タスクごとの結果は `summary.json`。

## 動画・ログ（git 管理外）

- 全エピソードの動画（各タスク 5 本）: `videos/<スイート>_<タスクID>/eval_episode_<n>.mp4`
- 実行ログ: `eval.log`
