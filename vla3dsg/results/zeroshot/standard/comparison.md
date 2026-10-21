## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| base | 公式の指示文のみ（例: put the bowl on the plate） | 95.0%（19/20） | 6 |
| base_short | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 100.0%（20/20） | 20 |
| base_short_json | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（JSON、1〜2 本。scene_graph/relevant.py） | 100.0%（20/20） | 33 |
| base_short_nl | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（自然文、1〜2 本。scene_graph/relevant.py） | 100.0%（20/20） | 22 |
| base_full | 公式の指示文 + 全部の関係の SG（三つ組） | 100.0%（20/20） | 88 |
| base_full_json | 公式の指示文 + 全部の関係の SG（JSON） | 100.0%（20/20） | 178 |
| base_full_nl | 公式の指示文 + 全部の関係の SG（自然文） | 100.0%（20/20） | 96 |
| base_wrong | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの） | 100.0%（20/20） | 20 |
| base_wrong_json | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの）（JSON） | 100.0%（20/20） | 33 |
| base_wrong_nl | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの）（自然文） | 100.0%（20/20） | 22 |

## タスクごと（成功回数）

| task | 指示文 | base | base_short | base_short_json | base_short_nl | base_full | base_full_json | base_full_nl | base_wrong | base_wrong_json | base_wrong_nl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| vla3dsg_goal 0 | Put the bowl on the plate | 19/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
