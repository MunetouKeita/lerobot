#!/bin/bash
# 4-2（sg_vs_nosg）で、ワインラックの裏へ行く癖がついた対策。見えるボウルのデモを増やし（wide・decoy_visible を各 50 本追加）、
# 標準のシーンの公式デモ 49 本を混ぜたデータで、SG なし・SG ありの 2 モデルを 4-2 と同じ設定で学習し、同じ評価をする。
# 学習前の評価は 4-2 のものを使う。
# セッションが切れても最後まで進み、各工程の開始・終了を status.log に残す。
#   setsid nohup vla3dsg/results/training/balanced_sg_vs_nosg/run.sh > /dev/null 2>&1 &
cd /home/common/github/lerobot
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
# データが増えて、4-2 の設定のままではメモリの断片化で OOM になった（37 ステップ目）ため
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
EXP=balanced_sg_vs_nosg
REC=vla3dsg/results/training/$EXP
STATUS=$REC/status.log
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $STATUS; }
run() {  # run <工程名> <コマンド...>: 失敗しても次の工程へ進む
  local stage=$1; shift
  log "START $stage"
  if "$@" >> $REC/run.log 2>&1; then log "DONE  $stage"; else log "FAIL  $stage (exit $?)"; fi
}
eval_one() {  # eval_one <結果の名前> <プロンプト条件> <policy-path または base> <スイート> <タスクID...>
  local name=$1 cond=$2 pp=() suite=$4 && [ "$3" != base ] && pp=(--policy-path "$3")
  shift 4
  [ -e vla3dsg/results/$name ] && return  # 再実行したときは済んだ評価を飛ばす
  run "eval $name" uv run python vla3dsg/scripts/run_eval.py --name $name --suite $suite --task-ids "$@" --n-episodes 20 \
    --prompt-condition $cond --annotated-video "${pp[@]}"
}
evaluate() {  # evaluate <結果の名前> <プロンプト条件> <policy-path>
  eval_one $1/train_scenes $2 $3 vla3dsg_goal_train 0 1 2 3  # 学習用シーンの評価用の初期状態（学習のデモとは別の配置）
  eval_one $1/goal $2 $3 vla3dsg_goal 0 1 2 3  # 2-2 と同じ 4 シーン
  eval_one $1/layout_far $2 $3 vla3dsg_goal_layout 1 2 5  # 2-3 の遠いボウル（4-1 と比べる）
}
NORM=$(ls ~/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)
train() {  # train <モデル名> <データセット名> <追加の引数...>: 有効バッチ 32（8 × 勾配累積 4）、12,000 ステップ ＝ 更新 3,000 回
  local model=$1 data=$2 out=outputs/train/${EXP}_$1
  shift 2
  [ -d $out/checkpoints/012000 ] && return
  run "train $model" uv run lerobot-train --dataset.repo_id=vla3dsg/$data --dataset.root=vla3dsg/data/$data \
    --dataset.video_backend=pyav --dataset.image_transforms.enable=true \
    --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
    --policy.device=cuda --policy.action_mode=continuous --policy.norm_tag=libero --policy.norm_stats_path=$NORM \
    --policy.train_mode_vlm=lora --policy.chunk_size=10 --policy.n_action_steps=10 \
    --policy.setup_type="single franka robotic arm in libero" --policy.control_mode="delta end-effector pose" \
    --policy.image_keys='["observation.images.image","observation.images.image2"]' --policy.dtype=bfloat16 \
    --policy.num_flow_timesteps=8 --policy.gradient_checkpointing=true --policy.compile_model=false \
    --policy.freeze_embedding=true --policy.normalize_gripper=false --policy.enable_knowledge_insulation=false \
    --policy.max_sequence_length=1024 --policy.scheduler_warmup_steps=800 --policy.scheduler_decay_steps=12000 \
    --policy.push_to_hub=false --wandb.enable=false --output_dir=$out --job_name=${EXP}_$model --steps=12000 --batch_size=8 \
    --accelerator.gradient_accumulation.steps=4 --num_workers=4 --log_freq=100 --env_eval_freq=-1 \
    --save_checkpoint=true --save_freq=4000 --seed=1000 "$@"
  mkdir -p $REC/$model
  cp $out/checkpoints/last/pretrained_model/train_config.json $REC/$model/ 2>/dev/null
  # run.log には 2 モデル分の損失が続けて入るため、学習の直後にこのモデルの分を切り出す
  grep -a "step:.*loss" $REC/run.log | tail -120 > $REC/$model/train_loss.log
  for s in 004000 012000; do  # 更新 1,000 回（4,000 ステップ）と 3,000 回
    [ -d $out/checkpoints/$s ] && evaluate training/$EXP/$model/step$s ${COND[$model]} $out/checkpoints/$s/pretrained_model
  done
}
declare -A COND=([nosg]=base [sg]=base_short)

data() {  # data <工程名> <作るデータセット> <コマンド...>: データセットがなければ作る
  local stage=$1 name=$2; shift 2
  [ -d vla3dsg/data/$name ] || run "$stage" "$@"
}
merge() {  # merge <作るデータセット> <元のデータセット...>
  local name=$1; shift
  local ids=() roots=()
  for d in "$@"; do ids+=("'vla3dsg/$d'"); roots+=("'vla3dsg/data/$d'"); done
  data "merge $name" $name uv run lerobot-edit-dataset --new_repo_id vla3dsg/$name --new_root vla3dsg/data/$name \
    --operation.type merge --operation.repo_ids "[$(IFS=,; echo "${ids[*]}")]" --operation.roots "[$(IFS=,; echo "${roots[*]}")]"
}

log "BEGIN（git $(git rev-parse --short HEAD)）"
# データ: 4-2 の 200 本 ＋ 見えるボウルの追加 100 本（前の生成とシードが重ならないよう 200000 から）＋ 公式デモ 49 本
data "demos goal_train_more" goal_train_more uv run python vla3dsg/scripts/generate_demos.py --name goal_train_more \
  --suite vla3dsg_goal_train --task-ids 0 3 --n-episodes 50 --seed-start 200000
data "sg goal_train_more_sg" goal_train_more_sg uv run python vla3dsg/scripts/make_sg_dataset.py --src goal_train_more --name goal_train_more_sg
data "official official_bowl" official_bowl uv run python vla3dsg/scripts/extract_official_demos.py --name official_bowl
data "official official_bowl_sg" official_bowl_sg uv run python vla3dsg/scripts/extract_official_demos.py --name official_bowl_sg \
  --condition base_short --scene vla3dsg_goal:0
merge goal_balanced goal_train goal_train_more official_bowl
merge goal_balanced_sg goal_train_sg goal_train_more_sg official_bowl_sg
# SG あり: 指示文は make_sg_dataset.py で正規化済みのため、学習でも正規化を切る（評価と同じ）
train sg goal_balanced_sg --policy.normalize_language=false
train nosg goal_balanced
run "summary" uv run python $REC/summarize.py
log "END"
