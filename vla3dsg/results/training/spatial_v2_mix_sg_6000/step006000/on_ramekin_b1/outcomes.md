# エピソードの結果（終了時に新しくできた on / in の関係）

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, ra | 16/20 | 14 × black bowl 1 on plate<br>3 × ramekin on plate<br>2 × black bowl 1 on plate, ramekin on plate<br>1 × ramekin on black bowl 1 |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl and place it on the plate | 17/20 | 17 × black bowl 1 on plate<br>1 × 変化なし<br>1 × black bowl 1 on plate, ramekin on black bowl 1<br>1 × black bowl 1 on plate, ramekin on plate |

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl on the ramekin and place it on the plate | 19/20 | 20 × black bowl 1 on plate |

## norel_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 8 | pick up the black bowl and place it on the plate. scene information: (black bowl 1, on, co | 0/20 | 17 × black bowl 2 on plate<br>3 × 変化なし |
