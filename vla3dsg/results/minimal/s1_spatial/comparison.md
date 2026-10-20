## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| P1 | P3 の SG から作った、場所を書いた指示文（LIBERO の指示文と同じ形。例: pick up the black bowl behind the wooden cabinet and place it on the plate） | 94.0%（47/50） | 17 |
| P2 | 対象だけの指示文（場所なし。例: pick up the black bowl 1 and place it on the plate） | 84.0%（42/50） | 13 |
| P3 | P2 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 80.0%（40/50） | 28 |
| P4 | P2 + 全部の関係の SG（三つ組） | 68.0%（34/50） | 124 |
| P5 | P2 + 誤った SG（同じ種類の別の物体の P3 の関係を、対象の名前で書いたもの） | 80.0%（40/50） | 29 |

## タスクごと（成功回数）

| task | 指示文 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| libero_spatial 0 | pick up the black bowl between the plate and the ramekin and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 1 | pick up the black bowl next to the ramekin and place it on the plate | 3/5 | 5/5 | 5/5 | 4/5 | 5/5 |
| libero_spatial 2 | pick up the black bowl from table center and place it on the plate | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| libero_spatial 3 | pick up the black bowl on the cookie box and place it on the plate | 5/5 | 2/5 | 3/5 | 5/5 | 2/5 |
| libero_spatial 4 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 5/5 | 4/5 | 1/5 | 1/5 | 5/5 |
| libero_spatial 5 | pick up the black bowl on the ramekin and place it on the plate | 5/5 | 5/5 | 5/5 | 3/5 | 5/5 |
| libero_spatial 6 | pick up the black bowl next to the cookie box and place it on the plate | 5/5 | 4/5 | 5/5 | 5/5 | 4/5 |
| libero_spatial 7 | pick up the black bowl on the stove and place it on the plate | 5/5 | 4/5 | 4/5 | 0/5 | 0/5 |
| libero_spatial 8 | pick up the black bowl next to the plate and place it on the plate | 4/5 | 4/5 | 5/5 | 4/5 | 5/5 |
| libero_spatial 9 | pick up the black bowl on the wooden cabinet and place it on the plate | 5/5 | 4/5 | 2/5 | 2/5 | 4/5 |
