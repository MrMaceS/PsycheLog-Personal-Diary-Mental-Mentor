from typing import Optional, List
from datetime import datetime,timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.diary import DiaryEntry
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DiaryService:
    """Сервис для управления записями дневника."""

    @staticmethod
    async def create_entry(
        db: AsyncSession,
        user_id: int,
        title: Optional[str],
        content: str,
        mood: Optional[str],
        tags: Optional[str],
    ) -> DiaryEntry:
        entry = DiaryEntry(
            user_id=user_id,
            title=title,
            content=content,
            mood=mood,
            tags=tags,
            is_deleted=False,
        )

        db.add(entry)
        await db.flush()

        logger.info(
            "diary_entry_created",
            entry_id=entry.id,
            user_id=user_id,
        )

        return entry

    @staticmethod
    async def get_entries_by_user(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[DiaryEntry]:
        stmt = (
            select(DiaryEntry)
            .where(DiaryEntry.user_id == user_id)
            .where(DiaryEntry.is_deleted == False)
            .order_by(DiaryEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_entry_by_id(
        db: AsyncSession,
        entry_id: int,
        user_id: int,
    ) -> Optional[DiaryEntry]:
        stmt = (
            select(DiaryEntry)
            .where(DiaryEntry.id == entry_id)
            .where(DiaryEntry.user_id == user_id)
            .where(DiaryEntry.is_deleted == False)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_entry(
        db: AsyncSession,
        entry: DiaryEntry,
        title: Optional[str] = None,
        content: Optional[str] = None,
        mood: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> DiaryEntry:
        if title is not None:
            entry.title = title
        if content is not None:
            entry.content = content
        if mood is not None:
            entry.mood = mood
        if tags is not None:
            entry.tags = tags

        entry.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(entry)

        logger.info(
            "diary_entry_updated",
            entry_id=entry.id,
        )

        return entry

    @staticmethod
    async def delete_entry(
        db: AsyncSession,
        entry: DiaryEntry,
    ) -> bool:
        entry.is_deleted = True

        await db.flush()

        logger.info(
            "diary_entry_deleted",
            entry_id=entry.id,
        )

        return True