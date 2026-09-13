import base64
from google import genai
from google.genai import types
from config import Config


class GeminiClient:
    """Клиент для работы с Google Gemini API (новый SDK)"""
    
    SYSTEM_PROMPT = """Ты - опытный и внимательный учитель. Твоя задача - тщательно проверить домашнюю работу ученика.

Тебе даны фотографии с заданием (учебник, распечатка или записанное задание) и фотографии тетради ученика с выполненной работой.

Проанализируй работу по следующему плану:
1. Кратко опиши, что нужно было сделать по заданию
2. Проанализируй каждое решение/ответ ученика
3. Укажи на ошибки и неточности (если есть)
4. Отметь правильные решения
5. Дай конкретные рекомендации для улучшения

Отвечай на русском языке, структурированно и понятно."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = genai.Client(api_key=config.google_api_key)
        self.model_name = config.model
    
    async def check_homework(self, task_photos_bytes: list, student_photos_bytes: list, captions: list = None) -> str:
        """Проверить домашнюю работу через Gemini"""
        if not task_photos_bytes:
            return "❌ Нет фотографий задания"
        if not student_photos_bytes:
            return "❌ Нет фотографий работ учеников"
        
        try:
            # Формируем содержимое запроса
            contents = []
            
            # Системный промпт и заголовок
            text_parts = [f"ИНСТРУКЦИЯ: {self.SYSTEM_PROMPT}\n\n"]
            
            # Фото задания
            text_parts.append("📋 ФОТОГРАФИИ С ЗАДАНИЕМ:\n")
            for i, photo_bytes in enumerate(task_photos_bytes, 1):
                text_parts.append(f"Задание - фото {i}:\n")
                contents.append(types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"))
            
            # Фото работ учеников
            text_parts.append("\n📝 РАБОТЫ УЧЕНИКОВ:\n")
            for i, (photo_bytes, caption) in enumerate(zip(student_photos_bytes, captions or []), 1):
                if caption:
                    text_parts.append(f"\nРабота ученика {i} ({caption}):\n")
                else:
                    text_parts.append(f"\nРабота ученика {i}:\n")
                contents.append(types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"))
            
            # Добавляем текстовую часть в начало
            contents.insert(0, types.Part.from_text(text="".join(text_parts)))
            
            # Отправляем запрос
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=4000,
                    system_instruction=self.SYSTEM_PROMPT
                )
            )
            
            if not response.text:
                return "❌ Модель не смогла сгенерировать ответ"
            
            return response.text
        
        except Exception as e:
            return f"❌ Ошибка при запросе к API: {str(e)}"
    
    async def close(self):
        """Закрытие клиента (если нужно)"""
        pass
