# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 9 | pick up the black bowl on the cookie box and place it on the plate | 19/20 | 20 × black bowl 2 on plate |

## norel

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 9 | pick up the black bowl and place it on the plate | 0/20 | 14 × black bowl 1 on plate<br>3 × ramekin on plate<br>2 × black bowl 1 on plate, black bowl 2 on black bowl 1<br>1 × 変化なし |

## norel_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 9 | pick up the black bowl and place it on the plate. scene information: (black bowl 2, on, co | 0/20 | 16 × black bowl 1 on plate<br>2 × ramekin on plate<br>1 × black bowl 1 on plate, black bowl 2 on black bowl 1<br>1 × black bowl 1 on plate, black bowl 2 on plate |
