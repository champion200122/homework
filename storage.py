from typing import List, Optional

class Storage:
    """Хранилище задания и работ учеников"""
    
    def __init__(self):
        self.task_photos: List[str] = []  # Telegram file_ids задания
        self.student_photos: List[str] = []  # Telegram file_ids работ
        self.photo_captions: List[str] = []  # Подписи к работам
    
    def set_task_photos(self, photo_ids: List[str]) -> None:
        """Установить новые фото задания (очищает предыдущие работы)"""
        self.task_photos = photo_ids
        self.student_photos = []
        self.photo_captions = []
    
    def add_task_photo(self, file_id: str) -> int:
        """Добавить фото к заданию. Возвращает номер."""
        self.task_photos.append(file_id)
        return len(self.task_photos)
    
    def clear_task(self) -> None:
        """Очистить задание и работы"""
        self.task_photos = []
        self.student_photos = []
        self.photo_captions = []
    
    def add_photo(self, file_id: str, caption: str = "") -> int:
        """Добавить фото работы ученика. Возвращает номер в очереди."""
        self.student_photos.append(file_id)
        self.photo_captions.append(caption or f"Работа {len(self.student_photos)}")
        return len(self.student_photos)
    
    def has_task(self) -> bool:
        return len(self.task_photos) > 0
    
    def has_photos(self) -> bool:
        return len(self.student_photos) > 0
    
    def get_status(self) -> str:
        """Возвращает текущий статус"""
        status_parts = []
        if self.has_task():
            status_parts.append(f"📝 Задание: {len(self.task_photos)} фото")
        else:
            status_parts.append("📝 Задание не установлено")
        
        if self.has_photos():
            status_parts.append(f"📷 Работы учеников: {len(self.student_photos)} фото")
        else:
            status_parts.append("📷 Нет работ для проверки")
        
        return "\n".join(status_parts)

# Глобальное хранилище
storage = Storage()
