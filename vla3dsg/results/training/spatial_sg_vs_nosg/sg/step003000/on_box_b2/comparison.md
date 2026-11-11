## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 65.0%（13/20） | 28 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 45.0%（9/20） | 11 |

## タスクごと（成功回数）

| task | 指示文 | norel_short | norel |
|---|---|---|---|
| vla3dsg_spatial 7 | pick up the black bowl on the wooden cabinet and place it on the plate | 13/20 | 9/20 |
