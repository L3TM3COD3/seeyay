from .start import router as start_router
from .photo import router as photo_router
from .template_selection import router as template_selection_router
from .energy import router as energy_router
from .dev_commands import router as dev_commands_router  # DEV ONLY - REMOVE BEFORE PROD

__all__ = [
    "start_router",
    "template_selection_router",
    "energy_router",
    "photo_router",
    "dev_commands_router"  # DEV ONLY - REMOVE BEFORE PROD
]
