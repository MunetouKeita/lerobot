## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| A | 元の指示文のみ | 50.0%（20/40） | 16 |
| L1 | 同じスイートの別タスクの指示文（タスク ID を PROMPT_OTHER_TASK_OFFSET ずらす） | 50.0%（20/40） | 16 |

## タスクごと（成功回数）

| task | 指示文 | A | L1 |
|---|---|---|---|
| vla3dsg_hidden 0 | pick up the black bowl behind the wooden cabinet and place it on the plate | 0/20 | 0/20 |
| vla3dsg_hidden 1 | pick up the black bowl next to the wooden cabinet and place it on the plate | 20/20 | 20/20 |
