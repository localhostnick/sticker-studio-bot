from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the main interactive menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ New Pack", callback_data="cmd_newpack"),
            InlineKeyboardButton("📥 Add Stickers", callback_data="cmd_add"),
        ],
        [
            InlineKeyboardButton("📋 Clone Pack", callback_data="cmd_clone"),
            InlineKeyboardButton("💾 Download Pack", callback_data="cmd_download"),
        ],
        [
            InlineKeyboardButton("✏️ Rename Pack", callback_data="cmd_rename"),
            InlineKeyboardButton("🗑️ Delete Pack", callback_data="cmd_delete"),
        ],
        [
            InlineKeyboardButton("📜 History & Packs", callback_data="cmd_history"),
            InlineKeyboardButton("⚙️ Settings", callback_data="cmd_settings"),
        ],
        [
            InlineKeyboardButton("❓ Help Guide", callback_data="cmd_help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Returns a standalone Cancel action inline button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Cancel Operation", callback_data="action_cancel")]
    ])
