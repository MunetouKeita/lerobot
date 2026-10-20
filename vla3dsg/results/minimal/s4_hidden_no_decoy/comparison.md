## 全体

| 条件 | 内容 | 成功率 | プロンプトの長さ（トークン、中央値） |
|---|---|---|---|
| P1 | P3 の SG から作った、場所を書いた指示文（LIBERO の指示文と同じ形。例: pick up the black bowl behind the wooden cabinet and place it on the plate） | 0.0%（0/20） | 14 |
| P1h | P1 で、対象が隠れていればそれも書く（例: pick up the black bowl that is hidden behind the wooden cabinet and place it on the plate） | 0.0%（0/20） | 18 |
| P2 | 対象だけの指示文（場所なし。例: pick up the black bowl 1 and place it on the plate） | 0.0%（0/20） | 11 |
| P2h | P2 で、対象が隠れていればそれも書く（例: pick up the black bowl 1 that is hidden and place it on the plate） | 0.0%（0/20） | 14 |
| P3 | P2 + 掴む対象を見分ける最小の関係だけの SG（三つ組、1〜2 本。scene_graph/relevant.py） | 0.0%（0/20） | 24 |
| P3h | P3 で、対象が隠れていれば関係に hidden を付ける | 0.0%（0/20） | 26 |
| P4 | P2 + 全部の関係の SG（三つ組） | 0.0%（0/20） | 88 |
| P4h | P4 で、対象が隠れていれば対象の最初の関係に hidden を付ける | 0.0%（0/20） | 90 |

## タスクごと（成功回数）

| task | 指示文 | P1 | P1h | P2 | P2h | P3 | P3h | P4 | P4h |
|---|---|---|---|---|---|---|---|---|---|
| vla3dsg_occluded 4 | pick up the black bowl and place it on the plate | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| vla3dsg_occluded 5 | pick up the black bowl and place it on the plate | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
