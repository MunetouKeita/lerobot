# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | put the bowl on the plate | 0/20 | 11 × 変化なし<br>9 × cream cheese on plate |

## base_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | put the bowl on the plate. scene information: (black bowl, behind, wine rack) | 0/20 | 12 × 変化なし<br>8 × cream cheese on plate |

## base_full

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | put the bowl on the plate. scene information: (black bowl, behind, wine rack); (black bowl | 0/20 | 16 × cream cheese on plate<br>4 × 変化なし |

## base_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | put the bowl on the plate. scene information: (black bowl, in front of, wine rack) | 0/20 | 11 × 変化なし<br>9 × cream cheese on plate |

## sg_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 2 | put the black bowl behind the wine rack on the plate | 0/20 | 18 × 変化なし<br>2 × cream cheese on plate |
