import uuid
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
from handlers.common import cancel_command
from handlers.start import start_command
from keyboards.main_keyboard import get_cancel_keyboard, get_main_menu_keyboard
from keyboards.pack_keyboard import get_packs_list_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.telegram_service import TelegramService
from services.queue_service import QueueService
from utils.logger import logger

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
        msg = "⚠️ <i>You have no owned sticker packs to rename! Use /newpack first.</i>"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    msg = (
        "✏️ <b>Rename Sticker Pack</b>\n\n"
        "<i>Select the pack you wish to rename:</i>"
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
    context.user_data["target_short_name"] = short_name

    msg = (
        f"✅ <b>Selected Pack:</b> <code>{short_name}</code>\n\n"
        "<i>Please enter the new pack title (1-64 characters):</i>"
    )
    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    return WAITING_NEW_TITLE


async def process_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Executes pack title rename directly via Telegram API and updates DB."""
    new_title = update.message.text.strip()
    if not new_title or len(new_title) > 64:
        await update.message.reply_text(
            "⚠️ <i>Title must be between 1 and 64 characters long. Try again:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_NEW_TITLE

    user = update.effective_user
    short_name = context.user_data.get("target_short_name", "")

    try:
        task_ctx = await QueueService.start_task(user.id, "Rename Sticker Pack")
    except RuntimeError as e:
        await update.message.reply_text(f"⚠️ {str(e)}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    status_msg = await update.message.reply_text("⏳ <i>Updating sticker pack title on Telegram...</i>", parse_mode="HTML")

    try:
        task_ctx.check_cancelled()
        # Direct Telegram Bot API set_sticker_set_title call
        success = await TelegramService.set_sticker_set_title(context.bot, short_name, new_title)

        if not success:
            raise RuntimeError(f"Telegram Bot API rejected title update for '{short_name}'.")

        # Update Local DB record
        async with AsyncSessionLocal() as session:
            await DatabaseService.update_pack_title(session, short_name, new_title)
            await DatabaseService.log_history(
                session=session,
                user_id=user.id,
                operation_type="RENAME",
                details=f"Renamed pack '{short_name}' title to '{new_title}'."
            )

        link = f"https://t.me/addstickers/{short_name}"
        final_text = (
            "🎉 <b>Pack Renamed Successfully!</b>\n\n"
            f"• <b>New Title:</b> <code>{new_title}</code>\n"
            f"• <b>Pack Link:</b> <a href='{link}'>{link}</a>"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=False)

    except Exception as e:
        logger.error(f"Error renaming pack: {e}")
        await status_msg.edit_text(f"❌ <b>Rename Failed:</b> {str(e)}", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    finally:
        await QueueService.finish_task(user.id)

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
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_command, pattern="^action_cancel$"),
            CallbackQueryHandler(start_command, pattern="^cmd_start$"),
        ],
    )
