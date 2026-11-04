#!/bin/bash
# 見えるボウルのデモ（goal_train の wide・decoy_visible、各 50 本）で SG なしの追加学習を行い、前後を評価する。
# セッションが切れても最後まで進み、各工程の開始・終了を status.log に残す。
#   setsid nohup vla3dsg/results/training/visible_nosg/run.sh > /dev/null 2>&1 &
cd /home/common/github/lerobot
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
NAME=visible_nosg
REC=vla3dsg/results/training/$NAME
OUT=outputs/train/$NAME
STATUS=$REC/status.log
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $STATUS; }
run() {  # run <工程名> <コマンド...>: 失敗しても次の工程へ進む
  local stage=$1; shift
  log "START $stage"
  if "$@" >> $REC/run.log 2>&1; then log "DONE  $stage"; else log "FAIL  $stage (exit $?)"; fi
}
evaluate() {  # evaluate <結果の名前> <policy-path または base>
  local pp=() && [ "$2" != base ] && pp=(--policy-path "$2")
  run "eval $1 学習用シーン" uv run python vla3dsg/scripts/run_eval.py --name $1/train_scenes --suite vla3dsg_goal_train --task-ids 0 3 --n-episodes 20 --annotated-video "${pp[@]}"
  [ "$2" = base ] && return  # 遠いボウル・標準の学習前の値は zeroshot/ にある
  run "eval $1 遠いボウル" uv run python vla3dsg/scripts/run_eval.py --name $1/layout_far --suite vla3dsg_goal_layout --task-ids 1 2 5 --n-episodes 20 --annotated-video "${pp[@]}"
  run "eval $1 標準" uv run python vla3dsg/scripts/run_eval.py --name $1/standard --suite vla3dsg_goal --task-ids 0 --n-episodes 20 --annotated-video "${pp[@]}"
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
# 学習前: 学習用シーンの評価用の初期状態（学習のデモとは別の配置）
[ -e vla3dsg/results/training/$NAME/before ] || evaluate training/$NAME/before base

# 学習: 有効バッチ 32（8 × 勾配累積 4）、12,000 ステップ ＝ 更新 3,000 回。学習率の予定もステップ（マイクロバッチ）で数える
EPS="[$(python3 -c 'print(",".join(map(str, [*range(0, 50), *range(150, 200)])))')]"  # task 0（wide）と 3（decoy_visible）
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)
run "train" uv run lerobot-train --dataset.repo_id=vla3dsg/goal_train --dataset.root=vla3dsg/data/goal_train --dataset.episodes="$EPS" \
  --dataset.video_backend=pyav --dataset.image_transforms.enable=true \
  --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
  --policy.device=cuda --policy.action_mode=continuous --policy.norm_tag=libero --policy.norm_stats_path=$NORM \
  --policy.train_mode_vlm=lora --policy.chunk_size=10 --policy.n_action_steps=10 \
  --policy.setup_type="single franka robotic arm in libero" --policy.control_mode="delta end-effector pose" \
  --policy.image_keys='["observation.images.image","observation.images.image2"]' --policy.dtype=bfloat16 \
  --policy.num_flow_timesteps=8 --policy.gradient_checkpointing=true --policy.compile_model=false \
  --policy.freeze_embedding=true --policy.normalize_gripper=false --policy.enable_knowledge_insulation=false \
  --policy.scheduler_warmup_steps=800 --policy.scheduler_decay_steps=12000 \
  --policy.push_to_hub=false --wandb.enable=false --output_dir=$OUT --job_name=$NAME --steps=12000 --batch_size=8 \
  --accelerator.gradient_accumulation.steps=4 --num_workers=4 --log_freq=100 --env_eval_freq=-1 \
  --save_checkpoint=true --save_freq=4000 --seed=1000
cp $OUT/checkpoints/last/pretrained_model/train_config.json $REC/ 2>/dev/null
grep -a "step:.*loss" $REC/run.log | tail -200 > $REC/train_loss.log

# 学習後: 更新 1,000 回（4,000 ステップ）と 3,000 回（12,000 ステップ）
for s in 004000 012000; do
  [ -d $OUT/checkpoints/$s ] && evaluate training/$NAME/step$s $OUT/checkpoints/$s/pretrained_model
done
run "summary" uv run python vla3dsg/results/training/$NAME/summarize.py
log "END"
