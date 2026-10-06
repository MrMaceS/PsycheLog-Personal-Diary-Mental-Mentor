from fastapi.security import HTTPBearer

# Глобальная security схема для авторизации
security = HTTPBearer(
    scheme_name="JWT",
    description="Access token из /api/v1/auth/login",
)