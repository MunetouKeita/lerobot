## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| P1 | P3 の SG から作った、場所を書いた指示文（LIBERO の指示文と同じ形。例: pick up the black bowl behind the wooden cabinet and place it on the plate） | 15.0%（3/20） | 14 |
| P2 | 対象だけの指示文（場所なし。例: pick up the black bowl 1 and place it on the plate） | 15.0%（3/20） | 13 |
| P3 | P2 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 15.0%（3/20） | 27 |
| P4 | P2 + 全部の関係の SG（三つ組） | 35.0%（7/20） | 127 |
| P5 | P2 + 誤った SG（同じ種類の別の物体の P3 の関係を、対象の名前で書いたもの） | 20.0%（4/20） | 28 |

## タスクごと（成功回数）

| task | 指示文 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| vla3dsg_occluded 2 | pick up the black bowl 1 and place it on the plate | 3/10 | 3/10 | 3/10 | 3/10 | 4/10 |
| vla3dsg_occluded 3 | pick up the black bowl 1 and place it on the plate | 0/10 | 0/10 | 0/10 | 4/10 | 0/10 |
