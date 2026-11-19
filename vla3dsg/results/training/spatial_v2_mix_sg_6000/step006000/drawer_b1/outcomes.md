# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, in, to | 13/20 | 13 × black bowl 1 on plate<br>5 × 変化なし<br>2 × black bowl 2 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl and place it on the plate | 18/20 | 18 × black bowl 1 on plate<br>1 × black bowl 2 on plate<br>1 × 変化なし |

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 19/20 | 19 × black bowl 1 on plate<br>1 × 変化なし |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, to | 1/20 | 13 × black bowl 2 on plate<br>6 × 変化なし<br>1 × black bowl 1 on plate |
