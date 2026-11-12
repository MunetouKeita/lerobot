## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 25.0%（5/20） | 11 |
| base | 公式の指示文のみ（例: put the bowl on the plate） | 20.0%（4/20） | 15 |

## タスクごと（成功回数）

| task | 指示文 | norel | base |
|---|---|---|---|
| vla3dsg_spatial 1 | pick up the black bowl next to the plate and place it on the plate | 5/20 | 4/20 |
