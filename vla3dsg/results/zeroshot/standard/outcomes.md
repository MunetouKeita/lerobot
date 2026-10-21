# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the bowl on the plate | 19/20 | 19 × black bowl on plate<br>1 × 変化なし |

## base_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) | 20/20 | 20 × black bowl on plate |

## base_full

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the bowl on the plate. scene information: (black bowl, in front of, wine bottle); (bla | 20/20 | 20 × black bowl on plate |

## base_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) | 20/20 | 20 × black bowl on plate |

## target

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the black bowl on the plate | 20/20 | 20 × black bowl on plate |

## sg_command

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 0 | put the black bowl to the left of the wooden cabinet on the plate | 20/20 | 20 × black bowl on plate |
