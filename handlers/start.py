from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards.main_keyboard import get_main_menu_keyboard
from middlewares.user_tracker import track_user


@track_user
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /start command with clean, natural messaging."""
    user = update.effective_user
    name = user.first_name if user else "Friend"

    text = (
        f"👋 <b>Welcome, {name}!</b>\n\n"
        f"✨ <b>Sticker Studio Bot</b>\n"
        f"<i>Create, manage, clone, and export Telegram sticker packs easily.</i> 🚀\n\n"
        f"<b>Features:</b>\n"
        f"• 📦 Batch Sticker Creation (ZIP / Photos)\n"
        f"• 📋 Clone Any Sticker Pack\n"
        f"• 💾 Export Packs (ZIP, PNG, WEBP)\n"
        f"• ✏️ Rename Packs (instant title update)\n"
        f"• 🎥 Video & GIF Sticker Support\n"
        f"• 🗑️ Delete Owned Packs\n\n"
        f"<i>Select an option below to get started:</i>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    return ConversationHandler.END


@track_user
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /help command with clear instructions."""
    text = (
        f"❓ <b>Bot Help & User Guide</b>\n\n"
        f"• <b>/newpack</b> — Create a new sticker pack\n"
        f"• <b>/add</b> — Add stickers to an existing pack\n"
        f"• <b>/clone</b> — Clone any Telegram sticker pack\n"
        f"• <b>/download</b> — Save a sticker pack as ZIP, PNG, or WEBP\n"
        f"• <b>/rename</b> — Update the title of an owned pack\n"
        f"• <b>/delete</b> — Permanently delete an owned pack\n"
        f"• <b>/history</b> — View your sticker packs & recent activity\n"
        f"• <b>/settings</b> — View bot settings & limits\n"
        f"• <b>/cancel</b> — Cancel current operation\n\n"
        f"<b>Upload Tips:</b>\n"
        f"• You can send multiple photos/files at once or upload a single ZIP archive.\n"
        f"• Supported formats: PNG, JPG, WEBP, GIF, WEBM."
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    return ConversationHandler.END
