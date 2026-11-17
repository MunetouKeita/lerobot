## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| base | 公式の指示文のみ（例: put the bowl on the plate） | 100.0%（20/20） | 14 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 20.0%（4/20） | 11 |
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 20.0%（4/20） | 25 |

## タスクごと（成功回数）

| task | 指示文 | base | norel | norel_short |
|---|---|---|---|---|
| vla3dsg_spatial 5 | pick up the black bowl on the stove and place it on the plate | 20/20 | 4/20 | 4/20 |
