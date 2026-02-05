# Данные о стилях фотосессий
# В продакшене можно хранить в БД или загружать из CMS

# Базовая системная инструкция для всех стилей
DEFAULT_SYSTEM_INSTRUCTION = """You are an expert AI image transformation artist. 
Your task is to transform the provided photo while:
1. Preserving the person's facial features, identity, and likeness
2. Maintaining natural proportions and realistic appearance
3. Applying the requested style transformation seamlessly
4. Creating a high-quality, professional result

Generate a single transformed image based on the input photo and style prompt."""

STYLES = [
    {
        "id": "ice_cube",
        "name": "Ледяной куб",
        "category": "effect",
        "image": "/images/styles/ice_cube.jpg",
        "prompt": """TASK: Photo edit (image-to-image). Use the uploaded photo as the ONLY truth source.

ABSOLUTE IDENTITY LOCK (CRITICAL):
Keep the person 1:1 identical to the uploaded photo: same face, age, skin tone, skin texture/pores, moles/scars, eye shape, nose, lips, jawline, eyebrows, hairstyle, hair color, body proportions, height/weight impression, pose, expression. Do NOT beautify, do NOT retouch, do NOT change facial symmetry.

KEEP ORIGINAL PHOTO INTACT:
Preserve the original background, clothing, framing, camera angle, perspective, lighting direction, shadows, and depth-of-field EXACTLY as in the input photo. The input photo is the base layer.

EDIT ONLY THIS EFFECT:
Add a transparent, realistic ice cube enclosing the person (the person is inside the cube). The cube must look physically correct: clear ice with internal micro-cracks, subtle trapped air bubbles, and a light frost/hoarfrost rim along edges and corners. Add small melt droplets and thin water streaks on the outer surface, with realistic specular highlights. The cube must match the original scene perspective (correct vanishing lines), scale, and contact with the ground/surface if visible. Background behind the cube should be subtly refracted/distorted through the ice, but the person's face must remain undistorted and fully recognizable.

COLOR & QUALITY:
Photorealistic. Preserve original color grading; only minimal coolness shift caused by ice refraction. Ultra-detailed textures (ice, frost, droplets). Highres, 8k, sharp.

CONSTRAINTS (NO):
No face change, no body reshaping, no new person, no extra limbs/fingers, no plastic skin, no anime/cartoon, no painterly look, no blur on the face, no text, no watermark, no logos.""",
        "system_instruction": DEFAULT_SYSTEM_INSTRUCTION,
    },
    {
        "id": "winter_triptych",
        "name": "Зимний триптих",
        "category": "look",
        "image": "/images/styles/winter_triptych.jpg",
        "prompt": """TASK: Generate a single ultra-detailed cinematic triptych collage (one image containing 3 connected frames). Use the uploaded photo as the ONLY identity reference for the woman.

ABSOLUTE IDENTITY LOCK (CRITICAL):
The woman must be 1:1 identical to the uploaded photo in ALL three frames: same face, age, eye shape, nose, lips, jawline, eyebrows, hair color and hairline, skin tone and natural skin texture/pores, moles/scars, body proportions. No beautification, no plastic skin, no symmetry changes.

LAYOUT (ONE IMAGE, 3 FRAMES):
Create a vertical triptych collage with three stacked frames, thin clean borders, editorial layout.
Frame 1 (top): close-up portrait. The woman's face inside a voluminous ivory fur hood. Snowflakes on eyelashes and on the lips. Natural glowing makeup with subtle "frost" highlight, soft blush, nude matte lips. Calm, cold gaze. Overcast winter light, cool blue-gray tones.
Frame 2 (middle): wide shot from behind. The woman stands on a frozen lake wearing a fur coat with hood. In the distance: a small wooden cabin and a pine forest partially covered by fog, lonely atmosphere. Same winter light, muted palette.
Frame 3 (bottom): car interior. The woman sits in a dark car, wrapped in the same fur coat, eyes closed. Outside the window: snowy landscape motion blur. Interior has warmer tones for cinematic contrast, but the woman's identity remains unchanged.

CINEMATIC PHOTOREALISM:
Soft overcast daylight in outdoor frames; warm practical interior light in car frame. High fidelity materials: fur texture, snow crystals, fog, glass reflections. Highres, 4k/8k look, sharp.

CONSTRAINTS (NO):
No face change, no different person, no extra limbs/fingers, no stylization (no illustration), no text, no watermark, no logos.""",
        "system_instruction": DEFAULT_SYSTEM_INSTRUCTION,
    },
    {
        "id": "placeholder_3",
        "name": "Скоро...",
        "category": "new",
        "image": "/images/styles/placeholder.jpg",
        "placeholder": True,
        "prompt": "",
        "system_instruction": "",
    },
    {
        "id": "placeholder_4",
        "name": "Скоро...",
        "category": "new",
        "image": "/images/styles/placeholder.jpg",
        "placeholder": True,
        "prompt": "",
        "system_instruction": "",
    }
]

CATEGORIES = [
    {"id": "all", "name": "Все"},
    {"id": "effect", "name": "Эффект"},
    {"id": "look", "name": "Образ"},
    {"id": "new", "name": "Новинка"}
]


def get_styles_by_category(category: str = "all"):
    """Получить стили по категории"""
    if category == "all":
        return STYLES
    return [s for s in STYLES if s["category"] == category]


def get_style_by_id(style_id: str):
    """Получить стиль по ID"""
    for style in STYLES:
        if style["id"] == style_id:
            return style
    return None


def get_all_style_ids():
    """Получить все ID стилей"""
    return [s["id"] for s in STYLES]
