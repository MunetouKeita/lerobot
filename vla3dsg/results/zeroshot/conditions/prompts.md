# vla3dsg_goal のシーンと指示文（初期状態 0）

## task 0: 標準

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |

## task 1: 場所シャッフル

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, left of, wooden cabinet) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, right of, wooden cabinet) |

## task 2: 標準＋隠れ

対象: black bowl（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl, behind, wine rack) |
| base_wrong | put the bowl on the plate. scene information: (black bowl, in front of, wine rack) |

## task 3: 標準＋隠れ（おとりあり）

対象: black bowl 1（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet) |

## task 4: 標準＋見える方が正解（おとりは裏）

対象: black bowl 1（scenes.png の赤丸）

| 条件 | 指示文 |
|---|---|
| base | put the bowl on the plate |
| base_short | put the bowl on the plate. scene information: (black bowl 1, left of, wooden cabinet) |
| base_wrong | put the bowl on the plate. scene information: (black bowl 1, behind, wine rack) |
