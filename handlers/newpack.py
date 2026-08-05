import shutil
import uuid
from pathlib import Path
from typing import List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from database import AsyncSessionLocal
from handlers.media_collector import handle_incoming_media
from keyboards.main_keyboard import get_cancel_keyboard, get_main_menu_keyboard
from keyboards.pack_keyboard import get_done_collecting_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.image_service import ImageService
from services.animated_service import AnimatedService
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger
from utils.progress import format_progress_message
from utils.short_name import generate_unique_short_name
from utils.typography import small_caps

WAITING_TITLE, WAITING_MEDIA = range(2)


@track_user
async def newpack_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /newpack command."""
    context.user_data.clear()
    context.user_data["session_id"] = uuid.uuid4().hex[:8]

    msg = (
        f"📦 <b>{small_caps('Create New Sticker Pack')}</b>\n\n"
        f"<i>{small_caps('Please enter a Title for your new sticker pack')} (e.g. My Cool Memes):</i>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())

    return WAITING_TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives pack title from user."""
    title = update.message.text.strip()
    if not title or len(title) > 64:
        await update.message.reply_text(
            f"⚠️ <i>{small_caps('Title must be between 1 and 64 characters long. Try again')}:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_TITLE

    context.user_data["pack_title"] = title
    bot_user = await context.bot.get_me()
    context.user_data["short_name"] = generate_unique_short_name(title, bot_user.username)

    msg = (
        f"✅ <b>{small_caps('Pack Title Set')}:</b> <code>{title}</code>\n\n"
        f"<i>{small_caps('Now send your sticker images')}:</i>\n"
        f"• {small_caps('Upload a single ZIP archive')}\n"
        f"• {small_caps('Or send multiple photos/documents at once')}\n\n"
        f"<i>{small_caps('Click Create Pack below when upload is complete')}.</i>"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_done_collecting_keyboard(0))
    return WAITING_MEDIA


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives photos/documents/ZIP files for the pack."""
    count, text_status = await handle_incoming_media(update, context)
    await update.message.reply_text(
        text_status,
        parse_mode="HTML",
        reply_markup=get_done_collecting_keyboard(count)
    )
    return WAITING_MEDIA


async def finish_pack_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes collected images and creates Telegram sticker pack."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    collected_files: List[Path] = context.user_data.get("collected_files", [])
    title = context.user_data.get("pack_title", "Custom Pack")
    short_name = context.user_data.get("short_name", "")

    if not collected_files:
        await query.edit_message_text(
            f"⚠️ <i>{small_caps('No files were received! Please upload images or a ZIP file.')}</i>",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_MEDIA

    # Register in queue service
    try:
        task_ctx = await QueueService.start_task(user.id, "Create Sticker Pack")
    except RuntimeError as e:
        await query.edit_message_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await query.edit_message_text(
        format_progress_message("Processing Images", 0, len(collected_files)),
        parse_mode="HTML"
    )

    processed_dir = collected_files[0].parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_paths: List[Path] = []

    try:
        # Step 1: Image Processing
        total = len(collected_files)
        detected_format = "static"

        for idx, src_file in enumerate(collected_files, start=1):
            task_ctx.check_cancelled()
            ext = src_file.suffix.lower()

            if ext in (".gif", ".webm"):
                detected_format = "video"
                out_path = processed_dir / f"sticker_{idx:03d}.webm"
                processed = await AnimatedService.process_video_sticker(src_file, out_path)
            else:
                out_path = processed_dir / f"sticker_{idx:03d}.webp"
                processed = await ImageService.process_sticker_image(
                    input_source=src_file,
                    output_path=out_path,
                    target_format="WEBP",
                    exact_canvas_512=True
                )

            processed_paths.append(processed)
            
            if idx % 3 == 0 or idx == total:
                await status_msg.edit_text(
                    format_progress_message("Processing Images", idx, total),
                    parse_mode="HTML"
                )

        # Step 2: Upload to Telegram
        await status_msg.edit_text(
            format_progress_message("Uploading Stickers to Telegram", 0, total),
            parse_mode="HTML"
        )

        async def upload_progress(current: int, tot: int):
            task_ctx.check_cancelled()
            await status_msg.edit_text(
                format_progress_message("Uploading Stickers to Telegram", current, tot),
                parse_mode="HTML"
            )

        packs_info = await TelegramService.create_sticker_pack(
            bot=context.bot,
            user_id=user.id,
            title=title,
            short_name=short_name,
            sticker_file_paths=processed_paths,
            sticker_format=detected_format,
            progress_callback=upload_progress
        )

        # Step 3: Record in Database
        async with AsyncSessionLocal() as session:
            for p in packs_info:
                await DatabaseService.create_sticker_pack(
                    session=session,
                    title=p["title"],
                    short_name=p["short_name"],
                    owner_id=user.id,
                    sticker_count=p["count"],
                    sticker_format=detected_format
                )
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="CREATE",
                details=f"Created pack '{title}' with {total} stickers."
            )

        links_text = "\n".join([f"• <a href='{p['link']}'>{p['title']}</a> ({p['count']} {small_caps('stickers')})" for p in packs_info])
        final_text = (
            f"🎉 <b>{small_caps('Sticker Pack Created Successfully')}!</b>\n\n"
            f"<b>{small_caps('Generated Pack(s)')}:</b>\n{links_text}\n\n"
            f"✨ <i>{small_caps('Total Stickers Uploaded')}: {total}</i>"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=False)

    except Exception as e:
        logger.error(f"Error during pack creation: {e}")
        await status_msg.edit_text(f"❌ <b>{small_caps('Creation Failed')}:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)
        if collected_files:
            shutil.rmtree(collected_files[0].parent, ignore_errors=True)

    return ConversationHandler.END


def get_newpack_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("newpack", newpack_start),
            CallbackQueryHandler(newpack_start, pattern="^cmd_newpack$"),
        ],
        states={
            WAITING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title),
            ],
            WAITING_MEDIA: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_media),
                CallbackQueryHandler(finish_pack_creation, pattern="^finish_collection$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", newpack_start),
            CallbackQueryHandler(newpack_start, pattern="^action_cancel$"),
            CallbackQueryHandler(newpack_start, pattern="^cmd_start$"),
        ],
    )
