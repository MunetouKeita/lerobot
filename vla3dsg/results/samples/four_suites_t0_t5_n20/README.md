# サンプル実行: 4 スイート × 2 タスク × 20 エピソード（デモ動画用）

- 日時: 2026-10-07
- 実行:
  ```bash
  uv run python vla3dsg/scripts/run_eval.py --name samples/four_suites_t0_t5_n20 \
      --suite libero_spatial,libero_object,libero_goal,libero_10 --task-ids 0 5 --n-episodes 20 --annotated-video
  uv run python vla3dsg/scripts/make_demo_video.py --name samples/four_suites_t0_t5_n20
  ```
- 条件: `conditions.json`（チェックポイント `allenai/MolmoAct2-LIBERO`、float32、`num_steps_wait=50`、シード 1000、元のタスク指示のみ）
- コミット: 実行時は `e1c7c5a3` に出力フォルダ整理の未コミット変更が乗った状態（`conditions.json` の `dirty: true`）。変更は本結果と同じコミットで追加
- 所要時間: 1,982 秒（約 33 分、モデル読み込みを含む）

## 結果

成功率 **99.4%**（159/160）

| スイート | task_id | 指示文 | 成功 |
|---|---|---|---|
| libero_spatial | 0 | pick up the black bowl between the plate and the ramekin and place it on the plate | 20/20 |
| libero_spatial | 5 | pick up the black bowl on the ramekin and place it on the plate | 20/20 |
| libero_object | 0 | pick up the alphabet soup and place it in the basket | 20/20 |
| libero_object | 5 | pick up the tomato sauce and place it in the basket | 20/20 |
| libero_goal | 0 | open the middle drawer of the cabinet | 19/20 |
| libero_goal | 5 | push the plate to the front of the stove | 20/20 |
| libero_10 | 0 | put both the alphabet soup and the tomato sauce in the basket | 20/20 |
| libero_10 | 5 | pick up the book and place it in the back compartment of the caddy | 20/20 |

- 失敗: libero_goal task 0 の episode 12（`lerobot-eval` は 1 タスクあたり先頭 10 本しか動画を保存しないため、動画はない）

## 動画（git 管理外）

- デモ動画（8 タスク × 各 1 エピソード、68 秒、720x468、20fps の等倍）: `videos/demo_with_captions.mp4`
  - 映像: agentview（左）と手首カメラ（右）。各タスクの episode 0（すべて成功）
  - 下部テロップ: 「指示：<指示文の日本語訳>」と「成功率：<成功回数>/20」
- エピソードごとの動画（テロップなし、各タスク先頭 10 本）: `videos/<スイート>_<タスクID>/eval_episode_<n>.mp4`
- 実行ログ: `eval.log`
