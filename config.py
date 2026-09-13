import os
from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
    teacher_id: int = int(os.environ.get("TEACHER_ID", "827744412"))
    webhook_url: str = os.environ.get("RENDER_EXTERNAL_URL", "")
    port: int = int(os.environ.get("PORT", "8000"))
    model: str = "gemini-1.5-flash"  # или "gemini-1.5-pro" для лучшего качества
