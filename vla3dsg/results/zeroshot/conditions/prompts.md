# vla3dsg_goal のシーンと指示文（初期状態 0）

## task 0: 標準

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_full | put the bowl on the plate. scene information: (black bowl, in front of, wine bottle); (black bowl, right of, cream cheese); (cream cheese, left of, black bowl); (cream cheese, left of, plate); (wine bottle, behind, black bowl); (wine bottle, left of, wine rack); (plate, in front of, black bowl); (plate, right of, cream cheese) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |
| target | put the black bowl on the plate |
| sg_command | put the black bowl to the left of the wooden cabinet on the plate |

## task 1: 場所シャッフル

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_full | put the bowl on the plate. scene information: (black bowl, in front of, plate); (black bowl, left of, cream cheese); (cream cheese, right of, black bowl); (cream cheese, in front of, wine bottle); (wine bottle, behind, cream cheese); (wine bottle, right of, plate); (plate, behind, black bowl); (plate, left of, wine bottle) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |
| target | put the black bowl on the plate |
| sg_command | put the black bowl to the left of the wooden cabinet on the plate |

## task 2: 標準＋隠れ

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, behind, wine rack) |
| base_full | put the bowl on the plate. scene information: (black bowl, behind, wine rack); (black bowl, behind, wine bottle); (cream cheese, left of, plate); (cream cheese, left of, wine bottle); (wine bottle, left of, wine rack); (wine bottle, right of, cream cheese); (plate, right of, cream cheese); (plate, left of, wooden cabinet) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, in front of, wine rack) |
| target | put the black bowl on the plate |
| sg_command | put the black bowl behind the wine rack on the plate |

## task 3: 標準＋隠れ（おとりあり）

対象: black bowl 1（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
| base_full | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack); (black bowl 1, behind, wine bottle); (black bowl 2, in front of, wine bottle); (black bowl 2, right of, cream cheese); (cream cheese, left of, black bowl 2); (cream cheese, left of, plate); (wine bottle, behind, black bowl 2); (wine bottle, left of, wine rack); (plate, in front of, black bowl 2); (plate, right of, cream cheese) |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet) |
| target | put the black bowl 1 on the plate |
| sg_command | put the black bowl behind the wine rack on the plate |
