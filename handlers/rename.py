import shutil
import uuid
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
from keyboards.pack_keyboard import get_packs_list_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.pack_downloader import PackDownloader
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger
from utils.progress import format_progress_message
from utils.short_name import generate_unique_short_name

SELECT_PACK, WAITING_NEW_TITLE = range(2)


@track_user
async def rename_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /rename command."""
    context.user_data.clear()
    context.user_data["session_id"] = uuid.uuid4().hex[:8]
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        user_packs = await DatabaseService.get_user_packs(session, user.id)

    if not user_packs:
        msg = "⚠️ You have no owned sticker packs to rename! Use /newpack first."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    msg = (
        "✏️ <b>Rename Sticker Pack</b>\n\n"
        "<i>Note: Telegram API renames packs by re-creating them with a new name.</i>\n\n"
        "Select the pack you wish to rename:"
    )
    kb = get_packs_list_keyboard(user_packs, action_prefix="select_rename")

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

    return SELECT_PACK


async def select_rename_pack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback when user selects a pack to rename."""
    query = update.callback_query
    await query.answer()

    short_name = query.data.split(":")[1]
    context.user_data["old_short_name"] = short_name

    msg = f"Selected Pack: <code>{short_name}</code>\n\nPlease enter the <b>New Pack Title</b>:"
    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    return WAITING_NEW_TITLE


async def process_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Executes pack rename via clone + delete routine."""
    new_title = update.message.text.strip()
    if not new_title or len(new_title) > 64:
        await update.message.reply_text("⚠️ Title must be 1-64 characters. Try again:", reply_markup=get_cancel_keyboard())
        return WAITING_NEW_TITLE

    user = update.effective_user
    old_short_name = context.user_data.get("old_short_name", "")
    bot_user = await context.bot.get_me()
    new_short_name = generate_unique_short_name(new_title, bot_user.username)

    try:
        task_ctx = await QueueService.start_task(user.id, "Rename Sticker Pack")
    except RuntimeError as e:
        await update.message.reply_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await update.message.reply_text("⏳ Processing pack rename request...", parse_mode="HTML")
    temp_dir = settings.TEMP_DIRECTORY / f"user_{user.id}_rename_{context.user_data['session_id']}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Download existing stickers
        stk_set = await TelegramService.get_sticker_set(context.bot, old_short_name)
        if not stk_set:
            raise ValueError(f"Could not access sticker pack '{old_short_name}'.")

        total = len(stk_set.stickers)
        first_stk = stk_set.stickers[0] if stk_set.stickers else None
        is_video = bool(first_stk and (getattr(first_stk, "is_video", False) or getattr(first_stk, "is_animated", False)))
        fmt = "WEBP" if not is_video else "PNG"

        await status_msg.edit_text(format_progress_message("Downloading Existing Stickers...", 0, total), parse_mode="HTML")

        async def dl_prog(c, t):
            task_ctx.check_cancelled()
            await status_msg.edit_text(format_progress_message("Downloading Existing Stickers...", c, t), parse_mode="HTML")

        downloaded_paths, _ = await PackDownloader.download_pack_as_files(
            bot=context.bot,
            pack_name_or_link=old_short_name,
            dest_dir=temp_dir,
            export_format=fmt,
            progress_callback=dl_prog
        )

        # Step 2: Create new pack with new title
        await status_msg.edit_text(format_progress_message("Creating Renamed Pack...", 0, total), parse_mode="HTML")

        async def up_prog(c, t):
            task_ctx.check_cancelled()
            await status_msg.edit_text(format_progress_message("Creating Renamed Pack...", c, t), parse_mode="HTML")

        stk_fmt = "video" if is_video else "static"
        created_packs = await TelegramService.create_sticker_pack(
            bot=context.bot,
            user_id=user.id,
            title=new_title,
            short_name=new_short_name,
            sticker_file_paths=downloaded_paths,
            sticker_format=stk_fmt,
            progress_callback=up_prog
        )

        # Step 3: Delete old pack from Telegram & DB
        await TelegramService.delete_sticker_pack(context.bot, old_short_name)
        async with AsyncSessionLocal() as session:
            await DatabaseService.delete_pack(session, old_short_name, user.id)
            for p in created_packs:
                await DatabaseService.create_sticker_pack(
                    session=session,
                    title=p["title"],
                    short_name=p["short_name"],
                    owner_id=user.id,
                    sticker_count=p["count"],
                    sticker_format=stk_fmt
                )
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="RENAME",
                details=f"Renamed pack '{old_short_name}' to '{new_title}'."
            )

        new_link = created_packs[0]["link"]
        final_text = (
            f"🎉 <b>Pack Renamed Successfully!</b>\n\n"
            f"• <b>New Title:</b> {new_title}\n"
            f"• <b>New Link:</b> <a href='{new_link}'>{new_link}</a>"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=False)

    except Exception as e:
        logger.error(f"Error renaming pack: {e}")
        await status_msg.edit_text(f"❌ <b>Rename Failed:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return ConversationHandler.END


def get_rename_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("rename", rename_start),
            CallbackQueryHandler(rename_start, pattern="^cmd_rename$"),
        ],
        states={
            SELECT_PACK: [
                CallbackQueryHandler(select_rename_pack, pattern="^select_rename:"),
            ],
            WAITING_NEW_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_rename),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", rename_start),
            CallbackQueryHandler(rename_start, pattern="^action_cancel$"),
            CallbackQueryHandler(rename_start, pattern="^cmd_start$"),
        ],
    )
