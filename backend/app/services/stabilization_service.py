import uuid
from typing import Dict, Any
from app.models.user import User
from app.core.logging_config import get_logger
from app.schemas.stabilization import StabilizationSessionResponse, ExerciseType

logger = get_logger(__name__)

# База безопасных, проверенных психологических упражнений (локальный кэш)
EXERCISES: Dict[str, Dict[str, Any]] = {
    "breathing": {
        "instruction": "Техника 'Квадратное дыхание': Вдох на 4 счета → Задержка на 4 счета → Выдох на 4 счета → Задержка на 4 счета. Повторите 4 раза.",
        "duration_seconds": 60,
    },
    "grounding_54321": {
        "instruction": "Техника заземления '5-4-3-2-1': Найдите вокруг себя 5 вещей, которые вы видите, 4, которые можете потрогать, 3, которые слышите, 2, которые чувствуете запахом, и 1, которую можете попробовать на вкус.",
        "duration_seconds": 120,
    },
    "affirmation": {
        "instruction": "Повторите про себя: 'Я в безопасности. Мои чувства важны. Этот момент пройдет. Я делаю всё, что могу, и этого достаточно'.",
        "duration_seconds": 30,
    }
}


class StabilizationService:
    @staticmethod
    def start_session(user: User) -> StabilizationSessionResponse:
        """
        Начинает сеанс стабилизации.
        Возвращает случайное (или первое доступное) упражнение.
        """
        import random
        exercise_key = random.choice(list(EXERCISES.keys()))
        exercise_data = EXERCISES[exercise_key]

        session_id = str(uuid.uuid4())

        can_use_ai = bool(user.consent_cloud_ai) and bool(user.consent_data_processing)

        logger.info(
            "stabilization_session_started",
            user_id=user.id,
            session_id=session_id,
            exercise_type=exercise_key,
        )

        return StabilizationSessionResponse(
            session_id=session_id,
            exercise_type=ExerciseType(exercise_key),
            instruction=exercise_data["instruction"],
            duration_seconds=exercise_data["duration_seconds"],
            can_use_ai_followup=can_use_ai,
        )

    @staticmethod
    def complete_session(
            user: User,
            session_id: str,
            mood_after: str | None = None,
            brief_note: str | None = None,
    ) -> dict:
        """
        Завершает сеанс стабилизации.
        Если разрешено, здесь можно было бы отправить brief_note в AI для мягкого анализа,
        но пока мы просто логируем завершение для сохранения приватности.
        """
        logger.info(
            "stabilization_session_completed",
            user_id=user.id,
            session_id=session_id,
            mood_after=mood_after,
            note_provided=bool(brief_note),
        )

        return {
            "message": "Сеанс завершен. Мы рады, что вы позаботились о своем состоянии.",
            "session_id": session_id,
        }