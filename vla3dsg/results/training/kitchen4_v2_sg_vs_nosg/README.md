# kitchen4_v2_sg_vs_nosg（4-5）

隠し場所 2 か所のシーン（`vla3dsg_kitchen4`）で、5-2 と同じ作り方のデモ（`kitchen4_v2_train`・`kitchen4_v2_train_sg`、200 本）から
SG なし（指示文 base）・SG あり（base_short）を更新 6,000 回学習し、1,000 回ごとに 3 シーン × 20 本で評価した。
最後に SG ありへ誤った SG（base_wrong: もう一方の隠し場所の裏）を与えた。設定は `run.sh`、経過は `status.log`。

- 6000ada。更新 1,000 回までは GPU 4 枚（1 枚あたりバッチ 8）、以降は 2 枚（16）に変えて続きから学習した（合計バッチ 32 は同じ）
- 結果と読み取れることは `experiments.md` の 4-5。SG なしもワインラックの裏の配置を手首カメラで見分けて解けたため、
  隠れたボウルの位置を変えて 4-6（`kitchen4_v3_sg_vs_nosg/`）でやり直した
