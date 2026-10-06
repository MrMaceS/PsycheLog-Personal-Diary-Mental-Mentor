from app.core.config import settings


print("ENVIRONMENT:", settings.ENVIRONMENT)
print("DEBUG:", settings.DEBUG)
print("DATABASE_URL:", settings.DATABASE_URL[:50] + "...")
print("JWT_SECRET_KEY:", settings.JWT_SECRET_KEY[:10] + "...")
print("Готово!")