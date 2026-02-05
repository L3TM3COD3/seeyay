from .start import router as start_router
from .photo import router as photo_router
from .webapp import router as webapp_router
from .template_selection import router as template_selection_router
from .energy import router as energy_router

__all__ = [
    "start_router",
    "template_selection_router",
    "energy_router",
    "webapp_router",
    "photo_router"
]
