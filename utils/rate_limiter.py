import asyncio
from typing import Callable, Any, TypeVar
from telegram.error import RetryAfter, TimedOut, NetworkError
from utils.logger import logger

T = TypeVar("T")


async def retry_telegram_api(
    func: Callable[..., Any], 
    *args: Any, 
    max_retries: int = 3, 
    **kwargs: Any
) -> Any:
    """Executes a Telegram API async function with retry backoff for rate limits."""
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except RetryAfter as e:
            wait_time = e.retry_after + 1
            logger.warning(f"Telegram API Rate Limit hit. Retrying after {wait_time}s (Attempt {attempt}/{max_retries})")
            await asyncio.sleep(wait_time)
        except (TimedOut, NetworkError) as e:
            wait_time = attempt * 2
            logger.warning(f"Telegram API Network issue: {e}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})")
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"Telegram API call failed: {e}")
            raise e

    # Final attempt
    return await func(*args, **kwargs)
