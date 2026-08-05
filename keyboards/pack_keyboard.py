from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from models.sticker_pack import StickerPack
from utils.typography import small_caps


def get_download_format_keyboard(short_name: str) -> InlineKeyboardMarkup:
    """Download format options keyboard in Small Caps styling."""
    keyboard = [
        [
            InlineKeyboardButton(f"📦 {small_caps('ZIP Archive')}", callback_data=f"dl_zip:{short_name}"),
            InlineKeyboardButton(f"🖼️ {small_caps('PNG Files')}", callback_data=f"dl_png:{short_name}"),
            InlineKeyboardButton(f"🎨 {small_caps('WEBP Files')}", callback_data=f"dl_webp:{short_name}"),
        ],
        [
            InlineKeyboardButton(f"🔙 {small_caps('Main Menu')}", callback_data="cmd_start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_packs_list_keyboard(packs: List[StickerPack], action_prefix: str) -> InlineKeyboardMarkup:
    """Generates inline buttons for selecting one of user's owned packs with Small Caps styling."""
    keyboard = []
    for pack in packs:
        label = f"📦 {pack.title} ({pack.sticker_count} {small_caps('stickers')})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"{action_prefix}:{pack.short_name}")])
    
    keyboard.append([InlineKeyboardButton(f"🔙 {small_caps('Main Menu')}", callback_data="cmd_start")])
    return InlineKeyboardMarkup(keyboard)


def get_delete_confirm_keyboard(short_name: str) -> InlineKeyboardMarkup:
    """Confirmation prompt keyboard for pack deletion with Small Caps font."""
    keyboard = [
        [
            InlineKeyboardButton(f"✅ {small_caps('Yes, Delete Forever')}", callback_data=f"confirm_delete:{short_name}"),
            InlineKeyboardButton(f"❌ {small_caps('No, Keep Pack')}", callback_data="cmd_start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_done_collecting_keyboard(count: int) -> InlineKeyboardMarkup:
    """Keyboard shown during batch media collection in Small Caps."""
    keyboard = [
        [InlineKeyboardButton(f"🚀 {small_caps('Create Pack')} ({count} {small_caps('items')})", callback_data="finish_collection")],
        [InlineKeyboardButton(f"🚫 {small_caps('Cancel')}", callback_data="action_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)
