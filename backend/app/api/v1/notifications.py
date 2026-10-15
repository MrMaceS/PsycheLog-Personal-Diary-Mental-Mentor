from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.services.notification_service import NotificationService
from app.api.v1.diary import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
):
    """Получение списка уведомлений пользователя."""
    import json

    notifications = await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    unread_count = await NotificationService.get_unread_count(
        db=db,
        user_id=current_user.id,
    )

    response_notifications = []
    for notification in notifications:
        data_dict = None
        if notification.data:
            try:
                data_dict = json.loads(notification.data)
            except:
                data_dict = None

        response_notifications.append(
            NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type,
                title=notification.title,
                message=notification.message,
                data=data_dict,
                is_read=notification.is_read,
                read_at=notification.read_at,
                created_at=notification.created_at,
            )
        )

    return NotificationListResponse(
        notifications=response_notifications,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
        notification_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Пометка уведомления как прочитанного."""
    import json

    notification = await NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено",
        )

    data_dict = None
    if notification.data:
        try:
            data_dict = json.loads(notification.data)
        except:
            data_dict = None

    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        data=data_dict,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


@router.patch("/read-all")
async def mark_all_notifications_read(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Пометка всех уведомлений как прочитанных."""
    count = await NotificationService.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )

    return {"message": f"Помечено как прочитанные: {count} уведомлений"}