# Данные о стилях фотосессий
# В продакшене можно хранить в БД или загружать из CMS

STYLES = [
    # === НОВЫЕ СТИЛИ ===
    {
        "id": "ice_cube",
        "name": "Ледяной куб",
        "category": "effect",
        "image": "/images/styles/ice_cube.jpg",  # TODO: заглушка
        "prompt": "Ice cube effect"
    },
    {
        "id": "winter_triptych",
        "name": "Зимний триптих",
        "category": "look",
        "image": "/images/styles/winter_triptych.jpg",  # TODO: заглушка
        "prompt": "Winter triptych collage"
    },
    # === БАЗОВЫЕ СТИЛИ ===
    {
        "id": "balloons",
        "name": "С шариками",
        "category": "effect",
        "image": "/images/styles/balloons.jpg",
        "prompt": "Transform this photo into a celebratory scene with colorful balloons in the background, keeping the person's face and features intact, professional photography style"
    },
    {
        "id": "disneyland",
        "name": "В Диснейленде",
        "category": "look",
        "image": "/images/styles/disneyland.jpg",
        "prompt": "Transform this photo to look like it was taken at Disneyland with magical castle in the background, keeping the person's face and features intact, bright and cheerful atmosphere"
    },
    {
        "id": "luxury",
        "name": "Luxury-стиль",
        "category": "look",
        "image": "/images/styles/luxury.jpg",
        "prompt": "Transform this photo into a luxury fashion photoshoot style, elegant setting, high-end fashion magazine look, keeping the person's face and features intact"
    },
    {
        "id": "business",
        "name": "Деловой стиль",
        "category": "look",
        "image": "/images/styles/business.jpg",
        "prompt": "Transform this photo into a professional business portrait, corporate setting, confident pose, keeping the person's face and features intact"
    },
    {
        "id": "neon",
        "name": "Неоновый",
        "category": "effect",
        "image": "/images/styles/neon.jpg",
        "prompt": "Transform this photo with neon lighting effects, cyberpunk aesthetic, vibrant pink and blue neon glow, keeping the person's face and features intact"
    },
    {
        "id": "vintage",
        "name": "Ретро",
        "category": "effect",
        "image": "/images/styles/vintage.jpg",
        "prompt": "Transform this photo into a vintage 1970s style with warm color grading, film grain, and retro aesthetic, keeping the person's face and features intact"
    },
    {
        "id": "nature",
        "name": "На природе",
        "category": "new",
        "image": "/images/styles/nature.jpg",
        "prompt": "Transform this photo to a beautiful natural outdoor setting with soft golden hour lighting, lush greenery, keeping the person's face and features intact"
    },
    {
        "id": "studio",
        "name": "Студийный",
        "category": "new",
        "image": "/images/styles/studio.jpg",
        "prompt": "Transform this photo into a professional studio photoshoot with perfect lighting, clean background, keeping the person's face and features intact"
    },
    {
        "id": "beach",
        "name": "На пляже",
        "category": "new",
        "image": "/images/styles/beach.jpg",
        "prompt": "Transform this photo to a beautiful beach setting with ocean in the background, sunset lighting, keeping the person's face and features intact"
    },
    {
        "id": "cafe",
        "name": "В кафе",
        "category": "look",
        "image": "/images/styles/cafe.jpg",
        "prompt": "Transform this photo into a cozy cafe setting, warm ambient lighting, aesthetic coffee shop atmosphere, keeping the person's face and features intact"
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
