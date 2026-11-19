# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, st | 18/20 | 18 × black bowl 2 on plate<br>2 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl and place it on the plate | 12/20 | 12 × black bowl 2 on plate<br>5 × black bowl 1 on plate<br>3 × 変化なし |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, left o | 0/20 | 13 × black bowl 1 on plate<br>7 × 変化なし |
