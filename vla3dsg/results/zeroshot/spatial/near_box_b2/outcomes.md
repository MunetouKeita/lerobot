# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl on the stove and place it on the plate | 20/20 | 20 × black bowl 2 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl and place it on the plate | 4/20 | 16 × black bowl 1 on plate<br>4 × black bowl 2 on plate |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 5 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, st | 4/20 | 16 × black bowl 1 on plate<br>4 × black bowl 2 on plate |
