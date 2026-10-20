# MolmoAct2 の追加学習が RTX 5090 で回るかの確認

- 日時: 2026-10-14
- コミット: `3004e9d8`
- 目的: 追加学習を、このPC（RTX 5090、VRAM 32GB）で行えるかを確かめる。回らなければ RTX A6000 のサーバで学習だけ行う予定だった
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

## 学習サーバ（RTX 6000 Ada）での確認（2026-10-14）

同じ設定（バッチ 8、20 マイクロバッチ）を学習サーバ（`ssh munetou-6000ada`、CLAUDE.md の「学習サーバ」）で実行した。ドライバは 550（CUDA 12.4）だが、`uv.lock` の torch 2.11.0+cu128 がそのまま動いた。2 枚では `uv run accelerate launch --num_processes=2 --mixed_precision=bf16 -m lerobot.scripts.lerobot_train ...`。

| 構成 | 秒/マイクロバッチ | サンプル/秒 | GPU メモリ（PyTorch の計測、1 枚あたり） |
|---|---|---|---|
| RTX 5090 × 1（このPC） | 1.63 | 4.9 | 25.8GB |
| RTX 6000 Ada × 1 | 6.06 | 1.3 | 24.1GB |
| RTX 6000 Ada × 2 | 7.14（2 枚で 16 サンプル） | 2.2 | 26.9GB |

- 実行時、サーバの GPU 4 枚はすべて他のユーザーの計算で使用率 94〜100%（メモリは 15〜22GB 使用）だった。そのため 1 枚あたり 5090 の 1/4 程度の速さしか出ず、2 枚でも 5090 1 枚の半分以下
- 速さは他のユーザーの使用状況で変わる。GPU が空いていれば、2 枚で 5090 より速くなる見込み（6000 Ada 1 枚の bf16 性能は 5090 の 8〜9 割程度）
- メモリは 1 枚 48GB のうち空きが 27〜34GB で、今の設定は収まる。SG で指示文が長くなっても、5090 より余裕がある
