import asyncio
from app.ai.transcription_provider import TranscriptionProvider

class MockTranscriptionProvider(TranscriptionProvider):
    """Mock-провайдер для тестов и fallback-логики."""

    async def transcribe(self, file_path: str) -> str:
        await asyncio.sleep(0.5)
        return (
            "[Транскрибация (Mock)]: Пользователь описывает свой день, "
            "упоминает рабочие задачи и легкую усталость. Настроение спокойное."
        )