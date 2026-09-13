import base64
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot

from storage import storage
from config import Config
from nemotron import NemotronClient
from keyboards import get_main_menu

router = Router()

class HomeworkStates(StatesGroup):
    waiting_for_task = State()

# Инициализация клиента
config = Config()
nemotron = NemotronClient(config)


def check_teacher(message: Message) -> bool:
    """Проверка, что пользователь - учитель"""
    return message.from_user.id == config.teacher_id


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие и главное меню"""
    if not check_teacher(message):
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    
    await message.answer(
        f"👋 Здравствуйте!\n\n"
        f"Я - бот для проверки домашних заданий.\n\n"
        f"📌 <b>Как пользоваться:</b>\n"
        f"1. Нажмите '📝 Новое задание' и отправьте текст задания\n"
        f"2. Пересылайте фотографии тетрадей учеников\n"
        f"3. Нажмите '📷 Проверить тетради' для анализа\n\n"
        f"Вы также можете напрямую переслать фото - я автоматически добавлю его в очередь проверки.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📝 Новое задание")
async def btn_new_task(message: Message, state: FSMContext):
    """Запрос нового задания"""
    if not check_teacher(message):
        return
    
    await message.answer(
        "📝 <b>Пришлите текст задания</b>\n\n"
        "Можно переслать сообщение или написать новый текст.\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await state.set_state(HomeworkStates.waiting_for_task)


@router.message(F.text == "🗑️ Очистить задание")
async def btn_clear_task(message: Message):
    """Очистка задания и всех работ"""
    if not check_teacher(message):
        return
    
    storage.clear_task()
    await message.answer(
        "✅ Задание и все работы очищены!\n\n"
        "Можете установить новое задание.",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📷 Проверить тетради")
async def btn_check_photos(message: Message):
    """Проверка всех накопленных фото"""
    if not check_teacher(message):
        return
    
    if not storage.has_task():
        await message.answer(
            "⚠️ Сначала установите задание!\n"
            "Нажмите '📝 Новое задание'.",
            reply_markup=get_main_menu()
        )
        return
    
    if not storage.has_photos():
        await message.answer(
            "⚠️ Нет фотографий для проверки!\n"
            "Перешлите фотографии тетрадей учеников.",
            reply_markup=get_main_menu()
        )
        return
    
    # Показываем статус начала проверки
    processing_msg = await message.answer(
        f"🔍 Начинаю проверку {len(storage.student_photos)} фотографий...\n"
        f"Это может занять 1-2 минуты."
    )
    
    # Скачиваем и конвертируем фото в base64
    photos_base64 = []
    bot = message.bot
    
    try:
        for i, file_id in enumerate(storage.student_photos, 1):
            await processing_msg.edit_text(
                f"🔍 Обрабатываю фото {i}/{len(storage.student_photos)}..."
            )
            
            file = await bot.get_file(file_id)
            photo_bytes = await bot.download_file(file.file_path)
            photo_b64 = base64.b64encode(photo_bytes.read()).decode('utf-8')
            photos_base64.append(photo_b64)
        
        await processing_msg.edit_text("🤖 Отправляю на анализ AI модели...")
        
        # Отправляем в Nemotron
        result = await nemotron.check_homework(
            task=storage.task_text,
            photos_base64=photos_base64,
            captions=storage.photo_captions
        )
        
        # Отправляем результат (разбиваем на части если слишком длинный)
        await processing_msg.delete()
        
        # Telegram лимит - 4096 символов
        if len(result) <= 4000:
            await message.answer(
                f"✅ <b>Результат проверки:</b>\n\n{result}",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
        else:
            # Разбиваем на части
            await message.answer("✅ <b>Результат проверки (часть 1):</b>", parse_mode="HTML")
            for i in range(0, len(result), 4000):
                chunk = result[i:i+4000]
                await message.answer(chunk, parse_mode="HTML")
            await message.answer("✅ Проверка завершена!", reply_markup=get_main_menu())
    
    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка при проверке: {str(e)}")


@router.message(F.text == "📋 Показать задание")
async def btn_show_task(message: Message):
    """Показать текущее задание и статус"""
    if not check_teacher(message):
        return
    
    if not storage.has_task():
        await message.answer(
            "📋 Задание не установлено.\n"
            "Нажмите '📝 Новое задание' для установки.",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer(
        f"📋 <b>Текущее задание:</b>\n\n"
        f"{storage.task_text}\n\n"
        f"📊 <b>Статус:</b>\n{storage.get_status()}",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(Command("cancel"))
@router.message(StateFilter(HomeworkStates.waiting_for_task), F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    if not check_teacher(message):
        return
    
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_main_menu())


@router.message(StateFilter(HomeworkStates.waiting_for_task))
async def receive_task(message: Message, state: FSMContext):
    """Получение текста задания"""
    if not check_teacher(message):
        return
    
    # Берем текст или caption
    task_text = message.text or message.caption or ""
    
    if not task_text.strip():
        await message.answer("⚠️ Пустое сообщение. Отправьте текст задания.")
        return
    
    storage.set_task(task_text.strip())
    await state.clear()
    
    await message.answer(
        f"✅ <b>Задание установлено!</b>\n\n"
        f"{task_text[:500]}{'...' if len(task_text) > 500 else ''}\n\n"
        f"Теперь пересылайте фотографии тетрадей учеников.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


# Автоматическое добавление фото при пересылке
@router.message(F.photo)
async def receive_photo(message: Message):
    """Получение фотографии (работы ученика)"""
    if not check_teacher(message):
        return
    
    # Берем фото максимального размера
    photo = message.photo[-1]
    
    # Проверяем, есть ли задание
    if not storage.has_task():
        await message.answer(
            "⚠️ Сначала установите задание!\n"
            "Нажмите '📝 Новое задание'.",
            reply_markup=get_main_menu()
        )
        return
    
    # Добавляем фото в очередь
    caption = message.caption or ""
    num = storage.add_photo(photo.file_id, caption)
    
    await message.answer(
        f"✅ Фото добавлено в очередь проверки (#{num})\n"
        f"Всего фото в очереди: {len(storage.student_photos)}\n\n"
        f"Нажмите '📷 Проверить тетради' когда будете готовы.",
        reply_markup=get_main_menu()
    )


@router.message(F.text)
async def unknown_text(message: Message):
    """Неизвестные текстовые команды"""
    if not check_teacher(message):
        return
    
    # Если есть активное состояние - не реагируем
    # Иначе показываем меню
    if message.text not in ["📝 Новое задание", "📷 Проверить тетради", 
                            "🗑️ Очистить задание", "📋 Показать задание"]:
        await message.answer(
            "🤔 Не понимаю команду.\n"
            "Используйте кнопки меню ниже.",
            reply_markup=get_main_menu()
        )
