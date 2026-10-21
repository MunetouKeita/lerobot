# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | put the bowl on the plate | 0/20 | 20 × black bowl 2 on plate |

## base_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) | 0/20 | 20 × black bowl 2 on plate |

## base_full

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack); (black bo | 0/20 | 19 × black bowl 2 on plate<br>1 × 変化なし |

## base_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet) | 0/20 | 19 × black bowl 2 on plate<br>1 × 変化なし |

## sg_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 3 | put the black bowl behind the wine rack on the plate | 0/20 | 20 × black bowl 2 on plate |
