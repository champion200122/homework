from typing import List, Optional

class Storage:
    """Хранилище задания и работ учеников"""
    
    def __init__(self):
        self.task_text: Optional[str] = None
        self.student_photos: List[str] = []  # Telegram file_ids
        self.photo_captions: List[str] = []  # Подписи к фото
    
    def set_task(self, text: str) -> None:
        """Установить новое задание (очищает предыдущие работы)"""
        self.task_text = text
        self.student_photos = []
        self.photo_captions = []
    
    def clear_task(self) -> None:
        """Очистить задание и работы"""
        self.task_text = None
        self.student_photos = []
        self.photo_captions = []
    
    def add_photo(self, file_id: str, caption: str = "") -> int:
        """Добавить фото работы ученика. Возвращает номер в очереди."""
        self.student_photos.append(file_id)
        self.photo_captions.append(caption or f"Фото {len(self.student_photos)}")
        return len(self.student_photos)
    
    def has_task(self) -> bool:
        return self.task_text is not None and self.task_text.strip() != ""
    
    def has_photos(self) -> bool:
        return len(self.student_photos) > 0
    
    def get_status(self) -> str:
        """Возвращает текущий статус"""
        status_parts = []
        if self.has_task():
            status_parts.append(f"📝 Задание установлено ({len(self.task_text)} символов)")
        else:
            status_parts.append("📝 Задание не установлено")
        
        if self.has_photos():
            status_parts.append(f"📷 Фото в очереди: {len(self.student_photos)}")
        else:
            status_parts.append("📷 Нет фото для проверки")
        
        return "\n".join(status_parts)

# Глобальное хранилище
storage = Storage()
