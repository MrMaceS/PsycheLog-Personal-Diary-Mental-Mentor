import asyncio
from app.core.database import init_db


async def test():
    print("Инициализация БД...")
    await init_db()
    print("Готово! Таблицы созданы.")


if __name__ == "__main__":
    asyncio.run(test())