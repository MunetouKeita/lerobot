## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| base | 公式の指示文のみ（例: put the bowl on the plate） | 10.0%（2/20） | 6 |
| base_short | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 45.0%（9/20） | 20 |
| base_short_json | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（JSON、1〜2 本。scene_graph/relevant.py） | 20.0%（4/20） | 33 |
| base_short_nl | 公式の指示文 + 掴む対象を見分ける最小の関係だけの SG（自然文、1〜2 本。scene_graph/relevant.py） | 45.0%（9/20） | 22 |
| base_full | 公式の指示文 + 全部の関係の SG（三つ組） | 0.0%（0/20） | 86 |
| base_full_json | 公式の指示文 + 全部の関係の SG（JSON） | 0.0%（0/20） | 177 |
| base_full_nl | 公式の指示文 + 全部の関係の SG（自然文） | 0.0%（0/20） | 94 |
| base_irrelevant | 公式の指示文 + base_full と同じ長さ（トークン数）の、シーンと無関係な文（長さの影響を見る対照） | 0.0%（0/20） | 85 |
| base_wrong | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの） | 40.0%（8/20） | 20 |
| base_wrong_json | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの）（JSON） | 45.0%（9/20） | 33 |
| base_wrong_nl | 公式の指示文 + 対象には当てはまらない関係の SG（おとりがあればおとりの関係、なければ前後左右を逆にしたもの）（自然文） | 60.0%（12/20） | 22 |

## タスクごと（成功回数）

| task | 指示文 | base | base_short | base_short_json | base_short_nl | base_full | base_full_json | base_full_nl | base_irrelevant | base_wrong | base_wrong_json | base_wrong_nl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vla3dsg_goal 1 | Put the bowl on the plate | 2/20 | 9/20 | 4/20 | 9/20 | 0/20 | 0/20 | 0/20 | 0/20 | 8/20 | 9/20 | 12/20 |
