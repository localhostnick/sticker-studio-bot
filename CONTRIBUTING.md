# Contributing to Telegram Sticker Pack Manager Bot

Thank you for your interest in contributing to the **Telegram Sticker Pack Manager Bot**! We welcome bug reports, feature requests, documentation improvements, and code contributions.

---

## 🚀 How to Contribute

### 1. Fork & Clone the Repository
```bash
git clone https://github.com/your-username/TG-STICKER-MANAGER.git
cd TG-STICKER-MANAGER
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your test `BOT_TOKEN`:
```bash
cp .env.example .env
```

### 4. Create a Feature Branch
```bash
git checkout -b feature/my-awesome-feature
```

### 5. Code Style & Verification
Ensure your code adheres to standard Python 3.12+ type hinting and formatting:
- Run `python -c "import compileall; compileall.compile_dir('.', force=True)"`
- Run `pytest` for unit testing.

### 6. Submit a Pull Request
Push your branch to GitHub and open a Pull Request against the `main` branch with a clear description of your changes.

---

## 📜 Code of Conduct
Please be polite, professional, and helpful to all contributors and community members.
