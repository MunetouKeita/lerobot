#!/bin/bash
# 段階 2 のやり直し（4-5）: 隠し場所が 2 か所のシーン（vla3dsg_kitchen4）で、段階 1（5-2）と同じ作り方のデモ
# （手先を回さずに縁を掴む、公式に合わせた速さ・待ち）で SG なし（base）・SG あり（base_short）の 2 モデルを学習・評価する。
# デモ: ワインラックの裏・キャビネットの裏 各 50 本、見えるボウル 100 本（4-4 と同じ構成）。公式デモは混ぜない。
# 6000ada の GPU 4 枚（GPUS_OVERRIDE="0 1" で 2 枚）で順に学習（合計バッチ 32、更新 6,000 回、学習率の減衰 6,000 回）し、
# 更新 1,000 回ごとのチェックポイントを 3 シーン × 20 本で評価する。最後に SG ありモデルに誤った SG（もう一方の隠し場所の裏）を与える。
# データセットは手元で作って送っておく:
#   setsid nohup vla3dsg/results/training/kitchen4_v2_sg_vs_nosg/run.sh > vla3dsg/results/training/kitchen4_v2_sg_vs_nosg/run.log 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
EXP=kitchen4_v2_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GPUS=(${GPUS_OVERRIDE:-0 1 2 3})
BATCH=$((32 / ${#GPUS[@]}))
SCENES=(hidden_rack hidden_cabinet wide)
STEPS=(001000 002000 003000 004000 005000 006000)
declare -A DATA=([nosg]=kitchen4_v2_train [sg]=kitchen4_v2_train_sg)
declare -A COND=([nosg]=base [sg]=base_short)
log() { echo "$(date '+%F %T') $*" >> $REC/status.log; }
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)

train() {  # train <モデル名>
  local model=$1 out=outputs/train/${EXP}_$1 data=${DATA[$1]}
  [ -d $out/checkpoints/006000 ] && return
  # 途中のチェックポイントがあれば続きから学習する（GPU の枚数を変えても合計バッチは 32 のまま）
  local resume=()
  [ -f $out/checkpoints/last/pretrained_model/train_config.json ] \
    && resume=(--resume=true --config_path=$out/checkpoints/last/pretrained_model/train_config.json --parallelism.dp_replicate=${#GPUS[@]})
  log "START train $model（GPU ${GPUS[*]}、1 枚あたりバッチ $BATCH${resume:+、$(readlink $out/checkpoints/last) から再開}）"
  CUDA_VISIBLE_DEVICES=$(IFS=,; echo "${GPUS[*]}") uv run --no-sync accelerate launch --multi_gpu --num_processes=${#GPUS[@]} \
    --mixed_precision=no -m lerobot.scripts.lerobot_train --dataset.repo_id=vla3dsg/$data --dataset.root=vla3dsg/data/$data \
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
    --policy.push_to_hub=false --wandb.enable=false --output_dir=$out --job_name=${EXP}_$model --steps=6000 --batch_size=$BATCH \
    --accelerator.gradient_accumulation.steps=1 --num_workers=4 --log_freq=50 --env_eval_freq=-1 \
    --save_checkpoint=true --save_freq=1000 --seed=1000 "${resume[@]}" >> $REC/train_$model.log 2>&1 \
    && log "DONE  train $model" || log "FAIL  train $model"
  mkdir -p $REC/$model
  cp $out/checkpoints/last/pretrained_model/train_config.json $REC/$model/ 2>/dev/null
  grep -a "step:.*loss" $REC/train_$model.log | tail -240 > $REC/$model/train_loss.log
}

jobs_list() {  # <モデル> <ステップ> <シーン番号> <条件>
  for s in "${STEPS[@]}"; do
    for model in nosg sg; do
      for t in "${!SCENES[@]}"; do echo "$model $s $t ${COND[$model]}"; done
    done
  done
  for t in "${!SCENES[@]}"; do echo "sg 006000 $t base_wrong"; done
}

eval_worker() {
  local w=$1 gpu=${GPUS[$1]} i=0
  while read -r model s t cond; do
    if (( i++ % ${#GPUS[@]} == w )); then
      local name=training/$EXP/$model/step$s/${SCENES[$t]}/$cond ckpt=outputs/train/${EXP}_$model/checkpoints/$s/pretrained_model
      [ -f vla3dsg/results/$name/summary.json ] && continue
      [ -d $ckpt ] || { log "SKIP  $name（チェックポイントがない）"; continue; }
      log "START eval gpu$gpu $name"
      CUDA_VISIBLE_DEVICES=$gpu uv run --no-sync python vla3dsg/scripts/run_eval.py --name $name --policy-path $ckpt \
        --suite vla3dsg_kitchen4 --task-ids $t --n-episodes 20 --prompt-condition $cond --annotated-video \
        > $REC/eval_slot$w.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
    fi
  done < <(jobs_list)
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
train nosg
train sg
for w in "${!GPUS[@]}"; do eval_worker $w & done
wait
for model in nosg sg; do
  for s in "${STEPS[@]}"; do
    conds=(${COND[$model]}); [ $model = sg ] && [ $s = 006000 ] && conds+=(base_wrong)
    uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/$model/step$s --scenes "${SCENES[@]}" \
      --names "${conds[@]}" > /dev/null 2>&1 || log "FAIL  summary $model step$s"
  done
done
log "DONE  summary"
for model in nosg sg; do
  for s in "${STEPS[@]}"; do
    [ $s = 006000 ] && continue
    n=$(ls -d vla3dsg/results/training/$EXP/$model/step$s/*/*/summary.json 2>/dev/null | wc -l)
    [ "$n" -eq ${#SCENES[@]} ] && rm -rf outputs/train/${EXP}_$model/checkpoints/$s && log "DELETE checkpoint $model $s"
  done
done
log "END"
