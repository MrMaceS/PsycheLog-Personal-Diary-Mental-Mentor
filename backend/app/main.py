from app.core.config import settings
from app.core.database import close_db
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    setup_logging()

    yield

    await close_db()


app = FastAPI(
    title="Emotional Support App API",
    description="Закрытое приложение для эмоциональной самопомощи",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Регистрация, вход, logout",
        },
        {
            "name": "Users",
            "description": "Профиль пользователя",
        },
        {
            "name": "Diary",
            "description": "Записи личного дневника",
        },
    ],
)


allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }