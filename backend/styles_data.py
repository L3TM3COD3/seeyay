# Данные о стилях фотосессий
# В продакшене можно хранить в БД или загружать из CMS

STYLES = [
    {
        "id": "ice_cube",
        "name": "Ледяной куб",
        "category": "effect",
        "image": "/images/styles/ice_cube.jpg",
        "prompt": "Ice cube effect"
    },
    {
        "id": "winter_triptych",
        "name": "Зимний триптих",
        "category": "look",
        "image": "/images/styles/winter_triptych.jpg",
        "prompt": "Winter triptych collage"
    }
]

CATEGORIES = [
    {"id": "all", "name": "Все"},
    {"id": "new", "name": "Новое"},
    {"id": "trending", "name": "Тренды"},
    {"id": "effect", "name": "Эффекты"},
    {"id": "look", "name": "Образ"},
    {"id": "for_her", "name": "Для неё"},
    {"id": "for_him", "name": "Для него"}
]


def get_styles_by_category(category: str = "all"):
    if category == "all":
        return STYLES
    return [s for s in STYLES if s["category"] == category]


def get_style_by_id(style_id: str):
    for style in STYLES:
        if style["id"] == style_id:
            return style
    return None
