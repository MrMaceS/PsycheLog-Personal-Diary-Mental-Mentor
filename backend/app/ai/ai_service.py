from fastapi import HTTPException, status

from app.ai.provider import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.models.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AIService:
    def __init__(self):
        # В будущем здесь будет: [GeminiProvider(), GroqProvider(), MockAIProvider()]
        # Порядок важен: сначала основные, в конце fallback (Mock)
        self.providers: list[AIProvider] = [MockAIProvider()]

    async def summarize_entry(self, text: str, user: User, mood: str | None = None) -> dict[str, str]:
        """
        Генерирует резюме с проверкой согласий и fallback-логикой.
        """

        if not user.consent_cloud_ai or not user.consent_data_processing:
            logger.warning(
                "ai_access_denied_due_to_consents",
                user_id=user.id,
                consent_cloud_ai=user.consent_cloud_ai,
                consent_data_processing=user.consent_data_processing,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Облачный AI недоступен. Проверьте настройки согласий в профиле.",
            )

        last_exception = None
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                logger.info("ai_provider_attempt", provider=provider_name, user_id=user.id)
                result = await provider.summarize(text, mood)
                logger.info("ai_provider_success", provider=provider_name, user_id=user.id)
                return result
            except Exception as e:
                logger.error(
                    "ai_provider_failed",
                    provider=provider_name,
                    user_id=user.id,
                    error=str(e),
                )
                last_exception = e
                continue

        logger.error("all_ai_providers_failed", user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис AI временно недоступен. Попробуйте позже.",
        )

    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """
        Универсальный метод для генерации текста (используется в медиации).
        """
        last_exception = None
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                logger.info("ai_generate_attempt", provider=provider_name)
                result = await provider.generate(prompt, system_prompt)
                logger.info("ai_generate_success", provider=provider_name)
                return result
            except Exception as e:
                logger.error(
                    "ai_generate_failed",
                    provider=provider_name,
                    error=str(e),
                )
                last_exception = e
                continue

        logger.error("all_ai_generate_providers_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис AI временно недоступен. Попробуйте позже.",
        )


ai_service = AIService()