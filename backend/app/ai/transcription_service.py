from app.ai.transcription_provider import TranscriptionProvider
from app.ai.groq_transcription_provider import GroqTranscriptionProvider
from app.ai.mock_transcription_provider import MockTranscriptionProvider
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TranscriptionService:
    def __init__(self):
        self.providers: dict[str, TranscriptionProvider] = {
            "groq": GroqTranscriptionProvider(),
            "mock": MockTranscriptionProvider(),
        }

    async def transcribe(self, file_path: str) -> str:
        """Транскрибирует файл с fallback-логикой."""
        provider_name = settings.TRANSCRIPTION_PROVIDER or "groq"
        provider = self.providers.get(provider_name, self.providers["mock"])

        try:
            logger.info("transcription_attempt", provider=provider_name, file_path=file_path)
            result = await provider.transcribe(file_path)
            logger.info("transcription_success", provider=provider_name)
            return result
        except Exception as e:
            logger.error("transcription_failed", provider=provider_name, error=str(e))

            if provider_name != "mock":
                logger.warning("falling_back_to_mock_transcription")
                mock_provider = self.providers["mock"]
                return await mock_provider.transcribe(file_path)

            raise


transcription_service = TranscriptionService()