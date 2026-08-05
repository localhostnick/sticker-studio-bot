import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN"
    BOT_USERNAME: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///sticker_bot.db"
    
    TEMP_DIRECTORY: Path = Path("./temp")
    STORAGE_DIRECTORY: Path = Path("./storage")
    LOGS_DIRECTORY: Path = Path("./logs")
    
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_IMAGES: int = 120                     # Telegram sticker pack max limit per pack
    MAX_VIDEO_STICKERS: int = 50              # Telegram limit for video stickers
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        self.TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)
        self.STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIRECTORY.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
