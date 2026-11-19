# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, to | 19/20 | 20 × black bowl 2 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl and place it on the plate | 7/20 | 9 × black bowl 1 on plate<br>7 × black bowl 2 on plate<br>4 × 変化なし |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, in, to | 1/20 | 14 × black bowl 1 on plate<br>5 × 変化なし<br>1 × black bowl 2 on plate |
