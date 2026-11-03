import asyncio
import shutil
import uuid
from pathlib import Path
from typing import List
from telegram import Update, InputFile
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import settings
from database import AsyncSessionLocal
from handlers.common import cancel_command
from handlers.start import start_command
from keyboards.main_keyboard import get_cancel_keyboard, get_main_menu_keyboard
from keyboards.pack_keyboard import get_download_format_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.pack_downloader import PackDownloader
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger
from utils.progress import format_progress_message
from utils.rate_limiter import retry_telegram_api

WAITING_LINK, SELECT_FORMAT = range(2)


@track_user
async def download_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /download command."""
    context.user_data.clear()
    context.user_data["session_id"] = uuid.uuid4().hex[:8]

    msg = (
        "💾 <b>Download Sticker Pack</b>\n\n"
        "<i>Please send the link or short name of the sticker pack to download:</i>\n"
        "e.g. <code>https://t.me/addstickers/animals</code>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())

    return WAITING_LINK


async def receive_download_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates pack link and shows format selection options."""
    text = update.message.text.strip()
    short_name = text.split("/")[-1].strip()

    status_msg = await update.message.reply_text(
        "🔍 <i>Checking sticker pack availability...</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    stk_set = await TelegramService.get_sticker_set(context.bot, short_name)

    if not stk_set:
        await status_msg.edit_text(
            f"❌ <i>Sticker pack <code>{short_name}</code> not found. Please verify the URL.</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_LINK

    context.user_data["download_short_name"] = short_name
    context.user_data["pack_title"] = stk_set.title
    context.user_data["sticker_count"] = len(stk_set.stickers)

    msg = (
        f"📦 <b>Pack Found:</b> <b>{stk_set.title}</b>\n"
        f"🔢 <b>Total Stickers:</b> {len(stk_set.stickers)}\n\n"
        "<i>Choose an export format below:</i>"
    )
    await status_msg.edit_text(msg, parse_mode="HTML", reply_markup=get_download_format_keyboard(short_name))
    return SELECT_FORMAT


async def process_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes download format callback query."""
    query = update.callback_query
    await query.answer()

    data = query.data
    fmt_type, short_name = data.split(":")[0].replace("dl_", "").upper(), data.split(":")[1]
    user = update.effective_user
    title = context.user_data.get("pack_title", short_name)
    total_count = context.user_data.get("sticker_count", 0)

    try:
        task_ctx = await QueueService.start_task(user.id, "Download Sticker Pack")
    except RuntimeError as e:
        await query.edit_message_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await query.edit_message_text(
        format_progress_message(f"Downloading Stickers ({fmt_type})", 0, total_count),
        parse_mode="HTML"
    )

    temp_dir = settings.TEMP_DIRECTORY / f"user_{user.id}_dl_{context.user_data.get('session_id', 'temp')}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        async def dl_progress(current: int, total: int):
            task_ctx.check_cancelled()
            await status_msg.edit_text(
                format_progress_message(f"Downloading Stickers ({fmt_type})", current, total),
                parse_mode="HTML"
            )

        export_fmt = "PNG" if fmt_type == "PNG" else "WEBP"
        files, _, _, _ = await PackDownloader.download_pack_as_files(
            bot=context.bot,
            pack_name_or_link=short_name,
            dest_dir=temp_dir,
            export_format=export_fmt,
            progress_callback=dl_progress
        )

        if fmt_type == "ZIP":
            await status_msg.edit_text("📦 <i>Packaging files into ZIP archive...</i>", parse_mode="HTML")
            zip_path = temp_dir / f"{short_name}.zip"
            await PackDownloader.create_zip_archive(files, zip_path)

            await status_msg.edit_text("📤 <i>Sending ZIP archive to Telegram...</i>", parse_mode="HTML")
            with open(zip_path, "rb") as f:
                await retry_telegram_api(
                    context.bot.send_document,
                    chat_id=user.id,
                    document=InputFile(f, filename=f"{short_name}.zip"),
                    caption=f"📦 <b>Sticker Pack ZIP Archive</b>\n\n• <b>Title:</b> {title}\n• <b>Count:</b> {len(files)} stickers",
                    parse_mode="HTML"
                )
        else:
            await status_msg.edit_text(f"📤 <i>Sending {len(files)} {fmt_type} files...</i>", parse_mode="HTML")
            for idx, file_path in enumerate(files, start=1):
                task_ctx.check_cancelled()
                with open(file_path, "rb") as f:
                    await retry_telegram_api(
                        context.bot.send_document,
                        chat_id=user.id,
                        document=InputFile(f, filename=file_path.name),
                    )
                if idx % 5 == 0:
                    await asyncio.sleep(0.5)

        async with AsyncSessionLocal() as session:
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="DOWNLOAD",
                details=f"Downloaded pack '{short_name}' as {fmt_type} ({len(files)} items)."
            )

        await status_msg.edit_text(
            f"✅ <b>Download Complete!</b>\n\n<i>Exported {len(files)} stickers as <b>{fmt_type}</b>.</i>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Error during pack download: {e}")
        await status_msg.edit_text(f"❌ <b>Download Failed:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return ConversationHandler.END


def get_download_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("download", download_start),
            CallbackQueryHandler(download_start, pattern="^cmd_download$"),
        ],
        states={
            WAITING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_download_link),
            ],
            SELECT_FORMAT: [
                CallbackQueryHandler(process_download_callback, pattern="^dl_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_command, pattern="^action_cancel$"),
            CallbackQueryHandler(start_command, pattern="^cmd_start$"),
        ],
    )
