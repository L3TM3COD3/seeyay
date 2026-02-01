from fastapi import APIRouter
from backend.styles_data import STYLES, CATEGORIES, get_styles_by_category, get_style_by_id

router = APIRouter(prefix="/api/styles", tags=["styles"])


@router.get("")
async def get_styles(category: str = "all"):
    """Получить список стилей по категории"""
    styles = get_styles_by_category(category)
    return {
        "styles": styles,
        "categories": CATEGORIES
    }


@router.get("/{style_id}")
async def get_style(style_id: str):
    """Получить информацию о конкретном стиле"""
    style = get_style_by_id(style_id)
    if not style:
        return {"error": "Style not found"}, 404
    return style
