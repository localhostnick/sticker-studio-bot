import asyncio
import os
import zipfile
import httpx
from pathlib import Path
from typing import List, Callable, Optional, Tuple
from telegram import Bot, StickerSet

from services.telegram_service import TelegramService
from services.image_service import ImageService
from utils.logger import logger


class PackDownloader:
    @classmethod
    async def download_pack_as_files(
        cls,
        bot: Bot,
        pack_name_or_link: str,
        dest_dir: Path,
        export_format: str = "PNG",  # PNG, WEBP, or BOTH
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[Path], str]:
        """Downloads all stickers from a pack and converts them to specified format."""
        # Extract short_name if URL given
        short_name = pack_name_or_link.split("/")[-1].strip()
        
        sticker_set: Optional[StickerSet] = await TelegramService.get_sticker_set(bot, short_name)
        if not sticker_set:
            raise ValueError(f"Sticker pack '{short_name}' not found or unreachable.")

        dest_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths: List[Path] = []
        total = len(sticker_set.stickers)

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, sticker in enumerate(sticker_set.stickers, start=1):
                # Fetch Telegram File info
                tg_file = await bot.get_file(sticker.file_id)
                file_url = tg_file.file_path

                # Download file bytes
                response = await client.get(file_url)
                response.raise_for_status()

                raw_bytes = response.content
                out_ext = "png" if export_format.upper() == "PNG" else "webp"
                out_file = dest_dir / f"sticker_{idx:03d}.{out_ext}"

                if sticker.is_animated or sticker.is_video:
                    # Save raw file for video/animated stickers
                    raw_ext = "tgs" if sticker.is_animated else "webm"
                    raw_file = dest_dir / f"sticker_{idx:03d}.{raw_ext}"
                    raw_file.write_bytes(raw_bytes)
                    downloaded_paths.append(raw_file)
                else:
                    # Process static image to requested format
                    await ImageService.process_sticker_image(
                        input_source=raw_bytes,
                        output_path=out_file,
                        target_format=export_format.upper(),
                        exact_canvas_512=True
                    )
                    downloaded_paths.append(out_file)

                if progress_callback:
                    await progress_callback(idx, total)

        return downloaded_paths, sticker_set.title

    @classmethod
    async def create_zip_archive(
        cls,
        file_paths: List[Path],
        zip_output_path: Path
    ) -> Path:
        """Packages downloaded sticker files into a ZIP archive."""
        zip_output_path.parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_running_loop()
        def _zip_sync():
            with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in file_paths:
                    zip_file.write(file_path, arcname=file_path.name)

        await loop.run_in_executor(None, _zip_sync)
        logger.info(f"Created ZIP archive at {zip_output_path} with {len(file_paths)} files.")
        return zip_output_path
