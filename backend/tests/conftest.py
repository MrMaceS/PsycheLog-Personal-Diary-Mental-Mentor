import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.core.database import Base
from app.core.config import settings

import app.models.user  # noqa: F401
import app.models.auth  # noqa: F401
import app.models.diary  # noqa: F401
import app.models.chat  # noqa: F401
import app.models.mediation  # noqa: F401
import app.models.notification  # noqa: F401


test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Создаём event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Эта фикстура запускается ОДИН раз перед всеми тестами.
    Она создаёт все таблицы в тестовой БД и удаляет их после.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
def client():
    """Фикстура HTTP-клиента для интеграционных тестов."""
    with TestClient(fastapi_app) as test_client:
        yield test_client