from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import get_user_role, register_user

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Регистрируем пользователя
    await register_user(user_id, username, full_name)
    
    # Получаем роль
    role = await get_user_role(user_id)
    
    if role == 'admin':
        await message.answer(
            f"👋 Привет, <b>Администратор</b>!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n"
            f"👤 {full_name}\n\n"
            f"<b>Доступные команды:</b>\n"
            f"📦 /catalog - Управление каталогом\n"
            f"📊 /stats - Статистика\n"
            f"👥 /users - Управление пользователями"
        )
    elif role == 'worker':
        await message.answer(
            f"👋 Привет, <b>Работник</b>!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n"
            f"👤 {full_name}\n\n"
            f"<b>Доступные команды:</b>\n"
            f"📋 /orders - Управление заказами\n"
            f"🔔 /notifications - Уведомления"
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в магазин мебели!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n"
            f"👤 {full_name}\n\n"
            f"<b>Доступные команды:</b>\n"
            f"🛋 /catalog - Каталог товаров\n"
            f"🛒 /cart - Корзина\n"
            f"📦 /orders - Мои заказы"
        )