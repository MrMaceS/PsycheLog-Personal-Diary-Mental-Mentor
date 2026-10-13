import asyncio
from app.ai.provider import AIProvider


class MockAIProvider(AIProvider):
    """Mock-провайдер для разработки и тестирования без реальных API-ключей."""

    async def summarize(self, text: str, mood: str | None = None) -> dict[str, str]:
        # Симуляция задержки сетевого запроса к AI (0.5 сек)
        await asyncio.sleep(0.5)

        mood_text = mood or "не указано"
        return {
            "summary": f"[AI-Резюме]: Запись длиной {len(text)} символов. Ключевая эмоция: {mood_text}.",
            "insights": "[AI-Инсайт]: Вы отлично справились с формулированием мыслей. Попробуйте сделать 3 глубоких вдоха, чтобы закрепить этот момент рефлексии."
        }