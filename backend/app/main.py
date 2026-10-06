from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
import uvicorn
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    setup_logging()
    if settings.ENVIRONMENT == "development":
        await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Emotional Support App API",
    description="Закрытое приложение для эмоциональной самопомощи",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Регистрация, вход, logout"},
        {"name": "Users", "description": "Профиль пользователя"},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)