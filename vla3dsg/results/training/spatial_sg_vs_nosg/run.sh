#!/bin/bash
# 段階 1（5 節）: vla3dsg_spatial のデモ（5 配置 × 正解のボウル 1/2 × 30 本）で、指示文が関係なし（norel）の SG なしモデルと、
# 関係なし＋SG（norel_short）の SG ありモデルを、6000ada の GPU 4 枚で順に学習し（accelerate で 4 枚に分け、1 枚あたりバッチ 8、
# 合計 32・勾配累積なし）、更新 500 回ごとのチェックポイントを評価する（1 枚に 1 つずつ）。評価が済んだ途中のチェックポイントは消す。
# 各工程を status.log に記録し、セッションが切れても進む。データセット（data/spatial_train_norel・spatial_train_sg）は手元で作って送っておく:
#   setsid nohup vla3dsg/results/training/spatial_sg_vs_nosg/run.sh > vla3dsg/results/training/spatial_sg_vs_nosg/run.log 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
EXP=spatial_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GPUS=(0 1 2 3)
EVALS_PER_GPU=1  # 評価 1 つ約 26GB（48GB の 1 枚に 1 つ）
SCENES=(center_b1 center_b2 drawer_b1 drawer_b2 near_box_b1 near_box_b2 on_box_b1 on_box_b2 on_ramekin_b1 on_ramekin_b2)
STEPS=(000500 001000 001500 002000 002500 003000)
declare -A DATA=([nosg]=spatial_train_norel [sg]=spatial_train_sg)
declare -A COND=([nosg]=norel [sg]=norel_short)
# 最後のチェックポイントだけ、もう一方の条件でも評価する（SG なしは人が書いた関係 base、SG ありは SG を外した norel）
declare -A COND_FINAL=([nosg]=base [sg]=norel)
log() { echo "$(date '+%F %T') $*" >> $REC/status.log; }
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)

train() {  # train <モデル名>: 更新 3,000 回（4 枚 × バッチ 8 ＝ 32）。学習率のスケジュールは 4-3・4-4 と同じ（ウォームアップ 200 回、減衰 3,000 回）
  local model=$1 out=outputs/train/${EXP}_$1 data=${DATA[$1]}
  [ -d $out/checkpoints/003000 ] && return
  log "START train $model"
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
    --policy.max_sequence_length=1024 --policy.scheduler_warmup_steps=200 --policy.scheduler_decay_steps=3000 \
    --policy.normalize_language=false \
    --policy.push_to_hub=false --wandb.enable=false --output_dir=$out --job_name=${EXP}_$model --steps=3000 --batch_size=8 \
    --accelerator.gradient_accumulation.steps=1 --num_workers=4 --log_freq=50 --env_eval_freq=-1 \
    --save_checkpoint=true --save_freq=500 --seed=1000 > $REC/train_$model.log 2>&1 \
    && log "DONE  train $model" || log "FAIL  train $model"
  mkdir -p $REC/$model
  cp $out/checkpoints/last/pretrained_model/train_config.json $REC/$model/ 2>/dev/null
  grep -a "step:.*loss" $REC/train_$model.log | tail -120 > $REC/$model/train_loss.log
}

# 評価の一覧: <モデル> <ステップ> <シーン番号> <条件>
jobs_list() {
  for s in "${STEPS[@]}"; do
    for model in nosg sg; do
      for t in "${!SCENES[@]}"; do echo "$model $s $t ${COND[$model]}"; done
    done
  done
  for model in nosg sg; do
    for t in "${!SCENES[@]}"; do echo "$model 003000 $t ${COND_FINAL[$model]}"; done
  done
}

eval_worker() {  # eval_worker <スロット番号>: 評価の一覧のうち、スロット番号の分を順に行う
  local w=$1 nslots=$((${#GPUS[@]} * EVALS_PER_GPU)) gpu=${GPUS[$(($1 / EVALS_PER_GPU))]} i=0
  while read -r model s t cond; do
    if (( i++ % nslots == w )); then
      local name=training/$EXP/$model/step$s/${SCENES[$t]}/$cond ckpt=outputs/train/${EXP}_$model/checkpoints/$s/pretrained_model
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
train nosg
train sg
for w in $(seq 0 $((${#GPUS[@]} * EVALS_PER_GPU - 1))); do eval_worker $w & done
wait
log "START summary"
for model in nosg sg; do
  for s in "${STEPS[@]}"; do
    conds=(${COND[$model]}); [ $s = 003000 ] && conds+=(${COND_FINAL[$model]})
    uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/$model/step$s --scenes "${SCENES[@]}" \
      --names "${conds[@]}" > /dev/null 2>&1 || log "FAIL  summary $model step$s"
  done
done
log "DONE  summary"
# 評価が済んだ途中のチェックポイントを消す（1 つ 18GB。最後の 003000 は残す）
for model in nosg sg; do
  for s in "${STEPS[@]}"; do
    [ $s = 003000 ] && continue
    n=$(ls -d vla3dsg/results/training/$EXP/$model/step$s/*/*/summary.json 2>/dev/null | wc -l)
    [ "$n" -eq ${#SCENES[@]} ] && rm -rf outputs/train/${EXP}_$model/checkpoints/$s && log "DELETE checkpoint $model $s"
  done
done
log "END"
