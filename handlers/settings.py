from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from keyboards.main_keyboard import get_main_menu_keyboard
from middlewares.user_tracker import track_user


@track_user
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /settings command."""
    db_type = settings.DATABASE_URL.split(":")[0]

    text = (
        "⚙️ <b>Bot System Configuration</b>\n\n"
        f"• <b>Max Upload Batch:</b> {settings.MAX_IMAGES} items\n"
        f"• <b>Max Upload Size:</b> {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB\n"
        f"• <b>Database Backend:</b> {db_type.upper()}\n"
        f"• <b>Logging Level:</b> {settings.LOG_LEVEL}\n"
        f"• <b>Temp Directory:</b> <code>{settings.TEMP_DIRECTORY}</code>\n\n"
        "<i>Configuration parameters can be tuned in your .env file.</i>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


def get_settings_handler() -> CommandHandler:
    return CommandHandler("settings", settings_command)
