from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database import AsyncSessionLocal
from keyboards.main_keyboard import get_main_menu_keyboard
from middlewares.user_tracker import track_user
from services.db_service import DatabaseService


@track_user
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /history command and history callback button."""
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        packs = await DatabaseService.get_user_packs(session, user.id)
        history_records = await DatabaseService.get_user_history(session, user.id, limit=10)

    # Format Packs List
    if packs:
        packs_lines = []
        for p in packs:
            link = f"https://t.me/addstickers/{p.short_name}"
            packs_lines.append(f"• <a href='{link}'>{p.title}</a> ({p.sticker_count} stickers)")
        packs_text = "\n".join(packs_lines)
    else:
        packs_text = "<i>No active sticker packs created yet.</i>"

    # Format History Records
    if history_records:
        history_lines = []
        for h in history_records:
            date_str = h.timestamp.strftime("%Y-%m-%d %H:%M")
            history_lines.append(f"[{date_str}] <b>{h.operation_type}</b> — {h.details or 'Done'}")
        history_text = "\n".join(history_lines)
    else:
        history_text = "<i>No operation history found.</i>"

    text = (
        "📜 <b>Your Sticker Packs & Activity Log</b>\n\n"
        f"<b>📦 Owned Sticker Packs ({len(packs)}):</b>\n"
        f"{packs_text}\n\n"
        "<b>🕒 Recent Operations:</b>\n"
        f"{history_text}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(), disable_web_page_preview=True)


def get_history_handler() -> CommandHandler:
    return CommandHandler("history", history_command)
