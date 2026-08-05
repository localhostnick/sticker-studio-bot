from functools import wraps
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

from database import AsyncSessionLocal
from services.db_service import DatabaseService
from utils.logger import logger


def track_user(func: Callable[..., Any]) -> Callable[..., Any]:
    """Middleware decorator that logs user activity and syncs profile with DB."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        effective_user = update.effective_user
        if effective_user:
            async with AsyncSessionLocal() as session:
                try:
                    await DatabaseService.get_or_create_user(
                        session=session,
                        user_id=effective_user.id,
                        username=effective_user.username,
                        first_name=effective_user.first_name,
                        last_name=effective_user.last_name,
                    )
                except Exception as e:
                    logger.error(f"Error updating user profile in middleware: {e}")

        return await func(update, context, *args, **kwargs)

    return wrapper
