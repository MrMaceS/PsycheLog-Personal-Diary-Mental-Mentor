from abc import ABC, abstractmethod
from typing import Dict


class AIProvider(ABC):
    """Абстрактный базовый класс для всех AI-провайдеров."""

    @abstractmethod
    async def summarize(self, text: str, mood: str | None = None) -> Dict[str, str]:
        """
        Генерирует резюме и инсайты для текста.

        :param text: Исходный текст записи дневника.
        :param mood: Настроение пользователя (опционально, для контекста).
        :return: Словарь с ключами 'summary' и 'insights'.
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Универсальная генерация текста на основе промпта (используется для медиации).
        """
        pass