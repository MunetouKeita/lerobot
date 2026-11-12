## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 85.0%（17/20） | 11 |
| base | 公式の指示文のみ（例: put the bowl on the plate） | 85.0%（17/20） | 16 |

## タスクごと（成功回数）

| task | 指示文 | norel | base |
|---|---|---|---|
| vla3dsg_spatial 8 | pick up the black bowl on the ramekin and place it on the plate | 17/20 | 17/20 |
