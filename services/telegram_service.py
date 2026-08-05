from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from telegram import Bot, InputSticker, StickerSet
from telegram.error import TelegramError

from config import settings
from utils.logger import logger
from utils.rate_limiter import retry_telegram_api


class TelegramService:
    @staticmethod
    async def create_sticker_pack(
        bot: Bot,
        user_id: int,
        title: str,
        short_name: str,
        sticker_file_paths: List[Path],
        emojis: Optional[List[str]] = None,
        sticker_format: str = "static",
        progress_callback: Optional[Callable[[int, int], Any]] = None
    ) -> List[Dict[str, Any]]:
        """Creates one or multiple sticker packs (split if sticker count exceeds Telegram limits).
        
        Returns a list of created pack dictionaries: [{'title': ..., 'short_name': ..., 'count': ...}, ...]
        """
        if not sticker_file_paths:
            raise ValueError("No sticker files provided for pack creation.")

        limit = settings.MAX_IMAGES if sticker_format == "static" else settings.MAX_VIDEO_STICKERS
        
        # Partition stickers into chunks based on Telegram limits
        chunks = [
            sticker_file_paths[i:i + limit] 
            for i in range(0, len(sticker_file_paths), limit)
        ]

        default_emojis = emojis if emojis else ["😀"]
        created_packs = []
        total_stickers = len(sticker_file_paths)
        processed_count = 0

        for index, chunk in enumerate(chunks, start=1):
            # Format sub-pack title & short_name if split into multiple parts
            current_title = f"{title} Part {index}" if len(chunks) > 1 else title
            if len(chunks) > 1:
                # Append part number before suffix
                base_name, _, suffix = short_name.rpartition("_by_")
                current_short_name = f"{base_name}_p{index}_by_{suffix}" if suffix else f"{short_name}_p{index}"
            else:
                current_short_name = short_name

            logger.info(f"Creating Telegram sticker set '{current_short_name}' for user {user_id} with {len(chunk)} stickers.")

            # Create initial sticker pack with the first sticker in the chunk
            first_path = chunk[0]
            with open(first_path, "rb") as f:
                first_input = InputSticker(
                    sticker=f,
                    emoji_list=[default_emojis[0 % len(default_emojis)]],
                    format=sticker_format
                )
                
                await retry_telegram_api(
                    bot.create_new_sticker_set,
                    user_id=user_id,
                    name=current_short_name,
                    title=current_title,
                    stickers=[first_input]
                )

            processed_count += 1
            if progress_callback:
                await progress_callback(processed_count, total_stickers)

            # Add remaining stickers to the created set
            for idx in range(1, len(chunk)):
                file_path = chunk[idx]
                emoji = default_emojis[idx % len(default_emojis)]
                
                with open(file_path, "rb") as f:
                    input_sticker = InputSticker(
                        sticker=f,
                        emoji_list=[emoji],
                        format=sticker_format
                    )
                    await retry_telegram_api(
                        bot.add_sticker_to_set,
                        user_id=user_id,
                        name=current_short_name,
                        sticker=input_sticker
                    )

                processed_count += 1
                if progress_callback:
                    await progress_callback(processed_count, total_stickers)

            created_packs.append({
                "title": current_title,
                "short_name": current_short_name,
                "count": len(chunk),
                "link": f"https://t.me/addstickers/{current_short_name}"
            })

        return created_packs

    @staticmethod
    async def add_stickers_to_existing_pack(
        bot: Bot,
        user_id: int,
        short_name: str,
        sticker_file_paths: List[Path],
        emojis: Optional[List[str]] = None,
        sticker_format: str = "static",
        progress_callback: Optional[Callable[[int, int], Any]] = None
    ) -> int:
        """Appends new stickers to an existing pack."""
        default_emojis = emojis if emojis else ["😀"]
        total = len(sticker_file_paths)
        added = 0

        for idx, file_path in enumerate(sticker_file_paths):
            emoji = default_emojis[idx % len(default_emojis)]
            with open(file_path, "rb") as f:
                input_sticker = InputSticker(
                    sticker=f,
                    emoji_list=[emoji],
                    format=sticker_format
                )
                await retry_telegram_api(
                    bot.add_sticker_to_set,
                    user_id=user_id,
                    name=short_name,
                    sticker=input_sticker
                )
            added += 1
            if progress_callback:
                await progress_callback(added, total)

        return added

    @staticmethod
    async def get_sticker_set(bot: Bot, name: str) -> Optional[StickerSet]:
        """Fetches sticker set info from Telegram."""
        try:
            return await retry_telegram_api(bot.get_sticker_set, name=name)
        except TelegramError as e:
            logger.warning(f"Failed to fetch sticker set {name}: {e}")
            return None

    @staticmethod
    async def delete_sticker_pack(bot: Bot, short_name: str) -> bool:
        """Deletes a sticker set created by the bot."""
        try:
            await retry_telegram_api(bot.delete_sticker_set, name=short_name)
            logger.info(f"Successfully deleted Telegram sticker set: {short_name}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to delete sticker set {short_name}: {e}")
            return False
