## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| base | 公式の指示文のみ（例: put the bowl on the plate） | 100.0%（20/20） | 14 |
| norel | 公式の指示文から対象の位置関係を外したもの（例: pick up the black bowl and place it on the plate） | 100.0%（20/20） | 11 |
| norel_short | norel + 掴む対象を見分ける最小の関係だけの SG（三つ組） | 100.0%（20/20） | 39 |
| norel_command | norel の対象の名前の後に、norel_short の SG から作った場所を入れた指示文（例: pick up the black bowl on the cookie box and place it on the plate） | 95.0%（19/20） | 24 |

## タスクごと（成功回数）

| task | 指示文 | base | norel | norel_short | norel_command |
|---|---|---|---|---|---|
| vla3dsg_spatial 0 | pick up the black bowl from table center and place it on the plate | 20/20 | 20/20 | 20/20 | 19/20 |
