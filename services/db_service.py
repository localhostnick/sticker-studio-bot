from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.sticker_pack import StickerPack
from models.history import History
from utils.logger import logger


class DatabaseService:
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession, 
        user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Fetch or register a user in the database."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Registered new user in DB: {user_id} (@{username})")
        else:
            # Update profile info if changed
            updated = False
            if user.username != username:
                user.username = username
                updated = True
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            
            user.last_active = datetime.now(timezone.utc)
            if updated:
                await session.commit()

        return user

    @staticmethod
    async def create_sticker_pack(
        session: AsyncSession,
        title: str,
        short_name: str,
        owner_id: int,
        sticker_count: int = 0,
        sticker_format: str = "static"
    ) -> StickerPack:
        """Record a newly created sticker pack in DB."""
        pack = StickerPack(
            title=title,
            short_name=short_name,
            owner_id=owner_id,
            sticker_count=sticker_count,
            sticker_format=sticker_format,
        )
        session.add(pack)
        await session.commit()
        await session.refresh(pack)
        return pack

    @staticmethod
    async def get_user_packs(session: AsyncSession, owner_id: int) -> List[StickerPack]:
        """Fetch all sticker packs created by a specific user."""
        result = await session.execute(
            select(StickerPack)
            .where(StickerPack.owner_id == owner_id)
            .order_by(StickerPack.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pack_by_short_name(session: AsyncSession, short_name: str) -> Optional[StickerPack]:
        """Fetch pack record by short_name."""
        result = await session.execute(
            select(StickerPack).where(StickerPack.short_name == short_name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_pack_count(session: AsyncSession, short_name: str, count: int) -> None:
        """Update sticker count of a pack."""
        await session.execute(
            update(StickerPack)
            .where(StickerPack.short_name == short_name)
            .values(sticker_count=count, updated_at=datetime.now(timezone.utc))
        )
        await session.commit()

    @staticmethod
    async def update_pack_title(session: AsyncSession, short_name: str, new_title: str) -> bool:
        """Update the title of a sticker pack in DB."""
        result = await session.execute(
            update(StickerPack)
            .where(StickerPack.short_name == short_name)
            .values(title=new_title, updated_at=datetime.now(timezone.utc))
        )
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def delete_pack(session: AsyncSession, short_name: str, owner_id: int) -> bool:
        """Delete pack record from DB if owned by owner_id."""
        result = await session.execute(
            delete(StickerPack)
            .where(StickerPack.short_name == short_name, StickerPack.owner_id == owner_id)
        )
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def log_history(
        session: AsyncSession,
        user_id: int,
        operation_type: str,
        details: Optional[str] = None,
        status: str = "SUCCESS"
    ) -> History:
        """Record an action in operation history log."""
        history = History(
            user_id=user_id,
            operation_type=operation_type,
            details=details,
            status=status
        )
        session.add(history)
        await session.commit()
        return history

    @staticmethod
    async def get_user_history(session: AsyncSession, user_id: int, limit: int = 15) -> List[History]:
        """Get recent operation history for a user."""
        result = await session.execute(
            select(History)
            .where(History.user_id == user_id)
            .order_by(History.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
