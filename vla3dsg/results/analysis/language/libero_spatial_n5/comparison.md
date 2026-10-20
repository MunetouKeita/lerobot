## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| L0 | 場所の指定を除いた指示文（例: pick up the black bowl and place it on the plate） | 88.0%（44/50） | 11 |
| L1 | 同じスイートの別タスクの指示文（タスク ID を PROMPT_OTHER_TASK_OFFSET ずらす） | 76.0%（38/50） | 16 |

## タスクごと（成功回数）

| task | 指示文 | L0 | L1 |
|---|---|---|---|
| libero_spatial 0 | pick up the black bowl between the plate and the ramekin and place it on the plate | 5/5 | 5/5 |
| libero_spatial 1 | pick up the black bowl next to the ramekin and place it on the plate | 5/5 | 0/5 |
| libero_spatial 2 | pick up the black bowl from table center and place it on the plate | 5/5 | 5/5 |
| libero_spatial 3 | pick up the black bowl on the cookie box and place it on the plate | 2/5 | 5/5 |
| libero_spatial 4 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 5/5 | 5/5 |
| libero_spatial 5 | pick up the black bowl on the ramekin and place it on the plate | 5/5 | 0/5 |
| libero_spatial 6 | pick up the black bowl next to the cookie box and place it on the plate | 3/5 | 5/5 |
| libero_spatial 7 | pick up the black bowl on the stove and place it on the plate | 5/5 | 5/5 |
| libero_spatial 8 | pick up the black bowl next to the plate and place it on the plate | 5/5 | 3/5 |
| libero_spatial 9 | pick up the black bowl on the wooden cabinet and place it on the plate | 4/5 | 5/5 |
