# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl on the ramekin and place it on the plate | 20/20 | 20 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl and place it on the plate | 17/20 | 17 × black bowl 1 on plate<br>3 × ramekin on plate |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, ra | 18/20 | 18 × black bowl 1 on plate<br>1 × black bowl 1 on plate, ramekin on plate<br>1 × ramekin on plate |

## norel_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl on the ramekin and place it on the plate | 20/20 | 20 × black bowl 1 on plate |
