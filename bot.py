import asyncio
import sys
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from telegram.request import HTTPXRequest

from config import settings
from database import init_db
from handlers.start import start_command, help_command
from handlers.newpack import get_newpack_handler
from handlers.add import get_add_handler
from handlers.clone import get_clone_handler
from handlers.download import get_download_handler
from handlers.rename import get_rename_handler
from handlers.delete import get_delete_handler
from handlers.history import history_command
from handlers.settings import settings_command
from handlers.common import cancel_command, error_handler
from utils.logger import logger


async def post_init(application) -> None:
    """Run post-initialization tasks like database init and bot profile check."""
    logger.info("Initializing database tables...")
    await init_db()
    
    bot_info = await application.bot.get_me()
    settings.BOT_USERNAME = bot_info.username
    logger.info(f"Bot connected successfully as @{bot_info.username} ({bot_info.first_name})")


def main() -> None:
    """Main entrypoint to configure and start the Telegram bot."""
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("BOT_TOKEN is missing or not set in .env configuration file! Exiting.")
        sys.exit(1)

    logger.info("Starting Telegram Sticker Pack Manager Bot...")

    # Configure custom HTTP request settings with longer timeouts
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    # Build Application
    app = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .request(request)
        .post_init(post_init)
        .concurrent_updates(True)
        .build()
    )

    # Register Conversation Handlers
    app.add_handler(get_newpack_handler())
    app.add_handler(get_add_handler())
    app.add_handler(get_clone_handler())
    app.add_handler(get_download_handler())
    app.add_handler(get_rename_handler())
    app.add_handler(get_delete_handler())

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Register Callback Query Handlers for Menu Navigation
    app.add_handler(CallbackQueryHandler(start_command, pattern="^cmd_start$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^cmd_help$"))
    app.add_handler(CallbackQueryHandler(history_command, pattern="^cmd_history$"))
    app.add_handler(CallbackQueryHandler(settings_command, pattern="^cmd_settings$"))
    app.add_handler(CallbackQueryHandler(cancel_command, pattern="^action_cancel$"))

    # Register Global Error Handler
    app.add_error_handler(error_handler)

    logger.info("Bot setup completed. Starting long-polling loop...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
