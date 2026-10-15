from abc import ABC, abstractmethod

class TranscriptionProvider(ABC):
    """Абстрактный базовый класс для провайдеров транскрибации."""

    @abstractmethod
    async def transcribe(self, file_path: str) -> str:
        """
        Транскрибирует аудиофайл в текст.
        :param file_path: Путь к локальному аудиофайлу.
        :return: Текст транскрибации.
        """
        pass