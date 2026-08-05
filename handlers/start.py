from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards.main_keyboard import get_main_menu_keyboard
from middlewares.user_tracker import track_user
from utils.typography import small_caps


@track_user
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /start command with Small Caps styling."""
    user = update.effective_user
    name = user.first_name if user else "Friend"

    text = (
        f"👋 <b>{small_caps('Welcome')}, {name}!</b>\n\n"
        f"✨ <b>{small_caps('Sticker Studio Bot')}</b>\n"
        f"<i>{small_caps('High-Speed Telegram Sticker Pack Manager')}</i> 🚀\n\n"
        f"<b>{small_caps('Features')}:</b>\n"
        f"📦 {small_caps('Batch Sticker Creation (ZIP / Photos)')}\n"
        f"📋 {small_caps('Clone Any Sticker Pack')}\n"
        f"💾 {small_caps('Export Packs (ZIP, PNG, WEBP)')}\n"
        f"✏️ {small_caps('Rename & Re-order Packs')}\n"
        f"🎥 {small_caps('Animated GIF & WEBM Support')}\n"
        f"🗑️ {small_caps('Delete Owned Packs')}\n\n"
        f"<i>{small_caps('Select an option below to begin')}:</i>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    return ConversationHandler.END


@track_user
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /help command with Small Caps styling."""
    text = (
        f"❓ <b>{small_caps('Bot Help & User Guide')}</b>\n\n"
        f"• <b>/newpack</b> — {small_caps('Create a brand new sticker pack')}\n"
        f"• <b>/add</b> — {small_caps('Append stickers to your existing pack')}\n"
        f"• <b>/clone</b> — {small_caps('Re-create any Telegram sticker pack')}\n"
        f"• <b>/download</b> — {small_caps('Save sticker pack as ZIP/PNG/WEBP')}\n"
        f"• <b>/rename</b> — {small_caps('Duplicate & rename a pack')}\n"
        f"• <b>/delete</b> — {small_caps('Permanently delete an owned pack')}\n"
        f"• <b>/history</b> — {small_caps('View recent activity & owned packs')}\n"
        f"• <b>/settings</b> — {small_caps('System configuration options')}\n"
        f"• <b>/cancel</b> — {small_caps('Cancel current operation')}\n\n"
        f"<b>{small_caps('Upload Tips')}:</b>\n"
        f"• {small_caps('Send a ZIP file with images or send multiple photos/documents at once.')}\n"
        f"• {small_caps('Supported formats: PNG, JPG, WEBP, GIF, WEBM.')}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    return ConversationHandler.END
