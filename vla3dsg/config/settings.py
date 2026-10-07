"""VLA×3DSG の設定値を一元管理する。"""

import os
from pathlib import Path

# パス
VLA3DSG_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = VLA3DSG_DIR.parent
# 実験結果。1 実験 = results/<名前>/（要約・条件は git 管理、videos/ と eval.log は管理外）
RESULTS_DIR = VLA3DSG_DIR / "results"
# テスト・計測スクリプトの使い捨て出力。git 管理外で、いつ消してもよい
TMP_DIR = VLA3DSG_DIR / "tmp"

# ヘッドレス描画と再現性のための環境変数（MuJoCo / torch の import 前に適用する）
RUNTIME_ENV = {
    "MUJOCO_GL": "egl",
    "PYOPENGL_PLATFORM": "egl",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
}


def apply_runtime_env() -> None:
    """未設定の環境変数だけを設定する。"""
    for key, value in RUNTIME_ENV.items():
        os.environ.setdefault(key, value)


# シード
SEED = 1000
EVAL_SEED = 1000

# LIBERO 環境
LIBERO_SUITES = ["libero_spatial", "libero_object", "libero_goal", "libero_10"]
LIBERO_OBS_SIZE = 360  # LeRobot の LiberoEnv 設定の既定値（縦横共通）
# reset 後の no-op ステップ数。MolmoAct2 の LIBERO 報告値は 50 で測定されている
LIBERO_NUM_STEPS_WAIT = 50
LIBERO_CONTROL_FPS = 20  # robosuite の制御周期。動画を実時間で保存するのに使う

# デモ動画のテロップ
DEMO_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"  # 日本語表示用（fonts-noto-cjk）
DEMO_HOLD_LAST_S = 1.0  # 各エピソードの最後のフレームを止めて見せる秒数
DEMO_EPISODES_PER_TASK = 1  # デモ動画に載せるエピソード数（成功率は全エピソードから計算）
# MolmoAct2 のドキュメントの評価コマンドに合わせる
LIBERO_CAMERA_NAME_MAPPING = {
    "agentview_image": "image",
    "robot0_eye_in_hand_image": "wrist_image",
}

# MolmoAct2（元の HF チェックポイント。LeRobot 形式は config.json が現在の LeRobot と非互換）
MOLMOACT2_CHECKPOINT = "allenai/MolmoAct2-LIBERO"
MOLMOACT2_NORM_TAG = "libero"
MOLMOACT2_DTYPE = "float32"  # ドキュメントの元チェックポイント用評価コマンドに合わせる


def molmoact2_eval_args(suite: str, task_ids: list[int], n_episodes: int, output_dir: Path) -> list[str]:
    """lerobot-eval の共通引数（環境タイプ libero_vla3dsg、シード固定）。"""
    return [
        "--env.discover_packages_path=vla3dsg.envs",
        "--env.type=libero_vla3dsg",
        f"--env.task={suite}",
        f"--env.task_ids={task_ids}",
        f"--env.num_steps_wait={LIBERO_NUM_STEPS_WAIT}",
        "--env.camera_name_mapping="
        + "{" + ",".join(f'"{k}":"{v}"' for k, v in LIBERO_CAMERA_NAME_MAPPING.items()) + "}",
        "--policy.type=molmoact2",
        f"--policy.checkpoint_path={MOLMOACT2_CHECKPOINT}",
        f"--policy.norm_tag={MOLMOACT2_NORM_TAG}",
        "--policy.inference_action_mode=continuous",
        f"--policy.dtype={MOLMOACT2_DTYPE}",
        "--policy.enable_inference_cuda_graph=true",
        "--policy.device=cuda",
        "--policy.per_episode_seed=true",
        f"--policy.eval_seed={EVAL_SEED}",
        "--eval.batch_size=1",
        f"--eval.n_episodes={n_episodes}",
        f"--seed={SEED}",
        f"--output_dir={output_dir}",
    ]
