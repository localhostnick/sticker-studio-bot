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

from config import settings
from database import AsyncSessionLocal
from keyboards.main_keyboard import get_cancel_keyboard, get_main_menu_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.pack_downloader import PackDownloader
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger
from utils.progress import format_progress_message
from utils.short_name import generate_unique_short_name
from utils.typography import small_caps

WAITING_LINK, WAITING_NEW_TITLE = range(2)


@track_user
async def clone_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /clone command."""
    context.user_data.clear()
    context.user_data["session_id"] = uuid.uuid4().hex[:8]

    msg = (
        f"📋 <b>{small_caps('Clone Sticker Pack')}</b>\n\n"
        f"<i>{small_caps('Please send the link or short name of the sticker pack to clone')}:</i>\n"
        f"e.g. <code>https://t.me/addstickers/packname</code>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())

    return WAITING_LINK


async def receive_clone_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives target sticker pack link."""
    text = update.message.text.strip()
    short_name = text.split("/")[-1].strip()

    status_msg = await update.message.reply_text(f"🔍 <i>{small_caps('Fetching sticker pack details')}...</i>", reply_markup=get_cancel_keyboard())
    sticker_set = await TelegramService.get_sticker_set(context.bot, short_name)

    if not sticker_set:
        await status_msg.edit_text(
            f"❌ <i>{small_caps('Could not find sticker pack')} <code>{short_name}</code>. {small_caps('Please check the link and try again')}:</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_LINK

    first_stk = sticker_set.stickers[0] if sticker_set.stickers else None
    is_vid = getattr(first_stk, "is_video", False) if first_stk else False
    is_anim = getattr(first_stk, "is_animated", False) if first_stk else False

    context.user_data["source_pack_short_name"] = short_name
    context.user_data["source_title"] = sticker_set.title
    context.user_data["sticker_count"] = len(sticker_set.stickers)
    context.user_data["is_video"] = is_vid or is_anim

    msg = (
        f"✅ <b>{small_caps('Found Pack')}:</b> <b>{sticker_set.title}</b> ({len(sticker_set.stickers)} {small_caps('stickers')})\n\n"
        f"<i>{small_caps('Please enter a New Title for your cloned pack')}:</i>"
    )
    await status_msg.edit_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    return WAITING_NEW_TITLE


async def process_clone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Downloads stickers from source pack and creates cloned pack."""
    new_title = update.message.text.strip()
    if not new_title or len(new_title) > 64:
        await update.message.reply_text(f"⚠️ <i>{small_caps('Title must be 1 to 64 characters. Try again')}:</i>", reply_markup=get_cancel_keyboard())
        return WAITING_NEW_TITLE

    user = update.effective_user
    source_short_name = context.user_data.get("source_pack_short_name", "")
    is_video = context.user_data.get("is_video", False)
    bot_user = await context.bot.get_me()
    new_short_name = generate_unique_short_name(new_title, bot_user.username)

    try:
        task_ctx = await QueueService.start_task(user.id, "Clone Sticker Pack")
    except RuntimeError as e:
        await update.message.reply_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await update.message.reply_text(
        format_progress_message("Downloading Source Stickers", 0, context.user_data.get("sticker_count", 0)),
        parse_mode="HTML"
    )

    temp_dir = settings.TEMP_DIRECTORY / f"user_{user.id}_clone_{context.user_data['session_id']}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        async def dl_progress(current: int, total: int):
            task_ctx.check_cancelled()
            await status_msg.edit_text(
                format_progress_message("Downloading Source Stickers", current, total),
                parse_mode="HTML"
            )

        fmt = "WEBP" if not is_video else "PNG"
        downloaded_paths, _ = await PackDownloader.download_pack_as_files(
            bot=context.bot,
            pack_name_or_link=source_short_name,
            dest_dir=temp_dir,
            export_format=fmt,
            progress_callback=dl_progress
        )

        total = len(downloaded_paths)

        await status_msg.edit_text(
            format_progress_message("Uploading Cloned Pack", 0, total),
            parse_mode="HTML"
        )

        async def upload_progress(current: int, tot: int):
            task_ctx.check_cancelled()
            await status_msg.edit_text(
                format_progress_message("Uploading Cloned Pack", current, tot),
                parse_mode="HTML"
            )

        stk_format = "video" if is_video else "static"
        created_packs = await TelegramService.create_sticker_pack(
            bot=context.bot,
            user_id=user.id,
            title=new_title,
            short_name=new_short_name,
            sticker_file_paths=downloaded_paths,
            sticker_format=stk_format,
            progress_callback=upload_progress
        )

        async with AsyncSessionLocal() as session:
            for p in created_packs:
                await DatabaseService.create_sticker_pack(
                    session=session,
                    title=p["title"],
                    short_name=p["short_name"],
                    owner_id=user.id,
                    sticker_count=p["count"],
                    sticker_format=stk_format
                )
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="CLONE",
                details=f"Cloned '{source_short_name}' to '{new_title}' ({total} stickers)."
            )

        links_text = "\n".join([f"• <a href='{p['link']}'>{p['title']}</a> ({p['count']} {small_caps('stickers')})" for p in created_packs])
        final_text = (
            f"🎉 <b>{small_caps('Pack Cloned Successfully')}!</b>\n\n"
            f"<b>{small_caps('Cloned Pack(s)')}:</b>\n{links_text}\n\n"
            f"✨ <i>{small_caps('Total Stickers Cloned')}: {total}</i>"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=False)

    except Exception as e:
        logger.error(f"Error during pack cloning: {e}")
        await status_msg.edit_text(f"❌ <b>{small_caps('Clone Failed')}:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return ConversationHandler.END


def get_clone_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("clone", clone_start),
            CallbackQueryHandler(clone_start, pattern="^cmd_clone$"),
        ],
        states={
            WAITING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_clone_link),
            ],
            WAITING_NEW_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_clone),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", clone_start),
            CallbackQueryHandler(clone_start, pattern="^action_cancel$"),
            CallbackQueryHandler(clone_start, pattern="^cmd_start$"),
        ],
    )
