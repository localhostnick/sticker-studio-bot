from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)

from database import AsyncSessionLocal
from handlers.common import cancel_command
from handlers.start import start_command
from keyboards.main_keyboard import get_main_menu_keyboard
from keyboards.pack_keyboard import get_packs_list_keyboard, get_delete_confirm_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService
from services.telegram_service import TelegramService
from utils.logger import logger

SELECT_PACK, CONFIRM_DELETE = range(2)


@track_user
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /delete command."""
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        user_packs = await DatabaseService.get_user_packs(session, user.id)

    if not user_packs:
        msg = "⚠️ You have no owned sticker packs available for deletion."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    msg = "🗑️ <b>Delete Sticker Pack</b>\n\nSelect the pack you wish to delete permanently:"
    kb = get_packs_list_keyboard(user_packs, action_prefix="select_del")

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

    return SELECT_PACK


async def select_delete_pack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback when user selects a pack to delete."""
    query = update.callback_query
    await query.answer()

    short_name = query.data.split(":")[1]
    context.user_data["target_delete_short_name"] = short_name

    msg = (
        f"⚠️ <b>ARE YOU SURE?</b>\n\n"
        f"You are about to permanently delete sticker pack <code>{short_name}</code>.\n"
        f"<i>This action cannot be undone.</i>"
    )
    kb = get_delete_confirm_keyboard(short_name)
    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=kb)
    return CONFIRM_DELETE


async def process_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Executes deletion after confirmation."""
    query = update.callback_query
    await query.answer()

    short_name = query.data.split(":")[1]
    user = update.effective_user

    await query.edit_message_text("⏳ Deleting sticker pack from Telegram...", parse_mode="HTML")

    # Step 1: Call Telegram API to delete sticker set
    success = await TelegramService.delete_sticker_pack(context.bot, short_name)

    # Step 2: Delete DB record & log audit
    async with AsyncSessionLocal() as session:
        await DatabaseService.delete_pack(session, short_name, user.id)
        await DatabaseService.log_history(
            session=session,
            user_id=user.id,
            operation_type="DELETE",
            details=f"Deleted pack '{short_name}'."
        )

    if success:
        msg = f"🗑️ <b>Sticker pack <code>{short_name}</code> has been deleted permanently.</b>"
    else:
        msg = f"⚠️ Removed local database record for <code>{short_name}</code>. (Telegram pack deletion returned status false)."

    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


def get_delete_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("delete", delete_start),
            CallbackQueryHandler(delete_start, pattern="^cmd_delete$"),
        ],
        states={
            SELECT_PACK: [
                CallbackQueryHandler(select_delete_pack, pattern="^select_del:"),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(process_confirm_delete, pattern="^confirm_delete:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_command, pattern="^action_cancel$"),
            CallbackQueryHandler(start_command, pattern="^cmd_start$"),
        ],
    )
