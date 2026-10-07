# Phase 0: 推論時間と GPU メモリの計測

- 日時: 2026-10-07
- LeRobot: upstream main `200ee535` + `vla3dsg` ブランチ（本体の変更なし）
- 計測スクリプト: `vla3dsg/scripts/measure_inference.py`（`lerobot-eval` と同じ処理経路で、前処理と推論の前後に `torch.cuda.synchronize()` を入れて計測）
- チェックポイント: `allenai/MolmoAct2-LIBERO`（`norm_tag=libero`、float32、CUDA graph 有効）
- 環境: `libero_vla3dsg`（`num_steps_wait=50`）、`libero_goal` task 0、3 エピソード（3/3 成功、計 352 ステップ）
- GPU: RTX 5090（32GB）

## 結果

| 項目 | 値 |
|---|---|
| アクションチャンク推論（10 ステップ分、`predict_action_chunk`） | 中央値 188.8 ms（初回は CUDA graph のキャプチャを含み 860.6 ms） |
| 前処理（画像・指示文のトークン化など、毎ステップ） | 中央値 8.9 ms |
| `select_action`（キューから取り出すだけのステップ） | 中央値 4.8 ms |
| 1 ステップあたりの方策側の平均時間 | 約 33 ms（`select_action` 平均 24.2 ms + 前処理 9.0 ms） |
| GPU メモリ（PyTorch の確保量のピーク） | allocated 22.57 GiB / reserved 24.2 GiB |
| GPU メモリ（nvidia-smi のピーク、Phase 0 の 1 エピソード評価時） | 約 26.0 GB（デスクトップ表示分を除く） |

- 推論は 10 ステップに 1 回（`n_action_steps=10`）。LIBERO の制御周期 20Hz（50ms/ステップ）に対し、チャンク推論 1 回は約 3.8 ステップ分の時間がかかるが、シミュレーションでは推論中に環境が止まるため成功率には影響しない
