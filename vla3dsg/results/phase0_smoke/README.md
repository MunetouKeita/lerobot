# Phase 0: 1タスク・1エピソードの動作確認

- 日時: 2026-10-07
- LeRobot: `8c920c42`（upstream main）+ `vla3dsg` ブランチ（本体の変更なし）
- チェックポイント: `allenai/MolmoAct2-LIBERO`（元の HF チェックポイント、`norm_tag=libero`、float32）
  - `allenai/MolmoAct2-LIBERO-LeRobot` は config.json が現在の LeRobot と非互換のため未使用
- スイート / タスク: `libero_goal` / task 0（open the middle drawer of the cabinet）
- シード: `--seed=1000`、`--policy.per_episode_seed=true`、`--policy.eval_seed=1000`
- プロンプト条件: 元のタスク指示のみ
- `num_steps_wait`: 10（LeRobot の既定値。MolmoAct2 の報告値は 50 で測定）

## 結果

- 成功（1/1）、126 ステップで終了（上限 300）
- 評価時間 8.9 秒（CUDA graph のキャプチャ含む）、コマンド全体 36.6 秒（モデルの読み込み含む）
- GPU メモリのピーク: 26,887 MiB（デスクトップ表示分の約 900 MiB を含む）
- 動画: `eval_episode_0.mp4`（agentview のみ、360x360、80fps で保存されるため実時間の4倍速で再生される）

## コマンド

```bash
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
uv run lerobot-eval \
  --policy.type=molmoact2 \
  --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
  --policy.norm_tag=libero \
  --policy.inference_action_mode=continuous \
  --policy.dtype=float32 \
  --policy.enable_inference_cuda_graph=true \
  --policy.device=cuda \
  --policy.per_episode_seed=true \
  --policy.eval_seed=1000 \
  --env.type=libero \
  --env.task=libero_goal \
  --env.task_ids='[0]' \
  --env.camera_name_mapping='{"agentview_image":"image","robot0_eye_in_hand_image":"wrist_image"}' \
  --eval.batch_size=1 \
  --eval.n_episodes=1 \
  --seed=1000 \
  --output_dir=vla3dsg/outputs/phase0_smoke
```

- 当時の出力先 `vla3dsg/outputs/` は 2026-10-07 の整理で削除した。動画と `eval_info.json` はこのディレクトリにある
