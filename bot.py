import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
import sqlite3
from datetime import datetime

# Настройки
BOT_TOKEN = "8646680836:AAETwdULkbpfB6UpGUkJziG46QT0I1Zsf3E"
MAIN_ADMIN_ID = 741468078

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Прокси для обхода блокировки (используем публичный SOCKS5)
session = AiohttpSession(
    proxy="socks5://orbtl.s5.opennetwork.cc:999"
)

# Инициализация
bot = Bot(token=BOT_TOKEN, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# База данных
def init_db():
    logger.info("Инициализация базы данных...")
    conn = sqlite3.connect('furniture_bot.db')
    c = conn.cursor()
    
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        role TEXT DEFAULT 'client',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Товары
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        model TEXT,
        doors INTEGER,
        base_price INTEGER,
        description TEXT,
        photo_id TEXT,
        dimensions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Заказы
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        items TEXT,
        total_price INTEGER,
        client_comment TEXT,
        worker_note TEXT,
        status TEXT DEFAULT 'new',
        deadline DATE,
        delivery_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')
    
    # Добавляем главного админа и работника
    c.execute('INSERT OR IGNORE INTO users (user_id, role) VALUES (?, ?)', 
              (MAIN_ADMIN_ID, 'admin'))
    c.execute('INSERT OR IGNORE INTO users (user_id, role) VALUES (?, ?)', 
              (7792815764, 'worker'))
    
    conn.commit()
    conn.close()
    logger.info("База данных готова!")

# Проверка роли
def get_user_role(user_id):
    conn = sqlite3.connect('furniture_bot.db')
    c = conn.cursor()
    c.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    role = result[0] if result else 'client'
    logger.info(f"Пользователь {user_id} имеет роль: {role}")
    return role

# Сохранение пользователя
def save_user(user_id, username, full_name, role='client'):
    conn = sqlite3.connect('furniture_bot.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (user_id, username, full_name, role) 
                 VALUES (?, ?, ?, ?)''', (user_id, username, full_name, role))
    conn.commit()
    conn.close()
    logger.info(f"Пользователь сохранён: {user_id} ({username}) - {role}")

# Состояния
class AddAdmin(StatesGroup):
    waiting_for_id = State()

class AddWorker(StatesGroup):
    waiting_for_id = State()

# Клавиатуры
def get_main_menu(role):
    if role == 'admin':
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Управление товарами", callback_data="admin_products")],
            [InlineKeyboardButton(text="📊 Все заказы", callback_data="admin_orders")],
            [InlineKeyboardButton(text="👥 Управление доступами", callback_data="admin_users")],
            [InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")]
        ])
    elif role == 'worker':
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="worker_orders")],
            [InlineKeyboardButton(text="🔴 Горящие заказы", callback_data="worker_urgent")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="worker_stats")]
        ])
    else:  # client
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Шкафы", callback_data="cat_shkaf")],
            [InlineKeyboardButton(text="🧥 Прихожие", callback_data="cat_prihojie")],
            [InlineKeyboardButton(text="🗄 Комоды", callback_data="cat_komod")],
            [InlineKeyboardButton(text="🛏 Тумбы", callback_data="cat_tumba")],
            [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="📄 Скачать прайс", callback_data="download_price")]
        ])

def get_admin_users_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")],
        [InlineKeyboardButton(text="➕ Добавить работника", callback_data="add_worker")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="list_admins")],
        [InlineKeyboardButton(text="📋 Список работников", callback_data="list_workers")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"Получена команда /start от {message.from_user.id} (@{message.from_user.username})")
    
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    role = get_user_role(user_id)
    save_user(user_id, username, full_name, role)
    
    if role == 'admin':
        text = f"👋 Добро пожаловать, {full_name}!\n\n🔧 Панель администратора"
    elif role == 'worker':
        text = f"👋 Добро пожаловать, {full_name}!\n\n📦 Панель работника"
    else:
        text = f"👋 Добро пожаловать, {full_name}!\n\n🛒 Выберите категорию товаров:"
    
    await message.answer(text, reply_markup=get_main_menu(role))
    logger.info(f"Отправлено меню для роли: {role}")

# Главное меню
@dp.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    logger.info(f"Возврат в главное меню: {callback.from_user.id}")
    role = get_user_role(callback.from_user.id)
    
    if role == 'admin':
        text = "🔧 Панель администратора"
    elif role == 'worker':
        text = "📦 Панель работника"
    else:
        text = "🛒 Выберите категорию товаров:"
    
    await callback.message.edit_text(text, reply_markup=get_main_menu(role))

# Управление доступами
@dp.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery):
    logger.info(f"Открыто управление доступами: {callback.from_user.id}")
    if get_user_role(callback.from_user.id) != 'admin':
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 Управление доступами:",
        reply_markup=get_admin_users_menu()
    )

# Добавить админа
@dp.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if get_user_role(callback.from_user.id) != 'admin':
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📝 Отправьте Telegram ID нового админа:\n\n"
        "Пользователь может узнать свой ID у бота @userinfobot"
    )
    await state.set_state(AddAdmin.waiting_for_id)

@dp.message(AddAdmin.waiting_for_id)
async def add_admin_process(message: Message, state: FSMContext):
    try:
        new_admin_id = int(message.text)
        
        conn = sqlite3.connect('furniture_bot.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO users (user_id, role) VALUES (?, ?)', 
                  (new_admin_id, 'admin'))
        conn.commit()
        conn.close()
        
        await message.answer(
            f"✅ Админ добавлен!\n\nID: {new_admin_id}",
            reply_markup=get_admin_users_menu()
        )
        
        # Уведомляем нового админа
        try:
            await bot.send_message(
                new_admin_id,
                "🎉 Вам выданы права администратора!\n\n"
                "Используйте /start для входа в панель управления."
            )
        except:
            pass
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число:")
        return
    
    await state.clear()

# Добавить работника
@dp.callback_query(F.data == "add_worker")
async def add_worker_start(callback: CallbackQuery, state: FSMContext):
    if get_user_role(callback.from_user.id) != 'admin':
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📝 Отправьте Telegram ID нового работника:\n\n"
        "Пользователь может узнать свой ID у бота @userinfobot"
    )
    await state.set_state(AddWorker.waiting_for_id)

@dp.message(AddWorker.waiting_for_id)
async def add_worker_process(message: Message, state: FSMContext):
    try:
        new_worker_id = int(message.text)
        
        conn = sqlite3.connect('furniture_bot.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO users (user_id, role) VALUES (?, ?)', 
                  (new_worker_id, 'worker'))
        conn.commit()
        conn.close()
        
        await message.answer(
            f"✅ Работник добавлен!\n\nID: {new_worker_id}",
            reply_markup=get_admin_users_menu()
        )
        
        # Уведомляем работника
        try:
            await bot.send_message(
                new_worker_id,
                "🎉 Вам выдан доступ к панели работника!\n\n"
                "Используйте /start для входа."
            )
        except:
            pass
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число:")
        return
    
    await state.clear()

# Список админов
@dp.callback_query(F.data == "list_admins")
async def list_admins(callback: CallbackQuery):
    if get_user_role(callback.from_user.id) != 'admin':
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    conn = sqlite3.connect('furniture_bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id, username, full_name FROM users WHERE role = ?', ('admin',))
    admins = c.fetchall()
    conn.close()
    
    text = "👑 Список администраторов:\n\n"
    for admin in admins:
        user_id, username, full_name = admin
        username_str = f"@{username}" if username else "нет username"
        name_str = full_name if full_name else "Неизвестно"
        text += f"• {name_str} ({username_str})\n  ID: {user_id}\n\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_users_menu())

# Список работников
@dp.callback_query(F.data == "list_workers")
async def list_workers(callback: CallbackQuery):
    if get_user_role(callback.from_user.id) != 'admin':
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    conn = sqlite3.connect('furniture_bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id, username, full_name FROM users WHERE role = ?', ('worker',))
    workers = c.fetchall()
    conn.close()
    
    text = "👷 Список работников:\n\n"
    for worker in workers:
        user_id, username, full_name = worker
        username_str = f"@{username}" if username else "нет username"
        name_str = full_name if full_name else "Неизвестно"
        text += f"• {name_str} ({username_str})\n  ID: {user_id}\n\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_users_menu())

# Заглушки для остальных разделов
@dp.callback_query(F.data.startswith("cat_"))
async def category_handler(callback: CallbackQuery):
    await callback.answer("🚧 Раздел в разработке", show_alert=True)

@dp.callback_query(F.data.startswith("admin_"))
async def admin_handler(callback: CallbackQuery):
    if callback.data == "admin_users":
        return
    await callback.answer("🚧 Раздел в разработке", show_alert=True)

@dp.callback_query(F.data.startswith("worker_"))
async def worker_handler(callback: CallbackQuery):
    await callback.answer("🚧 Раздел в разработке", show_alert=True)

@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    await callback.answer("🚧 Раздел в разработке", show_alert=True)

@dp.callback_query(F.data == "download_price")
async def download_price(callback: CallbackQuery):
    await callback.answer("🚧 Раздел в разработке", show_alert=True)

# Запуск бота
async def main():
    try:
        init_db()
        logger.info("=" * 50)
        logger.info("🚀 БОТ УСПЕШНО ЗАПУЩЕН!")
        logger.info(f"📋 Главный админ: {MAIN_ADMIN_ID}")
        logger.info("=" * 50)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    asyncio.run(main())