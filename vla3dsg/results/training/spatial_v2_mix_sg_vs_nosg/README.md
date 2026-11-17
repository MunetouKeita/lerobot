# 段階 1: SG なし／ありの学習、公式デモ 432 本を混ぜる（experiments.md の 5-4）

- 学習・評価: `run.sh`（6000ada の GPU 4 枚、2026-11-13 23:22〜2026-11-14 10:09）。コードは git e749d4aa に、未コミットの変更（`settings.py`・`demos/scripted.py`・`scripts/generate_demos.py`）を rsync で送ったもの
- データ: `vla3dsg/data/spatial_v2_mix_norel`・`spatial_v2_mix_sg`（デモの記録は `results/demos/spatial_v2_<配置>[_norel|_sg]/`）
- 結果: `<nosg|sg>/step<更新回数>/comparison.md`（配置 × 条件の成功率）、`<nosg|sg>/step<…>/<シーン>/outcomes.md`（終了時に皿に置いたボウル）
- チェックポイントは更新 3,000 回（`003000`）だけを 6000ada の `outputs/train/spatial_v2_mix_sg_vs_nosg_<nosg|sg>/` に残している。動画は 6000ada の各結果の `videos/`
