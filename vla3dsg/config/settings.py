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
# 自作スイート（BDDL・初期状態・tasks.json）。envs/custom_suites.py が登録する
CUSTOM_TASKS_DIR = VLA3DSG_DIR / "custom_tasks"

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
LIBERO_OBS_SIZE = 360  # LeRobot の LiberoEnv 設定の既定値（縦横共通）
# reset 後の no-op ステップ数。MolmoAct2 の LIBERO 報告値は 50 で測定されている
LIBERO_NUM_STEPS_WAIT = 50
LIBERO_CONTROL_FPS = 20  # robosuite の制御周期。動画を実時間で保存するのに使う
# 評価動画の保存（run_eval.py --annotated-video 時）: 各タスクの先頭 N 本と、それ以降の失敗エピソード
VIDEO_SAVE_FIRST_N = 10
VIDEO_SAVE_FAILURES = True

# デモ動画のテロップ
DEMO_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"  # 日本語表示用（fonts-noto-cjk）
DEMO_HOLD_LAST_S = 1.0  # 各エピソードの最後のフレームを止めて見せる秒数
DEMO_EPISODES_PER_TASK = 1  # デモ動画に載せるエピソード数（成功率は全エピソードから計算）
# MolmoAct2 のドキュメントの評価コマンドに合わせる
LIBERO_CAMERA_NAME_MAPPING = {
    "agentview_image": "image",
    "robot0_eye_in_hand_image": "wrist_image",
}

# 自作タスクの生成（scripts/make_custom_task.py）
CUSTOM_TASK_MAX_STEPS = 300  # libero_spatial・object は 280、goal は 300
CUSTOM_TASK_N_INIT = 50  # 初期状態の数（元の LIBERO と同じ）
CUSTOM_TASK_STABILITY_STEPS = 50  # 落ち着いた後、さらに何もしないで進めて動きを確かめるステップ数
CUSTOM_TASK_MAX_SETTLE_MOVE = 0.02  # m。配置の直後から落ち着くまでに水平方向にこれ以上動いた配置は除く（押し出し・転倒）
CUSTOM_TASK_MAX_DRIFT = 0.005  # m。落ち着いた後にこれ以上動く配置は除く
CUSTOM_TASK_MAX_TRIALS_FACTOR = 4  # 有効な配置が n_init の何倍の試行で集まらなければ中止するか
CUSTOM_TASK_VIS_MAX_POINTS = 400  # 見え方を測るときに使う対象物体の表面の点の数（メッシュの頂点を間引く）

# スクリプト制御による pick-and-place（demos/scripted.py）。正解の位置へ手先を動かす
SCRIPTED_GAIN = 25.0  # 手先の位置の誤差（m）に掛けて、移動量の指令（-1〜1）にする
SCRIPTED_SPEED = 0.8  # 移動の指令の大きさ（3 軸まとめたベクトルの長さ）の上限
SCRIPTED_SLOW_SPEED = 0.3  # 掴む・置く直前に下ろすときの速さの上限
SCRIPTED_SLOW_DZ = 0.03  # m。掴む・置く高さのこれだけ上から、ゆっくり下ろす
SCRIPTED_ACCEL = 0.1  # 移動・回転の指令の 1 ステップあたりの変化量の上限（加速・減速をなめらかにする）
SCRIPTED_ROT_GAIN = 1.0  # 手先の向きの初期からのずれ（回転ベクトル、rad）に掛けて、回転の指令にする
SCRIPTED_STALL_STEPS = 10  # このステップ数の間に
SCRIPTED_STALL_MOVE = 0.002  # m。手先がこれだけしか動かなければ、止まった（物体に当たっている）とみなして次の動作へ進む
SCRIPTED_TOL = 0.01  # m。各経由点にこれより近づいたら次へ進む
SCRIPTED_GRASP_OFFSET = (-0.04, 0.0, 0.01)  # m。ボウルの中心から見た掴む点（ロボット側の縁）
SCRIPTED_APPROACH_DZ = 0.12  # m。掴む点の上のこの高さから下ろす
SCRIPTED_LIFT_DZ = 0.15  # m。掴んだ後に持ち上げる高さ
SCRIPTED_VIA_DZ = 0.25  # m。障害物を避ける経由点の高さ（掴む点から）
SCRIPTED_RELEASE_DZ = 0.04  # m。置き場所の上のこの高さで放す
SCRIPTED_MAX_STEPS = 600  # 1 エピソードの動作指令の上限（robosuite の horizon 1000 から、待機の 50 ステップを引いても十分に小さく）
SCRIPTED_ACTION_MAX = 0.9375  # 移動量の指令の上限（LIBERO の公式デモの動作の範囲 ±0.9375 に合わせる）

# スクリプト制御によるデモの生成（scripts/generate_demos.py）
DEMO_DIR = VLA3DSG_DIR / "data"  # 生成したデータセット（LeRobot 形式、git 管理外）
DEMO_SEED_START = 100_000  # 配置のサンプリングのシード。評価の初期状態（make_custom_task.py はシード 0 から）と重ならないようにする
DEMO_IMAGE_SIZE = 256  # lerobot/libero と同じ
DEMO_FPS = 10  # lerobot/libero の表記に合わせる（実際の制御は 20Hz で、1 フレーム = 1 制御ステップ）
DEMO_GRASP_JITTER = 0.0  # m。掴む点を水平方向にずらす幅（縁を掴む動作はずれに敏感で、0.005 でも半分ほど掴み損ねるため 0）
DEMO_VIA_JITTER = 0.02  # m。経由点を水平方向にずらす幅
DEMO_MOVE_NOISE = 0.02  # 移動の指令に加える揺らぎ（1 ステップあたりの標準偏差）
DEMO_ROT_NOISE = 0.01  # 回転の指令に加える揺らぎ
DEMO_OFFICIAL_DATASET = "lerobot/libero"  # 比べる公式デモ（generate_demos.py --report）
DEMO_OFFICIAL_TASK = "libero_goal/put_the_bowl_on_the_plate"  # 自作のシーンのタスクと比べる公式デモ
DEMO_REPORT_N_EPISODES = 20  # 統計に使うエピソード数（各グループ）
DEMO_REPORT_STALL_MOVE = 0.001  # m。1 ステップの手先の移動がこれ未満なら「止まっている」と数える
DEMO_NOISE_THETA = 0.1  # 揺らぎが 0 に戻る速さ（オルンシュタイン＝ウーレンベック過程）
# タスクごとのスクリプト制御の設定: 掴む物体、置き場所、経由点（世界座標の x, y）、掴む点（省略時は SCRIPTED_GRASP_OFFSET）、
# 掴む前に手先を鉛直軸まわりに回す角度（度）。開いた指は初期の向きでは y 方向に並ぶため、x 方向の縁を掴むときは 90° 回して
# 指が縁の壁を挟むようにする（回さないと片方の指が縁に乗って下りられず、押し続ける）
DEMO_TASK_SPECS = {
    # libero_goal の put the bowl on the plate を元にしたスイート
    "vla3dsg_goal": {
        0: {"target": "akita_black_bowl_1", "dest": "plate_1", "via": [], "grasp_yaw_deg": 90.0},  # 標準
        1: {"target": "akita_black_bowl_1", "dest": "plate_1", "via": [], "grasp_yaw_deg": 90.0},  # 場所シャッフル
        # ワインラックの裏: 手先を回すと前腕がラックに当たるため、+y 側の縁を回さずに掴む（回すと 3/8、回さないと 8/8）
        2: {"target": "akita_black_bowl_1", "dest": "plate_1", "via": [(-0.47, 0.02)], "grasp_offset": (0.0, 0.04, 0.01)},
        3: {"target": "akita_black_bowl_1", "dest": "plate_1", "via": [(-0.47, 0.02)], "grasp_offset": (0.0, 0.04, 0.01)},
    },
}

# Scene Graph の生成（scene_graph/builder.py）
SG_NEAREST_K = 2  # 各物体について前後左右の関係を付ける近傍の数
SG_NEXT_TO_MAX_DIST = 0.03  # m。これより近い物体は前後左右ではなく "next to"
SG_ON_MIN_DZ = 0.005  # m。接触していて、相手よりこれ以上高いと "on"
# 掴む対象についての小さな SG（scene_graph/relevant.py）
SG_RELEVANT_MAX = 2  # 関係の最大数
SG_HIDDEN_MAX_VISIBLE = 0.2  # agentview から見える点の割合がこれ未満なら「隠れている」
SG_LANDMARK_OBJECTS = ("plate",)  # 固定物のほかに、位置の手がかりにする（大きくて動かない）物体の種類（行き先の物体は除く）

# プロンプト条件（run_eval.py --prompt-condition）
PROMPT_CONDITIONS = {
    "base": "公式の指示文のみ（例: put the bowl on the plate）",
    "base_short": "公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py）",
    "base_full": "公式の指示文 + 全部の関係の SG（三つ組）",
    "base_wrong": "公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの）",
    "sg_command": "base_short の SG から作った、場所を書いた指示文（例: put the black bowl behind the wine rack on the plate）",
}
PROMPT_CONDITIONS["base_irrelevant"] = "公式の指示文 + base_full と同じ長さ（トークン数）の、シーンと無関係な文（長さの影響を見る対照）"
# SG の形式を変えた条件（末尾 _json・_nl。付けないと三つ組）。textify.FORMATS
for _k in ("base_short", "base_full", "base_wrong"):
    PROMPT_CONDITIONS[f"{_k}_json"] = PROMPT_CONDITIONS[_k].replace("三つ組", "JSON") if "三つ組" in PROMPT_CONDITIONS[_k] else PROMPT_CONDITIONS[_k] + "（JSON）"
    PROMPT_CONDITIONS[f"{_k}_nl"] = PROMPT_CONDITIONS[_k].replace("三つ組", "自然文") if "三つ組" in PROMPT_CONDITIONS[_k] else PROMPT_CONDITIONS[_k] + "（自然文）"
# 自作スイートのタスク名の表示名（確認用の資料・表）
SCENE_LABELS = {"standard": "標準", "shuffle": "場所シャッフル", "hidden": "標準＋隠れ", "hidden_decoy": "標準＋隠れ（おとりあり）"}
# base_irrelevant の無関係な文（base_full と同じトークン数になるよう、先頭から切り出し、足りなければ繰り返す）
IRRELEVANT_TEXT = (
    "the weather was sunny in the morning and it started to rain in the afternoon. "
    "many people enjoy reading books in the library on weekends. "
    "the train arrived at the station ten minutes later than scheduled. "
    "a small bird was singing in the garden near the old tree. "
    "the museum opens at nine and closes at five every day except monday. "
)
PROMPT_SG_LABEL = "scene information"  # 指示文と追加テキストの区切り: "<指示文>. <ラベル>: <テキスト>"
# SG を加えると指示文が長くなるため、系列長の上限を広げる（既定は指示文 32 トークン分の見込み）
MOLMOACT2_MAX_SEQUENCE_LENGTH = 1024

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
        f"--policy.max_sequence_length={MOLMOACT2_MAX_SEQUENCE_LENGTH}",
        # 指示文の正規化は prompting/prompt_condition.py で元の指示文だけに行う（SG のテキストを壊さないため）
        "--policy.normalize_language=false",
        "--policy.enable_inference_cuda_graph=true",
        "--policy.device=cuda",
        "--policy.per_episode_seed=true",
        f"--policy.eval_seed={EVAL_SEED}",
        "--eval.batch_size=1",
        f"--eval.n_episodes={n_episodes}",
        f"--seed={SEED}",
        f"--output_dir={output_dir}",
    ]
