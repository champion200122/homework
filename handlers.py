from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from storage import storage
from config import Config
from gemini import GeminiClient
from keyboards import get_main_menu

router = Router()

class HomeworkStates(StatesGroup):
    waiting_for_task = State()  # Ожидание фото задания
    waiting_for_student_work = State()  # Ожидание фото работ

# Инициализация
config = Config()
gemini = GeminiClient(config)


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
        f"1. Нажмите '📝 Новое задание' и отправьте фото задания (учебник/распечатка)\n"
        f"2. Нажмите '📷 Добавить работы' и перешлите фото тетрадей учеников\n"
        f"3. Нажмите '🔍 Проверить работы' для анализа\n\n"
        f"Вы также можете напрямую переслать фото работ - они автоматически добавятся в очередь.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📝 Новое задание")
async def btn_new_task(message: Message, state: FSMContext):
    """Запрос нового задания"""
    if not check_teacher(message):
        return
    
    storage.clear_task()
    await message.answer(
        "📝 <b>Пришлите фотографии задания</b>\n\n"
        "Можно отправить несколько фото (учебник, распечатка, доска и т.д.).\n"
        "Когда закончите, нажмите '✅ Готово'.\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML",
        reply_markup=get_task_menu()
    )
    await state.set_state(HomeworkStates.waiting_for_task)


@router.message(F.text == "✅ Готово", StateFilter(HomeworkStates.waiting_for_task))
async def btn_task_done(message: Message, state: FSMContext):
    """Завершение загрузки задания"""
    if not check_teacher(message):
        return
    
    if not storage.has_task():
        await message.answer("⚠️ Вы не добавили ни одного фото задания!")
        return
    
    await state.clear()
    await message.answer(
        f"✅ <b>Задание установлено!</b>\n\n"
        f"Добавлено фото: {len(storage.task_photos)}\n\n"
        f"Теперь нажмите '📷 Добавить работы' и перешлите фото тетрадей учеников.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(StateFilter(HomeworkStates.waiting_for_task), F.photo)
async def receive_task_photo(message: Message):
    """Получение фото задания"""
    if not check_teacher(message):
        return
    
    photo = message.photo[-1]
    num = storage.add_task_photo(photo.file_id)
    
    await message.answer(f"✅ Фото задания добавлено (#{num})")


@router.message(F.text == "📷 Добавить работы")
async def btn_add_works(message: Message, state: FSMContext):
    """Добавление работ учеников"""
    if not check_teacher(message):
        return
    
    if not storage.has_task():
        await message.answer(
            "⚠️ Сначала установите задание!\n"
            "Нажмите '📝 Новое задание'.",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer(
        "📷 <b>Перешлите фотографии тетрадей учеников</b>\n\n"
        "Можно отправить по одному или пачкой.\n"
        "Когда будете готовы проверить, нажмите '🔍 Проверить работы'.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "🔍 Проверить работы")
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
            "⚠️ Нет работ для проверки!\n"
            "Нажмите '📷 Добавить работы' и перешлите фото тетрадей.",
            reply_markup=get_main_menu()
        )
        return
    
    # Показываем статус начала проверки
    processing_msg = await message.answer(
        f"🔍 Начинаю проверку {len(storage.student_photos)} работ...\n"
        f"Это может занять 1-2 минуты."
    )
    
    # Скачиваем все фото
    bot = message.bot
    
    try:
        # Скачиваем фото задания
        task_photos_bytes = []
        for i, file_id in enumerate(storage.task_photos, 1):
            await processing_msg.edit_text(f"🔍 Загружаю задание ({i}/{len(storage.task_photos)})...")
            file = await bot.get_file(file_id)
            photo_bytes = await bot.download_file(file.file_path)
            task_photos_bytes.append(photo_bytes.read())
        
        # Скачиваем фото работ
        student_photos_bytes = []
        for i, file_id in enumerate(storage.student_photos, 1):
            await processing_msg.edit_text(f"🔍 Загружаю работы ({i}/{len(storage.student_photos)})...")
            file = await bot.get_file(file_id)
            photo_bytes = await bot.download_file(file.file_path)
            student_photos_bytes.append(photo_bytes.read())
        
        await processing_msg.edit_text("🤖 Отправляю на анализ Gemini...")
        
        # Отправляем в Gemini
        result = await gemini.check_homework(
            task_photos_bytes=task_photos_bytes,
            student_photos_bytes=student_photos_bytes,
            captions=storage.photo_captions
        )
        
        # Отправляем результат
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
        f"Фото задания: {len(storage.task_photos)}\n\n"
        f"📊 <b>Статус:</b>\n{storage.get_status()}",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "🗑️ Очистить всё")
async def btn_clear_task(message: Message):
    """Очистка задания и всех работ"""
    if not check_teacher(message):
        return
    
    storage.clear_task()
    await message.answer(
        "✅ Всё очищено!\n\n"
        "Можете установить новое задание.",
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


# Автоматическое добавление фото работ
@router.message(F.photo, ~StateFilter(HomeworkStates.waiting_for_task))
async def receive_student_photo(message: Message):
    """Получение фотографии (работы ученика)"""
    if not check_teacher(message):
        return
    
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
        f"✅ Работа добавлена в очередь (#{num})\n"
        f"Всего работ в очереди: {len(storage.student_photos)}\n\n"
        f"Нажмите '🔍 Проверить работы' когда будете готовы.",
        reply_markup=get_main_menu()
    )


@router.message(F.text)
async def unknown_text(message: Message):
    """Неизвестные текстовые команды"""
    if not check_teacher(message):
        return
    
    await message.answer(
        "🤔 Не понимаю команду.\n"
        "Используйте кнопки меню ниже.",
        reply_markup=get_main_menu()
    )
