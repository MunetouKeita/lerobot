## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| A | 元の指示文のみ | 50.0%（20/40） | 16 |
| B1 | 指示文 + SG（JSON） | 50.0%（20/40） | 188 |
| B2 | 指示文 + SG（三つ組の列挙） | 50.0%（20/40） | 128 |
| B3 | 指示文 + SG（自然文） | 50.0%（20/40） | 130 |
| C | 指示文 + SG（JSON）と同じトークン数の無関係な文 | 50.0%（20/40） | 188 |
| D | 指示文 + 物体名を入れ替えた SG（JSON） | 50.0%（20/40） | 192 |

## タスクごと（成功回数）

| task | 指示文 | A | B1 | B2 | B3 | C | D |
|---|---|---|---|---|---|---|---|
| vla3dsg_hidden 0 | pick up the black bowl behind the wooden cabinet and place it on the plate | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 |
| vla3dsg_hidden 1 | pick up the black bowl next to the wooden cabinet and place it on the plate | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
