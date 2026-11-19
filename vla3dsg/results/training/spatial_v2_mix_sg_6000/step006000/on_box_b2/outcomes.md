# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, to | 18/20 | 19 × black bowl 2 on plate<br>1 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl and place it on the plate | 9/20 | 11 × black bowl 1 on plate<br>9 × black bowl 2 on plate |

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl on the wooden cabinet and place it on the plate | 19/20 | 19 × black bowl 2 on plate<br>1 × black bowl 1 on plate |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 7 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, co | 1/20 | 17 × black bowl 1 on plate<br>2 × 変化なし<br>1 × black bowl 2 on plate |
