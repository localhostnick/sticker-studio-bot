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
from keyboards.pack_keyboard import get_packs_list_keyboard, get_done_collecting_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.image_service import ImageService
from services.animated_service import AnimatedService
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger
from utils.progress import format_progress_message

SELECT_PACK, WAITING_MEDIA = range(2)


@track_user
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /add command."""
    context.user_data.clear()
    context.user_data["session_id"] = uuid.uuid4().hex[:8]
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        user_packs = await DatabaseService.get_user_packs(session, user.id)

    if not user_packs:
        msg = "⚠️ You haven't created any sticker packs with this bot yet! Use /newpack first."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    msg = "📥 <b>Add Stickers to Existing Pack</b>\n\nSelect a pack below to append stickers to:"
    kb = get_packs_list_keyboard(user_packs, action_prefix="select_add")

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

    return SELECT_PACK


async def select_pack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback when user selects a pack."""
    query = update.callback_query
    await query.answer()

    short_name = query.data.split(":")[1]
    context.user_data["selected_pack_short_name"] = short_name

    msg = (
        f"✅ Selected Pack: <code>{short_name}</code>\n\n"
        f"Now send the new images to append:\n"
        f"• Send a <b>ZIP file</b>\n"
        f"• Or send multiple photos/documents\n\n"
        f"<i>Click 'Create Pack' / 'Finish' when ready.</i>"
    )
    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_done_collecting_keyboard(0))
    return WAITING_MEDIA


async def receive_add_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives photos/documents/ZIP files to append."""
    count, text_status = await handle_incoming_media(update, context)
    await update.message.reply_text(
        text_status,
        parse_mode="HTML",
        reply_markup=get_done_collecting_keyboard(count)
    )
    return WAITING_MEDIA


async def finish_add_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Appends collected stickers to the selected pack."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    collected_files: List[Path] = context.user_data.get("collected_files", [])
    short_name = context.user_data.get("selected_pack_short_name", "")

    if not collected_files:
        await query.edit_message_text("⚠️ No new stickers were uploaded!", reply_markup=get_cancel_keyboard())
        return WAITING_MEDIA

    try:
        task_ctx = await QueueService.start_task(user.id, "Add Stickers")
    except RuntimeError as e:
        await query.edit_message_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await query.edit_message_text(
        format_progress_message("Processing New Images...", 0, len(collected_files)),
        parse_mode="HTML"
    )

    processed_dir = collected_files[0].parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_paths: List[Path] = []

    try:
        total = len(collected_files)
        detected_format = "static"

        for idx, src_file in enumerate(collected_files, start=1):
            task_ctx.check_cancelled()
            ext = src_file.suffix.lower()

            if ext in (".gif", ".webm"):
                detected_format = "video"
                out_path = processed_dir / f"add_{idx:03d}.webm"
                processed = await AnimatedService.process_video_sticker(src_file, out_path)
            else:
                out_path = processed_dir / f"add_{idx:03d}.webp"
                processed = await ImageService.process_sticker_image(src_file, out_path)

            processed_paths.append(processed)

            if idx % 3 == 0 or idx == total:
                await status_msg.edit_text(
                    format_progress_message("Processing New Images...", idx, total),
                    parse_mode="HTML"
                )

        await status_msg.edit_text(
            format_progress_message("Appending to Telegram Pack...", 0, total),
            parse_mode="HTML"
        )

        async def upload_progress(current: int, tot: int):
            task_ctx.check_cancelled()
            await status_msg.edit_text(
                format_progress_message("Appending to Telegram Pack...", current, tot),
                parse_mode="HTML"
            )

        added_count = await TelegramService.add_stickers_to_existing_pack(
            bot=context.bot,
            user_id=user.id,
            short_name=short_name,
            sticker_file_paths=processed_paths,
            sticker_format=detected_format,
            progress_callback=upload_progress
        )

        # Update DB count
        tg_set = await TelegramService.get_sticker_set(context.bot, short_name)
        new_total = len(tg_set.stickers) if tg_set else 0

        async with AsyncSessionLocal() as session:
            await DatabaseService.update_pack_count(session, short_name, new_total)
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="ADD",
                details=f"Appended {added_count} stickers to pack '{short_name}'."
            )

        final_text = (
            f"🎉 <b>Stickers Appended Successfully!</b>\n\n"
            f"• <b>Pack Link:</b> <a href='https://t.me/addstickers/{short_name}'>https://t.me/addstickers/{short_name}</a>\n"
            f"• <b>Added Count:</b> +{added_count}\n"
            f"• <b>Total Pack Stickers:</b> {new_total}"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=False)

    except Exception as e:
        logger.error(f"Error appending stickers: {e}")
        await status_msg.edit_text(f"❌ <b>Failed to add stickers:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)
        if collected_files:
            shutil.rmtree(collected_files[0].parent, ignore_errors=True)

    return ConversationHandler.END


def get_add_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
            CallbackQueryHandler(add_start, pattern="^cmd_add$"),
        ],
        states={
            SELECT_PACK: [
                CallbackQueryHandler(select_pack_callback, pattern="^select_add:"),
            ],
            WAITING_MEDIA: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_add_media),
                CallbackQueryHandler(finish_add_stickers, pattern="^finish_collection$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", add_start),
            CallbackQueryHandler(add_start, pattern="^action_cancel$"),
            CallbackQueryHandler(add_start, pattern="^cmd_start$"),
        ],
    )
