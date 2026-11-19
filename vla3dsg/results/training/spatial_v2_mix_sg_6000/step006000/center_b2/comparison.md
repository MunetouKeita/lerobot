## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 95.0%（19/20） | 38 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 0.0%（0/20） | 11 |
| base | 公式の指示文のみ（例: put the bowl on the plate） | 20.0%（4/20） | 15 |
| norel_wrong | norel + 対象には当てはまらない関係の SG（三つ組）（学習後に SG の中身を読んでいるかの対照） | 0.0%（0/20） | 27 |

## タスクごと（成功回数）

| task | 指示文 | norel_short | norel | base | norel_wrong |
|---|---|---|---|---|---|
| vla3dsg_spatial 1 | pick up the black bowl next to the plate and place it on the plate | 19/20 | 0/20 | 4/20 | 0/20 |
