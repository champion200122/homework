import aiohttp
import base64
from io import BytesIO
from config import Config

class NemotronClient:
    """Клиент для работы с Nemotron через tokenrouter.com"""
    
    SYSTEM_PROMPT = """Ты - опытный и внимательный учитель. Твоя задача - тщательно проверить домашнюю работу ученика.

Тебе дано задание и фотографии тетради ученика с выполненной работой.

Проанализируй работу по следующему плану:
1. Кратко оцени, что именно проверяется в задании
2. Проанализируй каждое решение/ответ
3. Укажи на ошибки и неточности (если есть)
4. Отметь правильные решения
5. Дай конкретные рекомендации для улучшения

Отвечай на русском языке, структурированно и понятно."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def check_homework(self, task: str, photos_base64: list, captions: list = None) -> str:
        """Проверить домашнюю работу через AI"""
        if not photos_base64:
            return "❌ Нет фотографий для проверки"
        
        # Формируем контент с текстом задания и изображениями
        content = [
            {"type": "text", "text": f"Задание для проверки:\n{task}\n\nНиже представлены фотографии работ ученика."}
        ]
        
        for i, (photo_b64, caption) in enumerate(zip(photos_base64, captions or []), 1):
            if caption:
                content.append({"type": "text", "text": f"\n📸 Фото {i} ({caption}):"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{photo_b64}"}
            })
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        try:
            async with self.session.post(
                f"{self.config.api_base}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"❌ Ошибка API ({response.status}):\n{error_text[:500]}"
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            return f"❌ Ошибка при запросе к API: {str(e)}"
    
    async def close(self):
        await self.session.close()
