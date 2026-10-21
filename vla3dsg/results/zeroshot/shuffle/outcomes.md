# エピソードの結果（終了時に新しくできた on / in の関係）

## base

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate | 2/20 | 12 × 変化なし<br>8 × black bowl on plate |

## base_short

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) | 9/20 | 12 × black bowl on plate<br>8 × 変化なし |

## base_short_json

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "left | 4/20 | 12 × 変化なし<br>7 × black bowl on plate<br>1 × plate on black bowl |

## base_short_nl

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: the black bowl is to the left of the wooden  | 9/20 | 11 × black bowl on plate<br>9 × 変化なし |

## base_full

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: (black bowl, in front of, plate); (black bow | 0/20 | 20 × 変化なし |

## base_full_json

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "in f | 0/20 | 19 × 変化なし<br>1 × black bowl on plate |

## base_full_nl

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: the black bowl is in front of the plate. the | 0/20 | 19 × 変化なし<br>1 × black bowl on plate |

## base_irrelevant

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: the weather was sunny in the morning and it  | 0/20 | 19 × 変化なし<br>1 × black bowl on plate |

## base_wrong

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) | 8/20 | 13 × black bowl on plate<br>7 × 変化なし |

## base_wrong_json

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "righ | 9/20 | 13 × black bowl on plate<br>7 × 変化なし |

## base_wrong_nl

| task | プロンプト（先頭） | 成功 | 結果（回数） |
|---|---|---|---|
| 1 | put the bowl on the plate. scene information: the black bowl is to the right of the wooden | 12/20 | 14 × black bowl on plate<br>6 × 変化なし |
