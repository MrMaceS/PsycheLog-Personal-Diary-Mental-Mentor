from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "psychelog_worker",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)

# Конфигурация Celery
celery_app.conf.update(
    # Сериализация задач
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc=True,

    task_acks_late=True,
    worker_prefetch_multiplier=1,

    result_expires=3600,  # Результаты хранятся 1 час

    # Автообнаружение задач
    include=[
        "app.workers.account_cleanup_tasks",
        # "app.workers.transcription_tasks",  # Спринт 4
        # "app.workers.ai_tasks",             # Спринт 3
        # "app.workers.media_cleanup_tasks",  # Спринт 4
        # "app.workers.notification_tasks",   # Спринт 5
    ],
)

celery_app.conf.task_routes = {
    "app.workers.account_cleanup_tasks.*": {"queue": "cleanup"},
    # "app.workers.transcription_tasks.*": {"queue": "ai"},
    # "app.workers.ai_tasks.*": {"queue": "ai"},
}