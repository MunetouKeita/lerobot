## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 80.0%（16/20） | 28 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 5.0%（1/20） | 11 |
| base | 公式の指示文のみ（例: put the bowl on the plate） | 10.0%（2/20） | 15 |
| norel_wrong | norel + 対象には当てはまらない関係の SG（三つ組）（学習後に SG の中身を読んでいるかの対照） | 15.0%（3/20） | 29 |

## タスクごと（成功回数）

| task | 指示文 | norel_short | norel | base | norel_wrong |
|---|---|---|---|---|---|
| vla3dsg_spatial 3 | pick up the black bowl on the wooden cabinet and place it on the plate | 16/20 | 1/20 | 2/20 | 3/20 |
