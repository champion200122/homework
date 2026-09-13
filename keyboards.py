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
                KeyboardButton(text="📷 Проверить тетради"),
                KeyboardButton(text="🗑️ Очистить задание")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard
