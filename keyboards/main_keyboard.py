from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.typography import small_caps


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the main interactive menu inline keyboard with Small Caps styling."""
    keyboard = [
        [
            InlineKeyboardButton(f"➕ {small_caps('New Pack')}", callback_data="cmd_newpack"),
            InlineKeyboardButton(f"📥 {small_caps('Add Stickers')}", callback_data="cmd_add"),
        ],
        [
            InlineKeyboardButton(f"📋 {small_caps('Clone Pack')}", callback_data="cmd_clone"),
            InlineKeyboardButton(f"💾 {small_caps('Download Pack')}", callback_data="cmd_download"),
        ],
        [
            InlineKeyboardButton(f"✏️ {small_caps('Rename Pack')}", callback_data="cmd_rename"),
            InlineKeyboardButton(f"🗑️ {small_caps('Delete Pack')}", callback_data="cmd_delete"),
        ],
        [
            InlineKeyboardButton(f"📜 {small_caps('History & Packs')}", callback_data="cmd_history"),
            InlineKeyboardButton(f"⚙️ {small_caps('Settings')}", callback_data="cmd_settings"),
        ],
        [
            InlineKeyboardButton(f"❓ {small_caps('Help Guide')}", callback_data="cmd_help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Returns a standalone Cancel Action inline button in Small Caps."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚫 {small_caps('Cancel Operation')}", callback_data="action_cancel")]
    ])
