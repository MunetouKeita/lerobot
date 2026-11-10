# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl on the wooden cabinet and place it on the plate | 0/20 | 20 × black bowl 1 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl and place it on the plate | 0/20 | 16 × black bowl 1 on plate<br>3 × 変化なし<br>1 × plate on black bowl 1 |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, to | 0/20 | 15 × black bowl 1 on plate<br>4 × 変化なし<br>1 × black bowl 1 on cookie box |

## norel_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | pick up the black bowl on the top of the wooden cabinet and place it on the plate | 0/20 | 20 × black bowl 1 on plate |
