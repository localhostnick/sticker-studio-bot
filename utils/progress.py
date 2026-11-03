def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Generates a visual progress bar.
    
    Example:
    current=4, total=10 => "████░░░░░░ 40%"
    """
    if total <= 0:
        return "░" * length + " 0%"
    
    percentage = min(1.0, max(0.0, current / total))
    filled_length = int(round(length * percentage))
    bar = "█" * filled_length + "░" * (length - filled_length)
    percent_str = f"{int(percentage * 100)}%"
    return f"{bar} {percent_str}"


def format_progress_message(action: str, current: int, total: int, details: str = "") -> str:
    """Formats a progress report string for Telegram edit_message_text."""
    bar = make_progress_bar(current, total)
    msg = f"⏳ <b>{action}</b>\n\n{bar}\n\n<b>Progress:</b> {current} / {total}"
    if details:
        msg += f"\n<i>{details}</i>"
    return msg
