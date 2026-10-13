## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| A | 元の指示文のみ | 96.0%（48/50） | 16 |
| B1 | 指示文 + SG（JSON） | 90.0%（45/50） | 187 |
| B2 | 指示文 + SG（三つ組の列挙） | 86.0%（43/50） | 126 |
| B3 | 指示文 + SG（自然文） | 82.0%（41/50） | 128 |
| C | 指示文 + SG（JSON）と同じトークン数の無関係な文 | 92.0%（46/50） | 187 |
| D | 指示文 + 物体名を入れ替えた SG（JSON） | 94.0%（47/50） | 188 |

## タスクごと（成功回数）

| task | 指示文 | A | B1 | B2 | B3 | C | D |
|---|---|---|---|---|---|---|---|
| libero_spatial 0 | pick up the black bowl between the plate and the ramekin and place it on the plate | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 1 | pick up the black bowl next to the ramekin and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 2 | pick up the black bowl from table center and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 3 | pick up the black bowl on the cookie box and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 4 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 4/5 | 3/5 | 3/5 | 3/5 | 3/5 | 3/5 |
| libero_spatial 5 | pick up the black bowl on the ramekin and place it on the plate | 5/5 | 4/5 | 4/5 | 3/5 | 4/5 | 5/5 |
| libero_spatial 6 | pick up the black bowl next to the cookie box and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 7 | pick up the black bowl on the stove and place it on the plate | 5/5 | 4/5 | 3/5 | 2/5 | 5/5 | 5/5 |
| libero_spatial 8 | pick up the black bowl next to the plate and place it on the plate | 4/5 | 5/5 | 4/5 | 4/5 | 4/5 | 5/5 |
| libero_spatial 9 | pick up the black bowl on the wooden cabinet and place it on the plate | 5/5 | 5/5 | 4/5 | 4/5 | 5/5 | 4/5 |
