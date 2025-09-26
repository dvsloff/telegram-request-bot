import asyncio
import sqlite3
import openpyxl
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile


# =======================
# Настройка
# =======================
API_TOKEN = "8386229219:AAHEWJVxjkitDXMqXDikEJS56BrKrty2cnE"   # сюда вставь токен из BotFather
ADMIN_ID = 474305924              # сюда вставь свой Telegram ID

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# =======================
# База данных
# =======================
conn = sqlite3.connect("requests.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    goal TEXT
                    user_id INTEGER,
                    status TEXT
                )''')
conn.commit()

# =======================
# Главное меню
# =======================
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧑‍💻 Обо мне")],
        [KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="📝 Оставить заявку")]
    ],
    resize_keyboard=True
)

# =======================
# Команды
# =======================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Это бот-визитка.\n\n"
        "📌 Возможности:\n"
        "— Узнать информацию обо мне\n"
        "— Получить мои контакты\n"
        "— Оставить заявку\n\n"
        "Выбирай нужный раздел 👇",
        reply_markup=main_kb
    )

# =======================
# Пользовательские кнопки
# =======================
@dp.message(F.text == "🧑‍💻 Обо мне")
async def about(message: types.Message):
    await message.answer("Данила, 22 года, пишу ботов")

@dp.message(F.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer("Связаться со мной можно:\nTelegram: @dvsloff\nEmail: danila.vsloff@gmail.com")

# =======================
# FSM для заявки
# =======================
class RequestForm(StatesGroup):
    name = State()
    phone = State()
    goal = State()
@dp.message(F.text == "📝 Оставить заявку")
async def start_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(RequestForm.name)

@dp.message(RequestForm.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(RequestForm.phone)

@dp.message(RequestForm.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Какая цель вашей заявки? (например: консультация, заказ услуги)")
    await state.set_state(RequestForm.goal)

@dp.message(RequestForm.goal)
async def get_goal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    phone = data["phone"]
    goal = message.text
    user_id = message.from_user.id

    cursor.execute("INSERT INTO requests (name, phone, goal, user_id, status) VALUES (?, ?, ?, ?, ?)",
                   (name, phone, goal, user_id, "Новая"))
    conn.commit()

    # уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"📩 Новая заявка!\n\nИмя: {name}\nТелефон: {phone}\nЦель: {goal}\nОт: @{message.from_user.username or 'без username'}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{cursor.lastrowid}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{cursor.lastrowid}")
                ]
            ]
        )
    )

    await message.answer("Спасибо! Ваша заявка отправлена ✅")
    await state.clear()

# =======================
# Админ: обработка заявок
# =======================
@dp.callback_query(F.data.startswith("accept_"))
async def accept_request(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE requests SET status='Принята' WHERE id=?", (req_id,))
    conn.commit()

    cursor.execute("SELECT user_id FROM requests WHERE id=?", (req_id,))
    user_id = cursor.fetchone()[0]

    await bot.send_message(user_id, "✅ Ваша заявка была принята!")
    await callback.message.edit_text("✅ Заявка отмечена как принята")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_request(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE requests SET status='Отклонена' WHERE id=?", (req_id,))
    conn.commit()

    cursor.execute("SELECT user_id FROM requests WHERE id=?", (req_id,))
    user_id = cursor.fetchone()[0]

    await bot.send_message(user_id, "❌ Ваша заявка была отклонена.")
    await callback.message.edit_text("❌ Заявка отмечена как отклонённая")

# КОМАНДЫ АДМИНА
# ==================
@dp.message(Command("all_requests"))
async def all_requests(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет доступа к этой команде.")
    cursor.execute("SELECT * FROM requests")
    rows = cursor.fetchall()
    if not rows:
        await message.answer("📭 Заявок пока нет.")
    else:
        text = "📋 Список заявок:\n\n"
        for row in rows:
            text += f"#{row[0]} | {row[1]} | {row[2]} | Статус: {row[3]}\n"
        await message.answer(text)


@dp.message(Command("clear_requests"))
async def clear_requests(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет доступа к этой команде.")
    cursor.execute("DELETE FROM requests")
    conn.commit()
    await message.answer("🗑 Все заявки удалены.")


@dp.message(Command("export_requests"))
async def export_requests(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет доступа к этой команде.")

    cursor.execute("SELECT * FROM requests")
    rows = cursor.fetchall()

    if not rows:
        return await message.answer("📭 Нет заявок для экспорта.")

    # Создаём Excel файл
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Заявки"

    # Заголовки
    ws.append(["Номер заявки", "Имя", "Телефон","UserID","Статус","Цель"])

    # Данные
    for row in rows:
        ws.append(row)

    # Сохраняем
    file_path = "requests_export.xlsx"
    wb.save(file_path)

    # Отправляем файл админу
    file = FSInputFile(file_path)
    await message.answer_document(file, caption="📂 Экспорт заявок")


@dp.message(Command("help_admin"))
async def help_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "👮‍♂️ Доступные команды админа:\n\n"
        "/all_requests — показать все заявки\n"
        "/clear_requests — удалить все заявки\n"
        "/export_requests — экспортировать заявки в Excel\n"
        "/help_admin — список доступных команд"
    )

# =======================
# Запуск
# =======================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())