from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from models.sticker_pack import StickerPack


def get_download_format_keyboard(short_name: str) -> InlineKeyboardMarkup:
    """Download format options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📦 ZIP Archive", callback_data=f"dl_zip:{short_name}"),
            InlineKeyboardButton("🖼️ PNG Files", callback_data=f"dl_png:{short_name}"),
            InlineKeyboardButton("🎨 WEBP Files", callback_data=f"dl_webp:{short_name}"),
        ],
        [
            InlineKeyboardButton("🔙 Main Menu", callback_data="cmd_start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_packs_list_keyboard(packs: List[StickerPack], action_prefix: str) -> InlineKeyboardMarkup:
    """Generates inline buttons for selecting one of the user's owned packs."""
    keyboard = []
    for pack in packs:
        label = f"📦 {pack.title} ({pack.sticker_count} stickers)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"{action_prefix}:{pack.short_name}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="cmd_start")])
    return InlineKeyboardMarkup(keyboard)


def get_delete_confirm_keyboard(short_name: str) -> InlineKeyboardMarkup:
    """Confirmation prompt keyboard for pack deletion."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete Forever", callback_data=f"confirm_delete:{short_name}"),
            InlineKeyboardButton("❌ No, Keep Pack", callback_data="cmd_start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_done_collecting_keyboard(count: int) -> InlineKeyboardMarkup:
    """Keyboard shown during batch media collection."""
    keyboard = [
        [InlineKeyboardButton(f"🚀 Create Pack ({count} items)", callback_data="finish_collection")],
        [InlineKeyboardButton("🚫 Cancel", callback_data="action_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)
