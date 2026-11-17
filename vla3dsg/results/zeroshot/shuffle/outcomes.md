# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate | 2/20 | 12 × 変化なし<br>8 × black bowl on plate |

## base_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) | 9/20 | 12 × black bowl on plate<br>8 × 変化なし |

## base_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) | 8/20 | 13 × black bowl on plate<br>7 × 変化なし |
