## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 90.0%（18/20） | 26 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 40.0%（8/20） | 11 |
| norel_wrong | norel + 対象には当てはまらない関係の SG（三つ組）（学習後に SG の中身を読んでいるかの対照） | 5.0%（1/20） | 28 |

## タスクごと（成功回数）

| task | 指示文 | norel_short | norel | norel_wrong |
|---|---|---|---|---|
| vla3dsg_spatial 6 | pick up the black bowl on the cookie box and place it on the plate | 18/20 | 8/20 | 1/20 |
