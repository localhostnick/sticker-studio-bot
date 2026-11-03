import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models.base import Base
from services.db_service import DatabaseService


@pytest.mark.asyncio
async def test_user_and_pack_crud():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        # Create user
        user = await DatabaseService.get_or_create_user(session, user_id=12345, username="testuser")
        assert user.id == 12345
        assert user.username == "testuser"

        # Create pack
        pack = await DatabaseService.create_sticker_pack(
            session=session,
            title="My Pack",
            short_name="my_pack_by_bot",
            owner_id=12345,
            sticker_count=5
        )
        assert pack.title == "My Pack"
        assert pack.short_name == "my_pack_by_bot"

        # Update pack title
        updated = await DatabaseService.update_pack_title(session, "my_pack_by_bot", "Renamed Pack")
        assert updated is True

        # Verify updated pack
        fetched = await DatabaseService.get_pack_by_short_name(session, "my_pack_by_bot")
        assert fetched is not None
        assert fetched.title == "Renamed Pack"

        # Delete pack
        deleted = await DatabaseService.delete_pack(session, "my_pack_by_bot", owner_id=12345)
        assert deleted is True

        # Verify deleted
        fetched_after = await DatabaseService.get_pack_by_short_name(session, "my_pack_by_bot")
        assert fetched_after is None

    await engine.dispose()
