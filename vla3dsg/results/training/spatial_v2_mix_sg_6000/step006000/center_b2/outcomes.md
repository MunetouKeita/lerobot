# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, left o | 19/20 | 19 × black bowl 2 on plate<br>1 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate | 0/20 | 14 × black bowl 1 on plate<br>6 × black bowl 1 on plate, black bowl 2 on black bowl 1 |

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl next to the plate and place it on the plate | 4/20 | 16 × black bowl 1 on plate<br>4 × black bowl 2 on plate |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, in fro | 0/20 | 18 × black bowl 1 on plate<br>1 × black bowl 1 on plate, black bowl 2 on black bowl 1<br>1 × 変化なし |
