# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, left o | 18/20 | 18 × black bowl 2 on plate<br>1 × black bowl 1 on plate<br>1 × 変化なし |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate | 8/20 | 12 × black bowl 1 on plate<br>8 × black bowl 2 on plate |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, in fro | 1/20 | 12 × black bowl 1 on plate<br>7 × 変化なし<br>1 × black bowl 2 on plate |
