import os
from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    api_key: str = os.environ.get("API_TOKENROUTER_KEY", "")
    teacher_id: int = int(os.environ.get("TEACHER_ID", "827744412"))
    webhook_url: str = os.environ.get("RENDER_EXTERNAL_URL", "")
    port: int = int(os.environ.get("PORT", "8000"))
    model: str = "nemotron-3-nano-omni-30b-a3b-reasoning"
    api_base: str = "https://api.tokenrouter.com/v1"
