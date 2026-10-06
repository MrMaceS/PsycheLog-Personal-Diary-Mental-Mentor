from fastapi import APIRouter
from app.api.v1 import auth, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)

# Остальные роутеры будут добавлены позже
# api_router.include_router(diary.router)
# api_router.include_router(stabilization.router)
# api_router.include_router(chats.router)
# api_router.include_router(mediation.router)
# api_router.include_router(invitations.router)
# api_router.include_router(media.router)
# api_router.include_router(notifications.router)
# api_router.include_router(export.router)