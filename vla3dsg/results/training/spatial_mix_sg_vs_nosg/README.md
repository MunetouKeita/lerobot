# 段階 1: 公式デモを混ぜた SG なし／ありの学習（experiments.md の 5-3）

- 学習・評価: `run.sh`（6000ada の GPU 4 枚、git e749d4aa、2026-11-12 14:28〜11-13 02:01）
- データ: `vla3dsg/data/spatial_mix_norel`・`spatial_mix_sg`（5-2 のデモ＋公式の libero_spatial のデモ 432 本。記録は `results/demos/official_spatial_<0〜9>/`）
- 結果: `<nosg|sg>/step<…>/comparison.md`、`<nosg|sg>/step<…>/<シーン>/outcomes.md`
- チェックポイントは更新 3,000 回（`003000`）だけを 6000ada の `outputs/train/spatial_mix_sg_vs_nosg_<nosg|sg>/` に残している。動画は 6000ada の各結果の `videos/`
