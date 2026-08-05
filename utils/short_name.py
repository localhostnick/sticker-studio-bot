import re
import uuid
from config import settings


def sanitize_short_name(name_input: str, bot_username: str = "") -> str:
    """Sanitizes user input into a valid Telegram sticker short_name.
    
    Rule:
    - Only english letters, numbers, underscores
    - Must start with a letter
    - Must end with _by_<bot_username>
    - Total length <= 64 chars
    """
    bot = (bot_username or settings.BOT_USERNAME).lstrip("@")
    suffix = f"_by_{bot}" if bot else "_by_bot"
    max_prefix_len = 64 - len(suffix)

    # Clean characters (replace non-alphanumeric with underscore)
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name_input)
    # Remove consecutive underscores
    clean = re.sub(r"_+", "_", clean)
    # Ensure starts with letter
    if not clean or not clean[0].isalpha():
        clean = f"pack_{clean}"
    
    clean = clean.strip("_")[:max_prefix_len]
    if not clean:
        clean = "pack"

    result = f"{clean}{suffix}"
    return result[:64]


def generate_unique_short_name(title: str, bot_username: str = "") -> str:
    """Generates a guaranteed unique short_name based on pack title and UUID snippet."""
    bot = (bot_username or settings.BOT_USERNAME).lstrip("@")
    suffix = f"_by_{bot}" if bot else "_by_bot"
    
    uid = uuid.uuid4().hex[:6]
    clean_title = re.sub(r"[^a-zA-Z0-9]", "", title).lower()[:15]
    if not clean_title or not clean_title[0].isalpha():
        clean_title = "stk"
        
    max_prefix_len = 64 - len(suffix) - len(uid) - 1
    prefix = clean_title[:max_prefix_len]
    return f"{prefix}_{uid}{suffix}"
