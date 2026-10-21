## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| base | 公式の指示文のみ（例: put the bowl on the plate） | 10.0%（2/20） | 6 |
| base_short | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 45.0%（9/20） | 20 |
| base_full | 公式の指示文 + 全部の関係の SG（三つ組） | 0.0%（0/20） | 86 |
| base_wrong | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの） | 40.0%（8/20） | 20 |
| target | 対象の SG のノード名だけの指示文（場所なし。例: put the black bowl 1 on the plate） | 65.0%（13/20） | 7 |
| sg_command | base_short の SG から作った、場所を書いた指示文（例: put the black bowl behind the wine rack on the plate） | 55.0%（11/20） | 14 |

## タスクごと（成功回数）

| task | 指示文 | base | base_short | base_full | base_wrong | target | sg_command |
|---|---|---|---|---|---|---|---|
| vla3dsg_goal 1 | Put the bowl on the plate | 2/20 | 9/20 | 0/20 | 8/20 | 13/20 | 11/20 |
