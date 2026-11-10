# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl on the wooden cabinet and place it on the plate | 20/20 | 20 × black bowl 2 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl and place it on the plate | 8/20 | 10 × black bowl 1 on plate<br>9 × black bowl 2 on plate<br>1 × 変化なし |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, to | 4/20 | 7 × 変化なし<br>6 × black bowl 1 on plate<br>6 × black bowl 2 on plate<br>1 × black bowl 1 on plate, black bowl 2 on black bowl 1 |
