from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import get_user_role

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if role == 'admin':
        await message.answer(
            f"👋 Привет, <b>Администратор</b>!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n\n"
            f"Доступные команды:\n"
            f"/admin - Админ-панель"
        )
    elif role == 'worker':
        await message.answer(
            f"👋 Привет, <b>Работник</b>!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n\n"
            f"Доступные команды:\n"
            f"/orders - Заказы"
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в магазин мебели!\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>\n\n"
            f"Доступные команды:\n"
            f"/catalog - Каталог товаров\n"
            f"/cart - Корзина\n"
            f"/orders - Мои заказы"
        )