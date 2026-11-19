#!/bin/bash
# 段階 1（5-3 の追加）: SG ありで学習したモデル（更新 3,000 回）に、誤った SG（norel_wrong: 位置関係なし＋もう一方のボウルの関係を対象の名前で書いた SG）
# を与えて評価する。SG の中身を読んでボウルを選んでいるかの対照。6000ada の GPU 4 枚（1 枚に 1 つずつ）:
#   setsid nohup vla3dsg/results/training/spatial_v2_sg_vs_nosg/run_wrong.sh > vla3dsg/results/training/spatial_v2_sg_vs_nosg/run_wrong.log 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
EXP=spatial_v2_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GPUS=(${GPUS_OVERRIDE:-0 1 2 3})
SCENES=(center_b1 center_b2 drawer_b1 drawer_b2 near_box_b1 near_box_b2 on_box_b1 on_box_b2 on_ramekin_b1 on_ramekin_b2)
CKPT=outputs/train/${EXP}_sg/checkpoints/003000/pretrained_model
log() { echo "$(date '+%F %T') $*" >> $REC/status_wrong.log; }

worker() {  # worker <スロット番号>
  local w=$1 gpu=${GPUS[$1]}
  for t in "${!SCENES[@]}"; do
    (( t % ${#GPUS[@]} == w )) || continue
    local name=training/$EXP/sg/step003000/${SCENES[$t]}/norel_wrong
    [ -f vla3dsg/results/$name/summary.json ] && continue
    log "START eval gpu$gpu $name"
    CUDA_VISIBLE_DEVICES=$gpu uv run --no-sync python vla3dsg/scripts/run_eval.py --name $name --policy-path $CKPT \
      --suite vla3dsg_spatial --task-ids $t --n-episodes 20 --prompt-condition norel_wrong --annotated-video \
      > $REC/eval_wrong_slot$w.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
  done
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
for w in "${!GPUS[@]}"; do worker $w & done
wait
uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/sg/step003000 --scenes "${SCENES[@]}" \
  --names norel_short norel norel_wrong > /dev/null 2>&1 && log "DONE  summary" || log "FAIL  summary"
log "END"
