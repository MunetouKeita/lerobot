## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 80.0%（16/20） | 27 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 85.0%（17/20） | 11 |
| base | 公式の指示文のみ（例: put the bowl on the plate） | 95.0%（19/20） | 16 |
| norel_wrong | norel + 対象には当てはまらない関係の SG（三つ組）（学習後に SG の中身を読んでいるかの対照） | 0.0%（0/20） | 26 |

## タスクごと（成功回数）

| task | 指示文 | norel_short | norel | base | norel_wrong |
|---|---|---|---|---|---|
| vla3dsg_spatial 8 | pick up the black bowl on the ramekin and place it on the plate | 16/20 | 17/20 | 19/20 | 0/20 |
