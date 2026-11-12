#!/bin/bash
# 5-2 の追加の評価: 最大ステップ数を 280 → 560 に延ばし、学習後の失敗が時間切れによるものかを確かめる。
# 更新 3,000 回の SG なし（norel）・SG あり（norel_short）と、比較のため学習前のモデル（base）を、10 タスク × 20 エピソードで評価する（6000ada の GPU 4 枚）。
#   setsid nohup vla3dsg/results/training/spatial_sg_vs_nosg/run_long.sh > vla3dsg/results/training/spatial_sg_vs_nosg/run_long.log 2>&1 < /dev/null &
cd "$(dirname "$0")/../../../.." || exit 1
EXP=spatial_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GPUS=(0 1 2 3)
MAX=560
SCENES=(center_b1 center_b2 drawer_b1 drawer_b2 near_box_b1 near_box_b2 on_box_b1 on_box_b2 on_ramekin_b1 on_ramekin_b2)
log() { echo "$(date '+%F %T') $*" >> $REC/status_long.log; }

jobs_list() {  # <モデル> <シーン番号> <条件>（学習したモデルを先に）
  for model in sg nosg; do
    for t in "${!SCENES[@]}"; do echo "$model $t $([ $model = sg ] && echo norel_short || echo norel)"; done
  done
  for t in "${!SCENES[@]}"; do echo "zeroshot $t base"; done
}

worker() {
  local g=$1 i=0
  while read -r model t cond; do
    if (( i++ % ${#GPUS[@]} == g )); then
      local name opt=()
      if [ $model = zeroshot ]; then
        name=training/$EXP/zeroshot/max$MAX/${SCENES[$t]}/$cond
      else
        name=training/$EXP/$model/step003000_max$MAX/${SCENES[$t]}/$cond
        opt=(--policy-path outputs/train/${EXP}_$model/checkpoints/003000/pretrained_model)
      fi
      [ -f vla3dsg/results/$name/summary.json ] && continue
      log "START gpu${GPUS[$g]} $name"
      CUDA_VISIBLE_DEVICES=${GPUS[$g]} uv run --no-sync python vla3dsg/scripts/run_eval.py --name $name "${opt[@]}" \
        --suite vla3dsg_spatial --task-ids $t --n-episodes 20 --prompt-condition $cond --max-steps $MAX --annotated-video \
        > $REC/eval_long_gpu${GPUS[$g]}.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
    fi
  done < <(jobs_list)
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
for g in "${!GPUS[@]}"; do worker $g & done
wait
log "START summary"
uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/sg/step003000_max$MAX --scenes "${SCENES[@]}" --names norel_short > /dev/null 2>&1
uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/nosg/step003000_max$MAX --scenes "${SCENES[@]}" --names norel > /dev/null 2>&1
uv run --no-sync python vla3dsg/scripts/summarize_results.py --root training/$EXP/zeroshot/max$MAX --scenes "${SCENES[@]}" --names base > /dev/null 2>&1
log "DONE  summary"
log "END"
