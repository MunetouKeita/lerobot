# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl on the cookie box and place it on the plate | 20/20 | 20 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl and place it on the plate | 9/20 | 10 × black bowl 1 on plate<br>9 × black bowl 2 on plate<br>1 × 変化なし |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, co | 17/20 | 17 × black bowl 1 on plate<br>3 × black bowl 2 on plate |

## norel_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 6 | pick up the black bowl on the cookie box and place it on the plate | 20/20 | 20 × black bowl 1 on plate |
