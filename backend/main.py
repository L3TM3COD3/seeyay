from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.routers import styles_router, users_router, payments_router, generate_router
from backend.routers.webhooks import router as webhooks_router
from backend.routers.cron import router as cron_router


app = FastAPI(
    title="СИЯЙ AI API",
    description="Backend API для Telegram бота нейрофотосессий",
    version="1.0.0"
)

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(styles_router)
app.include_router(users_router)
app.include_router(payments_router)
app.include_router(generate_router)
app.include_router(webhooks_router)
app.include_router(cron_router)

# Статические файлы для изображений стилей
if os.path.exists("static"):
    app.mount("/images", StaticFiles(directory="static/images"), name="images")

# Статические файлы Mini App (после сборки)
if os.path.exists("mini-app/dist"):
    app.mount("/", StaticFiles(directory="mini-app/dist", html=True), name="mini-app")


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
