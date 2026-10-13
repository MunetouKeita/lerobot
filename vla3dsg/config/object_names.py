"""SG のノード名に使う、LIBERO の物体カテゴリの読みやすい名前。

登録がないカテゴリは、カテゴリ名の "_" を空白に置き換えて使う。
"""

OBJECT_NAMES = {
    "akita_black_bowl": "black bowl",
    "cookies": "cookie box",
    "glazed_rim_porcelain_ramekin": "ramekin",
    "plate": "plate",
    "wooden_cabinet": "wooden cabinet",
    "flat_stove": "stove",
    "alphabet_soup": "alphabet soup",
    "bbq_sauce": "bbq sauce",
    "cream_cheese": "cream cheese",
    "new_salad_dressing": "salad dressing",
    "salad_dressing": "salad dressing",
    "tomato_sauce": "tomato sauce",
    "orange_juice": "orange juice",
    "chocolate_pudding": "chocolate pudding",
    "wine_bottle": "wine bottle",
    "wine_rack": "wine rack",
    "moka_pot": "moka pot",
    "white_yellow_mug": "yellow and white mug",
    "porcelain_mug": "white mug",
    "red_coffee_mug": "red coffee mug",
    "black_book": "black book",
    "yellow_book": "yellow book",
    "desk_caddy": "desk caddy",
}

# 物体の領域（サイト）の読みやすい名前と、その領域との関係（on / in）
REGION_RELATIONS = {
    "top_region": ("in", "top drawer of {parent}"),
    "middle_region": ("in", "middle drawer of {parent}"),
    "bottom_region": ("in", "bottom drawer of {parent}"),
    "top_side": ("on", "top of {parent}"),
    "cook_region": ("on", "{parent}"),
}
