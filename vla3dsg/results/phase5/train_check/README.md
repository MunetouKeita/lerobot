# MolmoAct2 の追加学習が RTX 5090 で回るかの確認

- 日時: 2026-10-14
- コミット: `3004e9d8`
- 目的: 追加学習（Phase 5）を、このPC（RTX 5090、VRAM 32GB）で行えるかを確かめる。回らなければ RTX A6000 のサーバで学習だけ行う予定だった
- データ: `lerobot/libero`（LIBERO 4 スイートの公式デモを LeRobot v3.0 形式にしたもの。1693 エピソード、1.9GB、10fps）
- 初期の重み: `allenai/MolmoAct2-LIBERO`（`--policy.checkpoint_path`）
- 設定（`train_config.json`）: LoRA（VLM、rank 64）＋アクションエキスパートは全パラメータ、bf16、勾配チェックポイント、`num_flow_timesteps=8`、画像の拡張あり、`compile_model=false`。学習するパラメータは 7.4 億（全体 56 億）

```bash
uv run lerobot-train --dataset.repo_id=lerobot/libero --dataset.root=<データセットのパス> --dataset.video_backend=pyav \
  --dataset.image_transforms.enable=true --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
  --policy.device=cuda --policy.action_mode=continuous --policy.norm_tag=libero \
  --policy.norm_stats_path=<MolmoAct2-LIBERO の norm_stats.json> --policy.train_mode_vlm=lora \
  --policy.chunk_size=10 --policy.n_action_steps=10 --policy.setup_type="single franka robotic arm in libero" \
  --policy.control_mode="delta end-effector pose" \
  --policy.image_keys='["observation.images.image","observation.images.image2"]' --policy.dtype=bfloat16 \
  --policy.num_flow_timesteps=8 --policy.gradient_checkpointing=true --policy.compile_model=false \
  --policy.freeze_embedding=true --policy.normalize_gripper=false --policy.enable_knowledge_insulation=false \
  --policy.push_to_hub=false --wandb.enable=false --output_dir=<出力先> --steps=40 --batch_size=8 \
  --accelerator.gradient_accumulation.steps=4 --num_workers=4 --log_freq=10 --env_eval_freq=-1 \
  --save_checkpoint=true --save_freq=40
```

## 結果

| 項目 | 結果 |
|---|---|
| 学習 | バッチ 8 で動く。勾配累積 4（実効バッチ 32、ドキュメントの推奨は 16〜32）も動く |
| GPU メモリ | PyTorch の計測で 25.8GB、`nvidia-smi` のピークで 29.7GB（32.6GB 中） |
| 速度 | 1 マイクロバッチ（8 サンプル）あたり約 1.63 秒（約 5 サンプル/秒）。`--steps` はマイクロバッチの数 |
| チェックポイント | 保存できる（1 つあたり 12GB） |
| 評価での読み込み | `lerobot-eval --policy.path=<checkpoint>/pretrained_model` で読み込め、libero_spatial task 0 で 2/2 成功（10 回の更新のみ） |

- **このPCで学習できる。** RTX A6000 のサーバは当面不要
- ただし余裕は約 3GB。SG を加えた指示文は、元の指示文より約 110〜170 トークン長い（実験1）ため、メモリがさらに増える可能性がある。足りなければバッチを 4 にして勾配累積を増やすか、A6000（48GB）で学習する
- 目安: 実効バッチ 32 で 1 万回更新すると約 18 時間（4 万マイクロバッチ × 1.63 秒）。`compile_model=true` で少し速くなる可能性がある
- `grdn`（勾配ノルム）のログが 0.000 なのは、MolmoAct2 がパラメータのグループごとに勾配を切り詰めており、全体の勾配ノルムを計算しないため（`grad_clip_norm=0`）。学習が止まっているわけではない
