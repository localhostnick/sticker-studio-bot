<div align="center">

# 🚀 ѕтιᴄᴋᴇʀ sтυᴅιᴏ ʙᴏт
### *The Ultimate High-Performance Telegram Sticker Pack Manager & Automation Bot*

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/python--telegram--bot-v22%2B-2CA5E0.svg?style=for-the-badge&logo=telegram&logoColor=white)](https://python-telegram-bot.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen.svg?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/realnikhil29/sticker-studio-bot/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

[**Live Demo (@ST1CKERSTUD10BOT)**](https://t.me/ST1CKERSTUD10BOT) • [**Key Features**](#-key-features) • [**Architecture**](#-architecture--design) • [**Deployment**](#-vps--docker-deployment) • [**Documentation**](#-api--environment-configuration)

---
</div>

## 📌 Executive Overview

**Sticker Studio Bot** is a state-of-the-art, asynchronous, enterprise-grade **Telegram Sticker Pack Manager Bot** engineered in **Python 3.12+** using the latest **python-telegram-bot (v22+)**, **SQLAlchemy Async ORM**, **Pillow**, and **FFmpeg**.

Designed for speed, scalability, and seamless user experience, it bypasses the manual bottleneck of official sticker bots by providing **batch processing**, **ZIP extraction**, **one-click pack cloning**, **multi-format exporting (ZIP/PNG/WEBP)**, and **automated video/GIF sticker encoding**.

---

## 🔥 Key Features

<table>
  <tr>
    <td width="50%">
      <h3>📦 1. Batch ZIP Upload</h3>
      <p>Upload a single <code>.zip</code> archive containing hundreds of images. Automatically extracts, sorts, validates extensions, and converts everything into Telegram-compliant stickers instantly.</p>
    </td>
    <td width="50%">
      <h3>📸 2. Multi-Media Collection</h3>
      <p>Send multiple photos or document files in a single batch message. The bot buffers and processes them seamlessly in the background.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📋 3. 1-Click Pack Cloning</h3>
      <p>Paste any public Telegram sticker pack link (<code>t.me/addstickers/...</code>). The bot fetches, converts, and re-creates a brand new pack under your ownership within seconds.</p>
    </td>
    <td width="50%">
      <h3>💾 4. Multi-Format Exporter</h3>
      <p>Download any Telegram sticker set in your format of choice: <b>ZIP Archive</b>, <b>PNG</b>, or <b>WEBP</b> for easy cross-platform sharing.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎥 5. Animated GIF & WEBM Support</h3>
      <p>Automatic VP9 encoding pipeline for animated GIFs and WEBM files matching Telegram video sticker specifications (512x512, 30fps, ≤3s, ≤256KB).</p>
    </td>
    <td width="50%">
      <h3>🔄 6. Intelligent Auto-Splitting</h3>
      <p>Exceeding Telegram limits? The engine automatically partitions packs with >120 static or >50 video stickers into clean multi-part sets (Part 1, Part 2, etc.).</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>⏳ 7. Real-Time Progress Visualizer</h3>
      <p>Live inline progress updates: <code>[██████░░░░] 60% (12/20)</code> featuring custom <b>Small Caps typography</b> for a premium UI experience.</p>
    </td>
    <td width="50%">
      <h3>🛡️ 8. Enterprise Resilience</h3>
      <p>Built-in task cancellation (<code>/cancel</code>), non-blocking async architecture, automated SQLite/PostgreSQL audit logging, and exponential backoff rate limiting.</p>
    </td>
  </tr>
</table>

---

## 🏗️ Architecture & System Design

The project is architected following **SOLID principles** and a strictly decoupled layered design:

```mermaid
graph TD
    User([👤 Telegram User]) -->|Commands / Media Upload| Handlers[🎮 Handler Layer]
    Handlers -->|Track User Profile| Middleware[🛡️ User Tracker Middleware]
    Handlers -->|Enforce Queue & Cancel| TaskQueue[⏳ Task Queue Service]
    
    TaskQueue --> ImagePipeline[🎨 Image Processing Engine (Pillow)]
    TaskQueue --> VideoPipeline[🎥 Video Processing Engine (FFmpeg)]
    TaskQueue --> ZipExtractor[📦 Safe ZIP Service]
    
    ImagePipeline --> TelegramAPI[⚡ Telegram Bot API (PTB v22+)]
    VideoPipeline --> TelegramAPI
    ZipExtractor --> ImagePipeline
    
    TelegramAPI --> DB[(DB Async SQLite / PostgreSQL)]
```

### 📁 Directory Structure

```
TG-STICKER-MANAGER/
├── .github/workflows/ci.yml # GitHub Actions CI pipeline
├── .gitignore               # Production ignore rules
├── .env.example             # Environment configuration template
├── Dockerfile               # Production Docker container definition
├── docker-compose.yml       # Docker Compose deployment setup
├── LICENSE                  # MIT License
├── README.md                # SEO-Optimized README
├── CONTRIBUTING.md          # Open-source contribution guidelines
├── SECURITY.md              # Security vulnerability policy
├── requirements.txt         # Core dependencies
├── bot.py                   # Application entry point & lifecycle manager
├── config.py                # Pydantic settings manager
├── database.py              # Async SQLAlchemy engine & session factory
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
│   ├── rate_limiter.py      # Exponential backoff retry handler
│   └── typography.py        # Small Caps typography formatter
│
└── tests/                   # Pytest Test Suite
    ├── test_image_service.py
    ├── test_zip_service.py
    └── test_short_name.py
```

---

## 💻 Quick Start & Installation

### Prerequisites
- **Python**: `3.12` or higher
- **FFmpeg**: Installed and available in PATH (Required for video/GIF processing)

### Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/realnikhil29/sticker-studio-bot.git
   cd sticker-studio-bot
   ```

2. **Create Virtual Environment**:
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
   Edit `.env` and add your Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather):
   ```env
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   DATABASE_URL=sqlite+aiosqlite:///sticker_bot.db
   LOG_LEVEL=INFO
   ```

5. **Launch the Bot**:
   ```bash
   python bot.py
   ```

---

## 🐳 VPS & Docker Deployment

Deploy in production using Docker Compose with zero hassle:

```bash
# Build and launch containerized daemon
docker-compose up -d --build

# View real-time logs
docker-compose logs -f
```

---

## ⚙️ Environment Configuration Parameters

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | `str` | *Required* | Telegram Bot API Token from @BotFather |
| `DATABASE_URL` | `str` | `sqlite+aiosqlite:///sticker_bot.db` | Async database URI (SQLite / PostgreSQL) |
| `TEMP_DIRECTORY` | `str` | `./temp` | Temporary staging directory for media processing |
| `STORAGE_DIRECTORY` | `str` | `./storage` | Permanent storage directory |
| `LOGS_DIRECTORY` | `str` | `./logs` | Application log output directory |
| `LOG_LEVEL` | `str` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MAX_UPLOAD_SIZE` | `int` | `52428800` (50MB) | Maximum file size limit for ZIP/media uploads |
| `MAX_IMAGES` | `int` | `120` | Max stickers per static pack (Telegram API limit) |

---

## 🧪 Testing

Execute the automated pytest suite:

```bash
pytest
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [**CONTRIBUTING.md**](CONTRIBUTING.md) for details on code standards and submitting pull requests.

---

## 📜 License

This project is open-source software licensed under the [**MIT License**](LICENSE).

<div align="center">
Made with ❤️ by <a href="https://github.com/realnikhil29">Nikhil</a>
</div>
