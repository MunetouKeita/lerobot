# 段階 1: 公式デモを混ぜた SG ありの学習を更新 6,000 回に延ばす（experiments.md の 5-5）

- 学習・評価: `run.sh`（6000ada の GPU 4 枚、2026-11-18 12:51〜21:50。学習 6.1 時間、評価 90 本 2.8 時間）。コードは git 608734b9 に、未コミットの `norel_wrong` の追加（`config/settings.py`・`prompting/prompt_condition.py`）を rsync で送ったもの
- データ: `vla3dsg/data/spatial_v2_mix_sg`（自作デモ 300 本に ③、公式の libero_spatial のデモ 432 本は ① のまま。同じデータで更新 3,000 回にした 5-4 の結果は削除）
- 設定: 5-3 と同じで、更新回数を 6,000 回、学習率の減衰を 6,000 回、チェックポイントの保存を 1,000 回ごとにした
- 結果: `step<更新回数>/comparison.md`（配置 × 条件の成功率）、`step<…>/<シーン>/outcomes.md`（終了時に皿に置いたボウル）。最後の `step006000` だけ ③ のほかに ②（norel）・①（base）・誤った SG（norel_wrong）でも評価した
- チェックポイントは更新 6,000 回（`006000`）だけを 6000ada の `outputs/train/spatial_v2_mix_sg_6000/` に残している。動画は 6000ada の各結果の `videos/`
