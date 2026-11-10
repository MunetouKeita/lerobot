#!/bin/bash
# 5-1: vla3dsg_spatial の 10 タスク × 3 条件（base・norel・norel_short）を学習前のモデルで評価する（学習サーバの GPU 4 枚）。
# 各 GPU が (タスク, 条件) の組を順に受け持つ。各工程を status.log に記録し、セッションが切れても進む。
#   setsid nohup vla3dsg/results/zeroshot/spatial/run.sh > vla3dsg/results/zeroshot/spatial/run.log 2>&1 &
cd "$(dirname "$0")/../../../.." || exit 1
REC=vla3dsg/results/zeroshot/spatial
export PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=$HOME/environments/lerobot-vla3dsg
export __EGL_VENDOR_LIBRARY_FILENAMES=$HOME/.config/egl/10_nvidia.json
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
SCENES=(center_b1 center_b2 drawer_b1 drawer_b2 near_box_b1 near_box_b2 on_box_b1 on_box_b2 on_ramekin_b1 on_ramekin_b2)
CONDS=(base norel norel_short)
GPUS=(0 1 2 3)
log() { echo "$(date '+%F %T') $*" >> $REC/status.log; }

worker() {  # worker <GPU の番号（GPUS の添字）>
  local g=$1 i=0
  for c in "${CONDS[@]}"; do
    for t in "${!SCENES[@]}"; do
      if (( i++ % ${#GPUS[@]} == g )); then
        local name=zeroshot/spatial/${SCENES[$t]}/$c
        [ -f vla3dsg/results/$name/summary.json ] && continue
        log "START gpu${GPUS[$g]} $name"
        CUDA_VISIBLE_DEVICES=${GPUS[$g]} uv run --no-sync python vla3dsg/scripts/run_eval.py --name $name \
          --suite vla3dsg_spatial --task-ids $t --n-episodes 20 --prompt-condition $c --annotated-video \
          > $REC/eval_gpu${GPUS[$g]}.log 2>&1 && log "DONE  $name" || log "FAIL  $name"
      fi
    done
  done
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
for g in "${!GPUS[@]}"; do worker $g & done
wait
log "START summary"
uv run --no-sync python vla3dsg/scripts/summarize_results.py --root zeroshot/spatial --scenes "${SCENES[@]}" \
  --names "${CONDS[@]}" && log "DONE  summary" || log "FAIL  summary"
log "END"
