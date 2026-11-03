<div align="center">

# Sticker Studio Bot
### Telegram Sticker Pack Manager Bot

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/python--telegram--bot-v22%2B-2CA5E0.svg)](https://python-telegram-bot.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/tests-5%20passed-brightgreen.svg)](tests)

[**Key Features**](#-key-features) • [**Architecture**](#-architecture--design) • [**Installation**](#-quick-start--installation) • [**Changelog & Fixes**](#-changelog--updates-history)

---
</div>

## Overview

**Sticker Studio Bot** is an asynchronous Telegram Sticker Pack Manager bot built with **Python 3.11+**, **python-telegram-bot (v22+)**, **SQLAlchemy Async ORM**, **Pillow**, and **FFmpeg**.

It helps users create, clone, manage, rename, and export Telegram sticker packs with support for batch image processing, ZIP archive extraction, and animated GIF/video stickers.

---

## Key Features

- **Batch ZIP Upload**: Upload a single `.zip` archive containing multiple images. The bot automatically extracts, validates, resizes, and converts images into stickers.
- **Multiple Media Uploads**: Send multiple photos or document files in a batch message. The bot buffers and processes them in order.
- **Pack Cloning**: Send any public Telegram sticker pack link (`t.me/addstickers/...`) to re-create the pack under your bot's ownership with original emojis preserved.
- **Sticker Pack Export**: Download any Telegram sticker pack as a **ZIP Archive**, **PNG**, or **WEBP** file.
- **Video & GIF Stickers**: Automatic VP9 encoding pipeline for animated GIFs and WEBM files matching Telegram video sticker specifications (512x512, 30fps, ≤3s, ≤256KB).
- **Auto-Splitting**: Automatically partitions packs exceeding Telegram limits (>120 static or >50 video stickers) into clean multi-part sets (Part 1, Part 2, etc.).
- **Native Title Renaming**: Updates sticker pack titles directly via Telegram Bot API without re-uploading files or breaking links.
- **Database Tracking**: Asynchronous SQLite (or PostgreSQL) storage tracking user accounts, created sticker packs, and audit logs.

---

## Project Structure

```
sticker-studio-bot/
├── .github/workflows/ci.yml # GitHub Actions CI pipeline
├── .gitignore               # Git ignore rules
├── .env.example             # Environment configuration template
├── Dockerfile               # Production Docker container definition
├── docker-compose.yml       # Docker Compose deployment setup
├── LICENSE                  # MIT License
├── README.md                # Project documentation & changelog
├── CONTRIBUTING.md          # Open-source contribution guidelines
├── SECURITY.md              # Security vulnerability policy
├── requirements.txt         # Core dependencies
├── bot.py                   # Application entry point & lifecycle manager
├── config.py                # Pydantic settings manager
├── database.py              # Async SQLAlchemy engine & session factory
├── pytest.ini               # Pytest configuration
├── run_bot.bat              # Windows quick launcher
│
├── models/                  # SQLAlchemy ORM Models
│   ├── base.py              # DeclarativeBase
│   ├── user.py              # User entity model
│   ├── sticker_pack.py      # StickerPack tracking model
│   └── history.py           # Operation audit log model
│
├── services/                # Business Logic Services
│   ├── db_service.py        # Async CRUD service
│   ├── image_service.py     # Pillow sticker engine (512x512, transparent padding, WEBP)
│   ├── animated_service.py  # FFmpeg GIF/WEBM VP9 encoder
│   ├── zip_service.py       # Safe async ZIP extractor (Zip-Slip protection)
│   ├── telegram_service.py  # PTB sticker set API wrapper & multi-pack splitter
│   ├── pack_downloader.py   # Downloader & ZIP exporter
│   └── queue_service.py     # Task queue manager with cancellation hooks
│
├── keyboards/               # Dynamic Inline Keyboards
│   ├── main_keyboard.py     # Main menu navigation keyboard
│   └── pack_keyboard.py     # Pack management & confirmation dialogs
│
├── handlers/                # Telegram Workflows & Commands
│   ├── start.py             # /start & /help handlers
│   ├── newpack.py           # /newpack creation workflow
│   ├── add.py               # /add sticker workflow
│   ├── clone.py             # /clone sticker pack workflow
│   ├── download.py          # /download pack workflow
│   ├── rename.py            # /rename pack workflow
│   ├── delete.py            # /delete pack workflow
│   ├── history.py           # /history & pack list workflow
│   ├── settings.py          # /settings system details
│   ├── common.py            # /cancel & error fallback
│   └── media_collector.py   # Batch media collector
│
├── middlewares/             # Request Middlewares
│   └── user_tracker.py      # Database user auto-registration
│
├── utils/                   # Shared Utilities
│   ├── logger.py            # Structured logging setup
│   ├── progress.py          # Visual progress bar generator
│   ├── short_name.py        # Sticker short_name generator & validator
│   └── rate_limiter.py      # Exponential backoff retry handler
│
└── tests/                   # Pytest Test Suite
    ├── test_db_service.py   # Database CRUD unit tests
    ├── test_image_service.py# Image conversion tests
    ├── test_zip_service.py  # ZIP extraction & security tests
    └── test_short_name.py   # Short name generator & sanitizer tests
```

---

## 🛠️ Quick Start & Installation

### Prerequisites
- **Python**: `3.11` or higher
- **FFmpeg**: Installed and available in your system PATH (required for video/GIF stickers)

### Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/localhostnick/sticker-studio-bot.git
   cd sticker-studio-bot
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather):
   ```env
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
   DATABASE_URL=sqlite+aiosqlite:///sticker_bot.db
   LOG_LEVEL=INFO
   ```

5. **Start the Bot**:
   ```bash
   python bot.py
   # Or on Windows double-click run_bot.bat
   ```

---

## 🐳 Docker Deployment

To deploy using Docker Compose:

```bash
# Build and launch container in background
docker-compose up -d --build

# View logs
docker-compose logs -f
```

---

## ⚙️ Environment Configuration Parameters

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | `str` | *Required* | Telegram Bot API Token from @BotFather |
| `DATABASE_URL` | `str` | `sqlite+aiosqlite:///sticker_bot.db` | Async database URI (SQLite / PostgreSQL) |
| `TEMP_DIRECTORY` | `str` | `./temp` | Temporary directory for media processing |
| `STORAGE_DIRECTORY` | `str` | `./storage` | Permanent storage directory |
| `LOGS_DIRECTORY` | `str` | `./logs` | Application log output directory |
| `LOG_LEVEL` | `str` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MAX_UPLOAD_SIZE` | `int` | `52428800` (50MB) | Maximum file size limit for ZIP/media uploads |
| `MAX_IMAGES` | `int` | `120` | Max stickers per static pack (Telegram API limit) |
| `MAX_VIDEO_STICKERS` | `int` | `50` | Max stickers per video pack (Telegram API limit) |

---

## 🧪 Testing

Run the automated pytest suite:

```bash
pytest
```

All 5 test suites run with `pytest-asyncio` and SQLite in-memory database:
- `test_db_service.py`: User registration, pack creation, rename, and deletion
- `test_image_service.py`: 512x512 resizing, aspect ratio preservation, transparent padding
- `test_short_name.py`: Telegram short name validation, sanitization, and uniqueness
- `test_zip_service.py`: ZIP archive extraction, extension filtering, and path traversal protection

---

## 📋 Changelog & Updates History

### Update v2.1 — Clean Formatting & Natural Messaging
- **Removed Fake Small Caps Typography**: Removed `utils/typography.py` and eliminated artificial unicode small-caps font conversions across all handlers, messages, keyboards, and progress bars. All user-facing text is now clean, readable, natural human conversational text.
- **Removed Extraneous GUI Files**: Removed experimental desktop GUI scripts and web assets to keep the bot codebase focused, clean, and lightweight.
- **Cleaned Documentation**: Removed outdated demo links and non-functional bot handles from the README.

### Update v2.0 — Core Bugfixes & API Stability
- **Fixed Infinite Conversation Fallback Loop**: Fixed critical bug in `handlers/newpack.py`, `handlers/add.py`, `handlers/clone.py`, `handlers/download.py`, `handlers/rename.py`, and `handlers/delete.py` where `/cancel` and the cancel button were mapped to the conversation entrypoint (`<handler>_start`) instead of `cancel_command`. Users can now cancel any ongoing operation at any step.
- **Native Pack Renaming (`set_sticker_set_title`)**: Replaced the previous destructive routine (which downloaded all stickers, created a new pack with a new short name, and deleted the old pack) with Telegram Bot API's native `bot.set_sticker_set_title()`. Pack links now remain permanent and existing users do not lose access.
- **Emoji Preservation on Pack Cloning**: In `services/pack_downloader.py` and `handlers/clone.py`, fixed an issue where all stickers were assigned a default `😀` emoji upon cloning. The bot now extracts and retains each sticker's original emoji mapping from Telegram.
- **Animated vs Video Sticker Format Handling**: Added proper classification between animated (`.tgs` Lottie) and video (`.webm` VP9) stickers. Previously, animated stickers were incorrectly sent as video format, causing Telegram API rejection.
- **ZIP Extraction Overwrite Collision Fix**: In `services/zip_service.py`, fixed a bug where files with identical names inside different subfolders inside a ZIP file would overwrite each other. Added collision detection so every extracted file is preserved.
- **Telegram Flood Control Protection**: In `handlers/download.py`, added rate-limiting delays and `retry_telegram_api` wrappers when sending multiple sticker files as separate documents, preventing Telegram `429 Too Many Requests` flood errors.
- **Native Telegram File Downloading**: Replaced fragile raw HTTPX file requests with `python-telegram-bot`'s native `bot.get_file()` and `tg_file.download_as_bytearray()`.
- **Fixed Missing HTML Parse Mode**: Added `parse_mode="HTML"` in `handlers/clone.py` line 57 to prevent raw `<i>` HTML tags from rendering as plain text.
- **Added `pytest.ini`**: Configured root `pythonpath = .` so tests run reliably across all environments without manual path configuration.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
