# 段階 1: SG なし／ありの学習（experiments.md の 5-2）

- 学習・評価: `run.sh`（6000ada の GPU 4 枚、git a15ba75c、2026-11-11 12:06〜11-12 02:52）
- データ: `vla3dsg/data/spatial_train_norel`・`spatial_train_sg`（記録は `results/demos/spatial_<配置>[_norel|_sg]/`）
- 結果: `<nosg|sg>/step<更新回数×4>/comparison.md`（配置 × 条件の成功率）、`<nosg|sg>/step<…>/<シーン>/outcomes.md`（終了時に皿に置いたボウル）
- チェックポイントは更新 3,000 回（`003000`）だけを 6000ada の `outputs/train/spatial_sg_vs_nosg_<nosg|sg>/` に残している。動画は 6000ada の各結果の `videos/`
