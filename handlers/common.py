import traceback
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards.main_keyboard import get_main_menu_keyboard
from services.queue_service import QueueService
from utils.logger import logger


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels any ongoing conversation or active task."""
    user = update.effective_user
    user_id = user.id if user else 0

    # Cancel active background processing queue task if present
    cancelled = await QueueService.cancel_user_task(user_id)
    
    # Clear user context state
    context.user_data.clear()

    msg = "🚫 <b>Operation cancelled.</b>"
    if cancelled:
        msg += "\n\n<i>Active processing task has been signaled to stop.</i>"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    elif update.message:
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global unhandled exception handler."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    tb_string = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    logger.error(f"Traceback:\n{tb_string}")

    if isinstance(update, Update):
        error_msg = "⚠️ <b>An error occurred while processing your request.</b>\n\nPlease try again or send /cancel."
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg, parse_mode="HTML")
            elif update.message:
                await update.message.reply_text(error_msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send error notification to user: {e}")
