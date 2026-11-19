# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, co | 17/20 | 17 × black bowl 1 on plate<br>2 × black bowl 2 on plate<br>1 × 変化なし |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl and place it on the plate | 11/20 | 11 × black bowl 1 on plate<br>9 × black bowl 2 on plate |

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl on the cookie box and place it on the plate | 18/20 | 20 × black bowl 1 on plate |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, to | 1/20 | 10 × black bowl 2 on plate<br>6 × black bowl 1 on black bowl 2, black bowl 2 on plate<br>3 × 変化なし<br>1 × black bowl 1 on plate |
