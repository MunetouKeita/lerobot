# vla3dsg_goal のシーンと指示文（初期状態 0）

## task 0: 標準

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_full | put the bowl on the plate. scene information: (black bowl, in front of, wine bottle); (black bowl, right of, cream cheese); (cream cheese, left of, black bowl); (cream cheese, left of, plate); (wine bottle, behind, black bowl); (wine bottle, left of, wine rack); (plate, in front of, black bowl); (plate, right of, cream cheese) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |
| sg_command | put the black bowl to the left of the wooden cabinet on the plate |
| base_irrelevant | put the bowl on the plate. scene information: the weather was sunny in the morning and it started to rain in the afternoon. many people enjoy reading books in the library on weekends. the train arrived at the station ten minutes later than scheduled. a small bird was singing in the garden near the old tree. the museum opens at nine and closes at five every day except monday. the weather was sunny in the morning and it started to |
| base_short_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "left of", "object": "wooden cabinet"}] |
| base_short_nl | put the bowl on the plate. scene information: the black bowl is to the left of the wooden cabinet. |
| base_full_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "in front of", "object": "wine bottle"}, {"subject": "black bowl", "relation": "right of", "object": "cream cheese"}, {"subject": "cream cheese", "relation": "left of", "object": "black bowl"}, {"subject": "cream cheese", "relation": "left of", "object": "plate"}, {"subject": "wine bottle", "relation": "behind", "object": "black bowl"}, {"subject": "wine bottle", "relation": "left of", "object": "wine rack"}, {"subject": "plate", "relation": "in front of", "object": "black bowl"}, {"subject": "plate", "relation": "right of", "object": "cream cheese"}] |
| base_full_nl | put the bowl on the plate. scene information: the black bowl is in front of the wine bottle. the black bowl is to the right of the cream cheese. the cream cheese is to the left of the black bowl. the cream cheese is to the left of the plate. the wine bottle is behind the black bowl. the wine bottle is to the left of the wine rack. the plate is in front of the black bowl. the plate is to the right of the cream cheese. |
| base_wrong_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "right of", "object": "wooden cabinet"}] |
| base_wrong_nl | put the bowl on the plate. scene information: the black bowl is to the right of the wooden cabinet. |

## task 1: 場所シャッフル

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_full | put the bowl on the plate. scene information: (black bowl, in front of, plate); (black bowl, left of, cream cheese); (cream cheese, right of, black bowl); (cream cheese, in front of, wine bottle); (wine bottle, behind, cream cheese); (wine bottle, right of, plate); (plate, behind, black bowl); (plate, left of, wine bottle) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |
| sg_command | put the black bowl to the left of the wooden cabinet on the plate |
| base_irrelevant | put the bowl on the plate. scene information: the weather was sunny in the morning and it started to rain in the afternoon. many people enjoy reading books in the library on weekends. the train arrived at the station ten minutes later than scheduled. a small bird was singing in the garden near the old tree. the museum opens at nine and closes at five every day except monday. the weather was sunny in the morning and it |
| base_short_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "left of", "object": "wooden cabinet"}] |
| base_short_nl | put the bowl on the plate. scene information: the black bowl is to the left of the wooden cabinet. |
| base_full_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "in front of", "object": "plate"}, {"subject": "black bowl", "relation": "left of", "object": "cream cheese"}, {"subject": "cream cheese", "relation": "right of", "object": "black bowl"}, {"subject": "cream cheese", "relation": "in front of", "object": "wine bottle"}, {"subject": "wine bottle", "relation": "behind", "object": "cream cheese"}, {"subject": "wine bottle", "relation": "right of", "object": "plate"}, {"subject": "plate", "relation": "behind", "object": "black bowl"}, {"subject": "plate", "relation": "left of", "object": "wine bottle"}] |
| base_full_nl | put the bowl on the plate. scene information: the black bowl is in front of the plate. the black bowl is to the left of the cream cheese. the cream cheese is to the right of the black bowl. the cream cheese is in front of the wine bottle. the wine bottle is behind the cream cheese. the wine bottle is to the right of the plate. the plate is behind the black bowl. the plate is to the left of the wine bottle. |
| base_wrong_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "right of", "object": "wooden cabinet"}] |
| base_wrong_nl | put the bowl on the plate. scene information: the black bowl is to the right of the wooden cabinet. |

## task 2: 標準＋隠れ

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, behind, wine rack) |
| base_full | put the bowl on the plate. scene information: (black bowl, behind, wine rack); (black bowl, behind, wine bottle); (cream cheese, left of, plate); (cream cheese, left of, wine bottle); (wine bottle, left of, wine rack); (wine bottle, right of, cream cheese); (plate, right of, cream cheese); (plate, left of, wooden cabinet) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, in front of, wine rack) |
| sg_command | put the black bowl behind the wine rack on the plate |
| base_irrelevant | put the bowl on the plate. scene information: the weather was sunny in the morning and it started to rain in the afternoon. many people enjoy reading books in the library on weekends. the train arrived at the station ten minutes later than scheduled. a small bird was singing in the garden near the old tree. the museum opens at nine and closes at five every day except monday. the weather was sunny in the morning and |
| base_short_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "behind", "object": "wine rack"}] |
| base_short_nl | put the bowl on the plate. scene information: the black bowl is behind the wine rack. |
| base_full_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "behind", "object": "wine rack"}, {"subject": "black bowl", "relation": "behind", "object": "wine bottle"}, {"subject": "cream cheese", "relation": "left of", "object": "plate"}, {"subject": "cream cheese", "relation": "left of", "object": "wine bottle"}, {"subject": "wine bottle", "relation": "left of", "object": "wine rack"}, {"subject": "wine bottle", "relation": "right of", "object": "cream cheese"}, {"subject": "plate", "relation": "right of", "object": "cream cheese"}, {"subject": "plate", "relation": "left of", "object": "wooden cabinet"}] |
| base_full_nl | put the bowl on the plate. scene information: the black bowl is behind the wine rack. the black bowl is behind the wine bottle. the cream cheese is to the left of the plate. the cream cheese is to the left of the wine bottle. the wine bottle is to the left of the wine rack. the wine bottle is to the right of the cream cheese. the plate is to the right of the cream cheese. the plate is to the left of the wooden cabinet. |
| base_wrong_json | put the bowl on the plate. scene information: [{"subject": "black bowl", "relation": "in front of", "object": "wine rack"}] |
| base_wrong_nl | put the bowl on the plate. scene information: the black bowl is in front of the wine rack. |

## task 3: 標準＋隠れ（おとりあり）

対象: black bowl 1（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
| base_full | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack); (black bowl 1, behind, wine bottle); (black bowl 2, in front of, wine bottle); (black bowl 2, right of, cream cheese); (cream cheese, left of, black bowl 2); (cream cheese, left of, plate); (wine bottle, behind, black bowl 2); (wine bottle, left of, wine rack); (plate, in front of, black bowl 2); (plate, right of, cream cheese) |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet) |
| sg_command | put the black bowl behind the wine rack on the plate |
| base_irrelevant | put the bowl on the plate. scene information: the weather was sunny in the morning and it started to rain in the afternoon. many people enjoy reading books in the library on weekends. the train arrived at the station ten minutes later than scheduled. a small bird was singing in the garden near the old tree. the museum opens at nine and closes at five every day except monday. the weather was sunny in the morning and it started to rain in the afternoon. many people enjoy reading books in the library on weekends. the train arrived at the station ten minutes later than scheduled. a small bird was |
| base_short_json | put the bowl on the plate. scene information: [{"subject": "black bowl 1", "relation": "behind", "object": "wine rack"}] |
| base_short_nl | put the bowl on the plate. scene information: the black bowl 1 is behind the wine rack. |
| base_full_json | put the bowl on the plate. scene information: [{"subject": "black bowl 1", "relation": "behind", "object": "wine rack"}, {"subject": "black bowl 1", "relation": "behind", "object": "wine bottle"}, {"subject": "black bowl 2", "relation": "in front of", "object": "wine bottle"}, {"subject": "black bowl 2", "relation": "right of", "object": "cream cheese"}, {"subject": "cream cheese", "relation": "left of", "object": "black bowl 2"}, {"subject": "cream cheese", "relation": "left of", "object": "plate"}, {"subject": "wine bottle", "relation": "behind", "object": "black bowl 2"}, {"subject": "wine bottle", "relation": "left of", "object": "wine rack"}, {"subject": "plate", "relation": "in front of", "object": "black bowl 2"}, {"subject": "plate", "relation": "right of", "object": "cream cheese"}] |
| base_full_nl | put the bowl on the plate. scene information: the black bowl 1 is behind the wine rack. the black bowl 1 is behind the wine bottle. the black bowl 2 is in front of the wine bottle. the black bowl 2 is to the right of the cream cheese. the cream cheese is to the left of the black bowl 2. the cream cheese is to the left of the plate. the wine bottle is behind the black bowl 2. the wine bottle is to the left of the wine rack. the plate is in front of the black bowl 2. the plate is to the right of the cream cheese. |
| base_wrong_json | put the bowl on the plate. scene information: [{"subject": "black bowl 1", "relation": "left of", "object": "wooden cabinet"}] |
| base_wrong_nl | put the bowl on the plate. scene information: the black bowl 1 is to the left of the wooden cabinet. |
