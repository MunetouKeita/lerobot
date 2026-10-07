# ベースライン: libero_goal（10 タスク × 5 エピソード）

- 日時: 2026-10-07
- 実行: `uv run python vla3dsg/scripts/run_eval.py --name baseline/libero_goal_n5 --suite libero_goal --n-episodes 5`
- 条件: `conditions.json`（チェックポイント `allenai/MolmoAct2-LIBERO`、`norm_tag=libero`、float32、`num_steps_wait=50`、シード 1000、元のタスク指示のみ）
- コミット: `8d664192`（upstream ベース `200ee535`）
- 所要時間: 322 秒（モデル読み込みを含む）

## 結果

成功率 **98.0%**（49/50、95% Wilson 区間 89.5〜99.6%）

| task_id | 指示文 | 成功 |
|---|---|---|
| 0 | open the middle drawer of the cabinet | 5/5 |
| 1 | put the bowl on the stove | 5/5 |
| 2 | put the wine bottle on top of the cabinet | 4/5 |
| 3 | open the top drawer and put the bowl inside | 5/5 |
| 4 | put the bowl on top of the cabinet | 5/5 |
| 5 | push the plate to the front of the stove | 5/5 |
| 6 | put the cream cheese in the bowl | 5/5 |
| 7 | turn on the stove | 5/5 |
| 8 | put the bowl on the plate | 5/5 |
| 9 | put the wine bottle on the rack | 5/5 |

## 報告値との比較

| | LIBERO Goal |
|---|---|
| 今回（元の HF チェックポイント、50 エピソード） | 98.0% |
| MolmoAct2 Original（`docs/source/molmoact2.mdx`） | 97.8% |
| LeRobot Implementation（`MolmoAct2-LIBERO-LeRobot`） | 98.0% |

報告値（各スイート 500 エピソード）とほぼ一致。ただし 50 エピソードのため信頼区間は広い。

## 失敗エピソード

- task 2 の episode 2: 上限の 300 ステップで時間切れ。腕がキャビネットの上付近で止まったまま終了している（動画は `vla3dsg/outputs/eval/baseline/libero_goal_n5/videos/libero_goal_2/eval_episode_2.mp4`、git 管理外）
