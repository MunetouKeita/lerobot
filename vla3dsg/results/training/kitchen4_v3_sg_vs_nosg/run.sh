#!/bin/bash
# 段階 2 のやり直し（4-6）: 隠し場所が 2 か所のシーン（vla3dsg_kitchen4）で、段階 1（5-2）と同じ作り方のデモ
# （手先を回さずに縁を掴む、公式に合わせた速さ・待ち）で SG なし（base）・SG あり（base_short）の 2 モデルを学習・評価する。
# 4-5 では、ワインラックの裏のボウルが最初から手首カメラに映り、SG なしでも隠し場所が分かった。隠れたボウルを
# どちらのカメラにも映らない位置へ動かし（評価の待ち 50 ステップの後に全 50 配置で確認）、隠れた 2 シーンのデモを作り直した。
# デモ: ワインラックの裏・キャビネットの裏 各 50 本（kitchen4_v3_hidden）、見えるボウル 100 本（4-5 と同じ kitchen4_v2_wide）。公式デモは混ぜない。
# このPC（GPU 1 枚）で、4-5 と同じ合計バッチ 32（8 × 勾配累積 4）、更新 6,000 回（24,000 ステップ）、学習率の減衰 6,000 回で学習する。
# 各モデルの学習の直後に、更新 1,000 回（4,000 ステップ）ごとのチェックポイントを 3 シーン × 20 本で評価し、最後のもの以外は消す。
# 最後に SG ありモデルに誤った SG（もう一方の隠し場所の裏）を与える。
#   setsid nohup vla3dsg/results/training/kitchen4_v3_sg_vs_nosg/run.sh > /dev/null 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True  # 4-3 でメモリの断片化による OOM が出たため
EXP=kitchen4_v3_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
SCENES=(hidden_rack hidden_cabinet wide)
declare -A DATA=([nosg]=kitchen4_v3_train [sg]=kitchen4_v3_train_sg)
declare -A COND=([nosg]=base [sg]=base_short)
log() { echo "$(date '+%F %T') $*" >> $REC/status.log; }
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)

train() {  # train <モデル名>
  local model=$1 out=outputs/train/${EXP}_$1 data=${DATA[$1]}
  [ -d $out/checkpoints/024000 ] && return
  # 途中のチェックポイントがあれば続きから学習する
  local resume=()
  [ -f $out/checkpoints/last/pretrained_model/train_config.json ] \
    && resume=(--resume=true --config_path=$out/checkpoints/last/pretrained_model/train_config.json)
  log "START train $model${resume:+（$(readlink $out/checkpoints/last) から再開）}"
  uv run lerobot-train --dataset.repo_id=vla3dsg/$data --dataset.root=vla3dsg/data/$data \
    --dataset.video_backend=pyav --dataset.image_transforms.enable=true \
    --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
    --policy.device=cuda --policy.action_mode=continuous --policy.norm_tag=libero --policy.norm_stats_path=$NORM \
    --policy.train_mode_vlm=lora --policy.chunk_size=10 --policy.n_action_steps=10 \
    --policy.setup_type="single franka robotic arm in libero" --policy.control_mode="delta end-effector pose" \
    --policy.image_keys='["observation.images.image","observation.images.image2"]' --policy.dtype=bfloat16 \
    --policy.num_flow_timesteps=8 --policy.gradient_checkpointing=true --policy.compile_model=false \
    --policy.freeze_embedding=true --policy.normalize_gripper=false --policy.enable_knowledge_insulation=false \
    --policy.max_sequence_length=1024 --policy.scheduler_warmup_steps=800 --policy.scheduler_decay_steps=24000 \
    --policy.normalize_language=false \
    --policy.push_to_hub=false --wandb.enable=false --output_dir=$out --job_name=${EXP}_$model --steps=24000 --batch_size=8 \
    --accelerator.gradient_accumulation.steps=4 --num_workers=4 --log_freq=200 --env_eval_freq=-1 \
    --save_checkpoint=true --save_freq=4000 --seed=1000 "${resume[@]}" >> $REC/train_$model.log 2>&1 \
    && log "DONE  train $model" || log "FAIL  train $model"
  mkdir -p $REC/$model
  cp $out/checkpoints/last/pretrained_model/train_config.json $REC/$model/ 2>/dev/null
  grep -a "step:.*loss" $REC/train_$model.log | tail -120 > $REC/$model/train_loss.log
}

evaluate() {  # evaluate <モデル名> <チェックポイント> <条件>: 3 シーン × 20 本。結果は更新回数（ステップ ÷ 4）の名前で保存する
  local model=$1 ckpt=$2 cond=$3
  local upd=$(printf "%06d" $((10#$ckpt / 4)))
  local pp=outputs/train/${EXP}_$model/checkpoints/$ckpt/pretrained_model
  for t in "${!SCENES[@]}"; do
    local name=training/$EXP/$model/step$upd/${SCENES[$t]}/$cond
    [ -f vla3dsg/results/$name/summary.json ] && continue
    [ -d $pp ] || { log "SKIP  $name（チェックポイントがない）"; continue; }
    log "START eval $name"
    uv run python vla3dsg/scripts/run_eval.py --name $name --policy-path $pp --suite vla3dsg_kitchen4 --task-ids $t \
      --n-episodes 20 --prompt-condition $cond --annotated-video > $REC/eval.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
  done
}

run_model() {  # run_model <モデル名>: 学習 → 全チェックポイントの評価 → 要約 → 最後以外のチェックポイントを消す
  local model=$1
  train $model
  for ckpt in 004000 008000 012000 016000 020000 024000; do
    evaluate $model $ckpt ${COND[$model]}
    [ $model = sg ] && [ $ckpt = 024000 ] && evaluate sg 024000 base_wrong
  done
  for upd in 001000 002000 003000 004000 005000 006000; do
    conds=(${COND[$model]}); [ $model = sg ] && [ $upd = 006000 ] && conds+=(base_wrong)
    uv run python vla3dsg/scripts/summarize_results.py --root training/$EXP/$model/step$upd --scenes "${SCENES[@]}" \
      --names "${conds[@]}" > /dev/null 2>&1 || log "FAIL  summary $model step$upd"
  done
  for ckpt in 004000 008000 012000 016000 020000; do
    local upd=$(printf "%06d" $((10#$ckpt / 4)))
    n=$(ls -d vla3dsg/results/training/$EXP/$model/step$upd/*/*/summary.json 2>/dev/null | wc -l)
    [ "$n" -eq ${#SCENES[@]} ] && rm -rf outputs/train/${EXP}_$model/checkpoints/$ckpt && log "DELETE checkpoint $model $ckpt"
  done
}

log "BEGIN（git $(git rev-parse --short HEAD)、このPC）"
run_model nosg
run_model sg
log "END"
