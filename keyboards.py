from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Новое задание"),
                KeyboardButton(text="📋 Показать задание")
            ],
            [
                KeyboardButton(text="📷 Добавить работы"),
                KeyboardButton(text="🔍 Проверить работы")
            ],
            [
                KeyboardButton(text="🗑️ Очистить всё")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_task_menu() -> ReplyKeyboardMarkup:
    """Меню при добавлении задания"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Готово")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard
