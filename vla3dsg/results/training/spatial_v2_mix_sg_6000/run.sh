#!/bin/bash
# 段階 1（5-5）: 公式デモを混ぜた SG ありの学習（5-4 の sg と同じデータ）を、更新 6,000 回に延ばす（5-4 では 3,000 回でもまだ上がっていた）。
# 学習率のスケジュールはウォームアップ 200 回・減衰 6,000 回。それ以外は 5-4 と同じ。
# SG なしの比較は同じモデルで SG を外す（norel）。公式の指示文の力（base）と、誤った SG（norel_wrong）も最後のチェックポイントで評価する。
# 6000ada の GPU 4 枚（GPUS_OVERRIDE="0 1" で 2 枚）。更新 1,000 回ごとのチェックポイントを ③（norel_short）で評価し、済んだ途中のものは消す:
#   setsid nohup vla3dsg/results/training/spatial_v2_mix_sg_6000/run.sh > vla3dsg/results/training/spatial_v2_mix_sg_6000/run.log 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
EXP=spatial_v2_mix_sg_6000
REC=vla3dsg/results/training/$EXP
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GPUS=(${GPUS_OVERRIDE:-0 1 2 3})
BATCH=$((32 / ${#GPUS[@]}))  # 合計のバッチを 32 にそろえる（2 枚なら 1 枚あたり 16）
SCENES=(center_b1 center_b2 drawer_b1 drawer_b2 near_box_b1 near_box_b2 on_box_b1 on_box_b2 on_ramekin_b1 on_ramekin_b2)
STEPS=(001000 002000 003000 004000 005000 006000)
FINAL_CONDS=(norel base norel_wrong)
DATA=spatial_v2_mix_sg
OUT=outputs/train/$EXP
log() { echo "$(date '+%F %T') $*" >> $REC/status.log; }
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)

train() {
  [ -d $OUT/checkpoints/006000 ] && return
  log "START train（GPU ${GPUS[*]}、1 枚あたりバッチ $BATCH）"
  CUDA_VISIBLE_DEVICES=$(IFS=,; echo "${GPUS[*]}") uv run --no-sync accelerate launch --multi_gpu --num_processes=${#GPUS[@]} \
    --mixed_precision=no -m lerobot.scripts.lerobot_train --dataset.repo_id=vla3dsg/$DATA --dataset.root=vla3dsg/data/$DATA \
    --dataset.video_backend=pyav --dataset.image_transforms.enable=true \
    --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
    --policy.device=cuda --policy.action_mode=continuous --policy.norm_tag=libero --policy.norm_stats_path=$NORM \
    --policy.train_mode_vlm=lora --policy.chunk_size=10 --policy.n_action_steps=10 \
    --policy.setup_type="single franka robotic arm in libero" --policy.control_mode="delta end-effector pose" \
    --policy.image_keys='["observation.images.image","observation.images.image2"]' --policy.dtype=bfloat16 \
    --policy.num_flow_timesteps=8 --policy.gradient_checkpointing=true --policy.compile_model=false \
    --policy.freeze_embedding=true --policy.normalize_gripper=false --policy.enable_knowledge_insulation=false \
    --policy.max_sequence_length=1024 --policy.scheduler_warmup_steps=200 --policy.scheduler_decay_steps=6000 \
    --policy.normalize_language=false \
    --policy.push_to_hub=false --wandb.enable=false --output_dir=$OUT --job_name=$EXP --steps=6000 --batch_size=$BATCH \
    --accelerator.gradient_accumulation.steps=1 --num_workers=4 --log_freq=50 --env_eval_freq=-1 \
    --save_checkpoint=true --save_freq=1000 --seed=1000 > $REC/train.log 2>&1 \
    && log "DONE  train" || { log "FAIL  train"; log "END"; exit 1; }
  cp $OUT/checkpoints/last/pretrained_model/train_config.json $REC/ 2>/dev/null
  grep -a "step:.*loss" $REC/train.log | tail -240 > $REC/train_loss.log
}

jobs_list() {  # <ステップ> <シーン番号> <条件>
  for s in "${STEPS[@]}"; do for t in "${!SCENES[@]}"; do echo "$s $t norel_short"; done; done
  for c in "${FINAL_CONDS[@]}"; do for t in "${!SCENES[@]}"; do echo "006000 $t $c"; done; done
}

eval_worker() {
  local w=$1 gpu=${GPUS[$1]} i=0
  while read -r s t cond; do
    if (( i++ % ${#GPUS[@]} == w )); then
      local name=training/$EXP/step$s/${SCENES[$t]}/$cond ckpt=$OUT/checkpoints/$s/pretrained_model
      [ -f vla3dsg/results/$name/summary.json ] && continue
      [ -d $ckpt ] || { log "SKIP  $name（チェックポイントがない）"; continue; }
      log "START eval gpu$gpu $name"
      CUDA_VISIBLE_DEVICES=$gpu uv run --no-sync python vla3dsg/scripts/run_eval.py --name $name --policy-path $ckpt \
        --suite vla3dsg_spatial --task-ids $t --n-episodes 20 --prompt-condition $cond --annotated-video \
        > $REC/eval_slot$w.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
    fi
  done < <(jobs_list)
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
train
for w in "${!GPUS[@]}"; do eval_worker $w & done
wait
for s in "${STEPS[@]}"; do
  conds=(norel_short); [ $s = 006000 ] && conds+=("${FINAL_CONDS[@]}")
  uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/step$s --scenes "${SCENES[@]}" \
    --names "${conds[@]}" > /dev/null 2>&1 || log "FAIL  summary step$s"
done
log "DONE  summary"
for s in "${STEPS[@]}"; do
  [ $s = 006000 ] && continue
  n=$(ls -d vla3dsg/results/training/$EXP/step$s/*/*/summary.json 2>/dev/null | wc -l)
  [ "$n" -eq ${#SCENES[@]} ] && rm -rf $OUT/checkpoints/$s && log "DELETE checkpoint $s"
done
log "END"
