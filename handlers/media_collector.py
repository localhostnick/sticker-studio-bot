import uuid
from pathlib import Path
from typing import List, Tuple
from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from services.zip_service import ZipService
from keyboards.pack_keyboard import get_done_collecting_keyboard
from utils.logger import logger

SUPPORTED_MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".webm"}


async def handle_incoming_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[int, str]:
    """Downloads incoming photo/document/ZIP media into user session directory.
    
    Returns (total_collected_count, status_message)
    """
    user_id = update.effective_user.id
    user_dir = settings.TEMP_DIRECTORY / f"user_{user_id}_{context.user_data.get('session_id', 'default')}"
    user_dir.mkdir(parents=True, exist_ok=True)

    if "collected_files" not in context.user_data:
        context.user_data["collected_files"] = []

    collected_files: List[Path] = context.user_data["collected_files"]
    message = update.message

    if not message:
        return len(collected_files), "No message detected."

    # Case 1: ZIP Archive Upload
    if message.document and message.document.file_name and message.document.file_name.lower().endswith(".zip"):
        doc = message.document
        if doc.file_size and doc.file_size > settings.MAX_UPLOAD_SIZE:
            return len(collected_files), "❌ ZIP file exceeds max allowed size (50MB)."

        zip_target = user_dir / f"archive_{uuid.uuid4().hex[:6]}.zip"
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(custom_path=zip_target)

        extract_dir = user_dir / f"zip_extract_{uuid.uuid4().hex[:6]}"
        try:
            extracted_media = await ZipService.extract_and_scan_zip(zip_target, extract_dir)
            if not extracted_media:
                return len(collected_files), "⚠️ No valid images (.png, .jpg, .webp, .gif, .webm) found in ZIP archive."
            
            collected_files.extend(extracted_media)
            return len(collected_files), f"✅ Extracted {len(extracted_media)} images from ZIP archive!"
        except Exception as e:
            logger.error(f"ZIP processing error: {e}")
            return len(collected_files), f"❌ Failed to extract ZIP: {str(e)}"

    # Case 2: Document Upload (PNG, JPG, WEBP, GIF, WEBM)
    elif message.document:
        doc = message.document
        ext = Path(doc.file_name or "").suffix.lower()
        if ext not in SUPPORTED_MEDIA_EXTENSIONS:
            return len(collected_files), f"⚠️ Unsupported document type '{ext}'. Please send PNG, JPG, WEBP, GIF, or WEBM."

        file_target = user_dir / f"doc_{len(collected_files)+1:03d}{ext}"
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(custom_path=file_target)
        collected_files.append(file_target)
        return len(collected_files), f"✅ Added file: {doc.file_name}"

    # Case 3: Photo Upload
    elif message.photo:
        photo = message.photo[-1]  # Highest resolution
        file_target = user_dir / f"photo_{len(collected_files)+1:03d}.jpg"
        tg_file = await context.bot.get_file(photo.file_id)
        await tg_file.download_to_drive(custom_path=file_target)
        collected_files.append(file_target)
        return len(collected_files), "✅ Added photo."

    return len(collected_files), "⚠️ Unrecognized file type."
