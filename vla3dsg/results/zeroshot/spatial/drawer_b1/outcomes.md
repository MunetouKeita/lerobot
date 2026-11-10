# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 20/20 | 20 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl and place it on the plate | 16/20 | 16 × black bowl 1 on plate<br>3 × 変化なし<br>1 × plate on black bowl 1 |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, in, to | 7/20 | 13 × 変化なし<br>7 × black bowl 1 on plate |

## norel_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 20/20 | 20 × black bowl 1 on plate |
