from .styles import router as styles_router
from .users import router as users_router
from .payments import router as payments_router
from .generate import router as generate_router

__all__ = ["styles_router", "users_router", "payments_router", "generate_router"]
