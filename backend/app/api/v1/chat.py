from typing import List
from fastapi import (APIRouter, Depends, HTTPException,
                     status, WebSocket, WebSocketDisconnect,
                     Query)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import verify_token
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.models.chat import Chat, chat_members, Message
from app.schemas.chat import (
    CreateChatRequest,
    ChatResponse,
    ChatMemberResponse,
    CreateMessageRequest,
    MessageResponse,
)
from app.services.chat_service import ChatService
from app.api.v1.diary import get_current_user
from app.websocket.manager import manager

logger = get_logger(__name__)
router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("/",
             response_model=ChatResponse,
             status_code=status.HTTP_201_CREATED
             )
async def create_chat(
        request: CreateChatRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Создание чата (личного или группового) с приглашением участников."""
    chat = await ChatService.create_chat(
        db=db,
        creator=current_user,
        name=request.name,
        is_group=request.is_group,
        member_usernames=request.member_usernames,
    )

    result = await db.execute(
        select(chat_members).where(chat_members.c.chat_id == chat.id)
    )
    member_records = result.all()

    members_response = []
    for member in member_records:
        user_result = await db.execute(
            select(User).where(User.id == member.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            members_response.append(
                ChatMemberResponse(
                    user_id=user.id,
                    username=user.username,
                    display_name=user.display_name,
                    role=member.role,
                )
            )

    return ChatResponse(
        id=chat.id,
        name=chat.name,
        is_group=chat.is_group,
        created_by_id=chat.created_by,
        members=members_response,
        created_at=chat.created_at,
    )


@router.get("/", response_model=List[ChatResponse])
async def list_my_chats(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Список чатов, в которых участвует текущий пользователь."""
    result = await db.execute(
        select(chat_members.c.chat_id).where(
            chat_members.c.user_id == current_user.id
        )
    )
    chat_ids = [row[0] for row in result.all()]

    if not chat_ids:
        return []

    chats_result = await db.execute(
        select(Chat).where(Chat.id.in_(chat_ids))
    )
    chats = chats_result.scalars().all()

    response = []
    for chat in chats:
        members_result = await db.execute(
            select(chat_members).where(chat_members.c.chat_id == chat.id)
        )
        member_records = members_result.all()

        members_response = []
        for member in member_records:
            user_result = await db.execute(
                select(User).where(User.id == member.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                members_response.append(
                    ChatMemberResponse(
                        user_id=user.id,
                        username=user.username,
                        display_name=user.display_name,
                        role=member.role,
                    )
                )

        response.append(
            ChatResponse(
                id=chat.id,
                name=chat.name,
                is_group=chat.is_group,
                created_by_id=chat.created_by,
                members=members_response,
                created_at=chat.created_at,
            )
        )

    return response


@router.post(
    "/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
async def send_message(
        chat_id: int,
        request: CreateMessageRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Отправка сообщения в чат."""
    message = await ChatService.send_message(
        db=db,
        chat_id=chat_id,
        sender_id=current_user.id,
        content=request.content,
        media_attachment_id=request.media_attachment_id,
    )

    return MessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.user_id,
        sender_username=current_user.username,
        content=message.content,
        media_attachment_id=message.media_attachment_id,
        is_deleted=message.is_deleted,
        created_at=message.created_at,
        edited_at=message.edited_at,
    )


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def list_messages(
        chat_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Получение списка сообщений в чате."""
    member_check = await db.execute(
        select(chat_members).where(
            chat_members.c.chat_id == chat_id,
            chat_members.c.user_id == current_user.id,
        )
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    response = []
    for message in messages:
        sender_result = await db.execute(
            select(User).where(User.id == message.user_id)
        )
        sender = sender_result.scalar_one_or_none()

        response.append(
            MessageResponse(
                id=message.id,
                chat_id=message.chat_id,
                sender_id=message.user_id,
                sender_username=sender.username if sender else "unknown",
                content=message.content,
                media_attachment_id=message.media_attachment_id,
                is_deleted=message.is_deleted,
                created_at=message.created_at,
                edited_at=message.edited_at,
            )
        )

    return response


@router.delete("/messages/{message_id}")
async def delete_message(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Мягкое удаление сообщения (только своего)."""
    await ChatService.delete_message(
        db=db,
        message_id=message_id,
        current_user=current_user,
    )

    return {"message": "Сообщение удалено"}


@router.websocket("/ws/{chat_id}")
async def websocket_chat_endpoint(
        websocket: WebSocket,
        chat_id: int,
        token: str = Query(..., description="JWT access token"),
        db: AsyncSession = Depends(get_db),
):
    """
    WebSocket-эндпоинт для real-time обмена сообщениями в чате.
    Поддерживает отправку и получение сообщений в реальном времени.
    """
    payload = verify_token(token, token_type="access")
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    member_check = await db.execute(
        select(chat_members).where(
            chat_members.c.chat_id == chat_id,
            chat_members.c.user_id == user_id,
        )
    )
    if not member_check.scalar_one_or_none():
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()

            content = data.get("content")
            media_attachment_id = data.get("media_attachment_id")

            if not content and not media_attachment_id:
                continue

            message = await ChatService.send_message(
                db=db,
                chat_id=chat_id,
                sender_id=user_id,
                content=content,
                media_attachment_id=media_attachment_id,
            )

            sender_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            sender = sender_result.scalar_one_or_none()

            message_payload = {
                "type": "new_message",
                "data": {
                    "id": message.id,
                    "chat_id": message.chat_id,
                    "sender_id": message.user_id,
                    "sender_username": sender.username if sender else "unknown",
                    "content": message.content,
                    "media_attachment_id": message.media_attachment_id,
                    "is_deleted": message.is_deleted,
                    "created_at": message.created_at.isoformat(),
                }
            }

            members_result = await db.execute(
                select(chat_members.c.user_id).where(chat_members.c.chat_id == chat_id)
            )
            member_user_ids = [row[0] for row in members_result.all()]

            await manager.broadcast_to_chat(message_payload, member_user_ids)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("websocket_error", chat_id=chat_id, user_id=user_id, error=str(e))
        manager.disconnect(websocket, user_id)