import asyncio
from openai import OpenAI
from app.core.config import settings
from app.ai.transcription_provider import TranscriptionProvider
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class GroqTranscriptionProvider(TranscriptionProvider):
    def __init__(self):
        api_key = settings.GROQ_API_KEY or "dummy_key_for_fallback_initialization"
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )

    async def transcribe(self, file_path: str) -> str:
        """Вызывает Groq Whisper API для транскрибации."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_transcribe, file_path)

    def _sync_transcribe(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="text",
                language="ru",
            )
        return transcription.strip()