# サンプル実行: 4 スイート × 2 タスク × 2 エピソード（目視確認用）

- 日時: 2026-10-07
- 実行:
  ```bash
  uv run python vla3dsg/scripts/run_eval.py --name samples/four_suites_t0_t5_n2 \
      --suite libero_spatial,libero_object,libero_goal,libero_10 --task-ids 0 5 --n-episodes 2 --annotated-video
  uv run python vla3dsg/scripts/make_demo_video.py --name samples/four_suites_t0_t5_n2
  ```
- 条件: `conditions.json`（チェックポイント `allenai/MolmoAct2-LIBERO`、float32、`num_steps_wait=50`、シード 1000、元のタスク指示のみ）
- コミット: 実行時は `b605051b` に可視化コードの未コミット変更が乗った状態（`conditions.json` の `dirty: true`）。可視化コードは本結果と同じコミットで追加
- 所要時間: 257 秒（モデル読み込みを含む）

## 結果

成功率 **100%**（16/16）

| スイート | task_id | 指示文 | 成功 |
|---|---|---|---|
| libero_spatial | 0 | pick up the black bowl between the plate and the ramekin and place it on the plate | 2/2 |
| libero_spatial | 5 | pick up the black bowl on the ramekin and place it on the plate | 2/2 |
| libero_object | 0 | pick up the alphabet soup and place it in the basket | 2/2 |
| libero_object | 5 | pick up the tomato sauce and place it in the basket | 2/2 |
| libero_goal | 0 | open the middle drawer of the cabinet | 2/2 |
| libero_goal | 5 | push the plate to the front of the stove | 2/2 |
| libero_10 | 0 | put both the alphabet soup and the tomato sauce in the basket | 2/2 |
| libero_10 | 5 | pick up the book and place it in the back compartment of the caddy | 2/2 |

## 動画（git 管理外）

- テロップ付きデモ（全 16 エピソードを連結、133 秒、720x526、20fps）: `vla3dsg/outputs/eval/samples/four_suites_t0_t5_n2/videos/demo_with_captions.mp4`
  - 上部: タスク名、指示文、ステップ数、状態（RUNNING / SUCCESS / TIMEOUT）
  - 中央: agentview（左）と手首カメラ（右）
  - 下部テロップ: 与えた指示、タスクごとの成功率（成功回数/実行数）、エピソードごとの成否
  - 各エピソードの最後のフレームを 1 秒止めて表示
- エピソードごとの動画: 同じディレクトリの `<スイート>_<タスクID>/eval_episode_<n>.mp4`
