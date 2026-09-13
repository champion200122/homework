import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io
from config import Config

class GeminiClient:
    """Клиент для работы с Google Gemini API"""
    
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
        genai.configure(api_key=config.google_api_key)
        
        # Настройки безопасности
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model = genai.GenerativeModel(
            model_name=config.model,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "max_output_tokens": 4000,
            },
            safety_settings=self.safety_settings
        )
    
    async def check_homework(self, task_photos_bytes: list, student_photos_bytes: list, captions: list = None) -> str:
        """Проверить домашнюю работу через Gemini"""
        if not task_photos_bytes:
            return "❌ Нет фотографий задания"
        if not student_photos_bytes:
            return "❌ Нет фотографий работ учеников"
        
        try:
            # Формируем контент для Gemini
            content_parts = []
            
            # Добавляем системный промпт
            content_parts.append(f"СИСТЕМНАЯ ИНСТРУКЦИЯ: {self.SYSTEM_PROMPT}\n\n")
            
            # Добавляем фото задания
            content_parts.append("📋 ФОТОГРАФИИ С ЗАДАНИЕМ:\n")
            for i, photo_bytes in enumerate(task_photos_bytes, 1):
                content_parts.append(f"Задание - фото {i}:\n")
                content_parts.append({"mime_type": "image/jpeg", "data": photo_bytes})
            
            # Добавляем фото работ учеников
            content_parts.append("\n\n📝 РАБОТЫ УЧЕНИКОВ:\n")
            for i, (photo_bytes, caption) in enumerate(zip(student_photos_bytes, captions or []), 1):
                if caption:
                    content_parts.append(f"\nРабота ученика {i} ({caption}):\n")
                else:
                    content_parts.append(f"\nРабота ученика {i}:\n")
                content_parts.append({"mime_type": "image/jpeg", "data": photo_bytes})
            
            # Отправляем запрос
            response = await self.model.generate_content_async(content_parts)
            
            if not response.candidates:
                return "❌ Модель не смогла сгенерировать ответ"
            
            return response.text
        
        except Exception as e:
            return f"❌ Ошибка при запросе к API: {str(e)}"
