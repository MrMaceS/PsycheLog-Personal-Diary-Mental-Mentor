from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from fastapi import HTTPException, status

from app.models.chat import Chat, chat_members, Message, ChatRole
from app.models.user import User
from app.core.logging_config import get_logger
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType

logger = get_logger(__name__)


class ChatService:
    @staticmethod
    async def create_chat(
            db: AsyncSession,
            creator: User,
            name: Optional[str],
            is_group: bool,
            member_usernames: List[str],
    ) -> Chat:
        """Создаёт чат и добавляет создателя и указанных участников."""
        if is_group and not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для группового чата необходимо указать название",
            )

        chat = Chat(
            name=name,
            is_group=is_group,
            created_by=creator.id,
        )
        db.add(chat)
        await db.flush()

        await db.execute(
            insert(chat_members).values(
                chat_id=chat.id,
                user_id=creator.id,
                role=ChatRole.OWNER
            )
        )

        for username in member_usernames:
            if username == creator.username:
                continue

            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning("chat_invite_user_not_found", username=username, chat_id=chat.id)
                continue

            await db.execute(
                insert(chat_members).values(
                    chat_id=chat.id,
                    user_id=user.id,
                    role=ChatRole.MEMBER
                )
            )

        await db.commit()
        await db.refresh(chat)

        logger.info("chat_created", chat_id=chat.id, creator_id=creator.id, is_group=is_group)
        return chat

    @staticmethod
    async def send_message(
        db: AsyncSession,
        chat_id: int,
        sender_id: int,
        content: Optional[str],
        media_attachment_id: Optional[int],
    ) -> Message:
        """Отправляет сообщение в чат после проверки, что пользователь является участником."""
        member_check = await db.execute(
            select(chat_members).where(
                chat_members.c.chat_id == chat_id,
                chat_members.c.user_id == sender_id,
            )
        )
        if not member_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этого чата",
            )

        if not content and not media_attachment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сообщение должно содержать текст или медиафайл",
            )

        message = Message(
            chat_id=chat_id,
            user_id=sender_id,
            content=content,
            media_attachment_id=media_attachment_id,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        logger.info("message_sent", message_id=message.id, chat_id=chat_id, sender_id=sender_id)

        sender_result = await db.execute(
            select(User).where(User.id == sender_id)
        )
        sender = sender_result.scalar_one_or_none()
        sender_name = sender.display_name if sender else "Кто-то"

        members_result = await db.execute(
            select(chat_members.c.user_id).where(chat_members.c.chat_id == chat_id)
        )
        member_ids = [row[0] for row in members_result.all()]

        for member_id in member_ids:
            if member_id != sender_id:
                await NotificationService.create_notification(
                    db=db,
                    user_id=member_id,
                    notification_type=NotificationType.CHAT_MESSAGE,
                    title=f"Новое сообщение от {sender_name}",
                    message=content or "[Медиа]",
                    data={
                        "chat_id": chat_id,
                        "message_id": message.id,
                        "sender_id": sender_id,
                    },
                )

        await db.commit()

        return message

    @staticmethod
    async def delete_message(
            db: AsyncSession,
            message_id: int,
            current_user: User,
    ) -> Message:
        """Мягко удаляет сообщение. Пользователь может удалить только СВОЁ сообщение."""
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сообщение не найдено",
            )

        if message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете удалять только свои сообщения",
            )

        message.is_deleted = True
        message.deleted_by_id = current_user.id
        message.content = "[Сообщение удалено]"

        await db.commit()
        await db.refresh(message)

        logger.info("message_deleted", message_id=message.id, deleted_by=current_user.id)
        return message