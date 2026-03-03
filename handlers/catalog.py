from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncpg
from database import pool

router = Router()


class MilanConfig(StatesGroup):
    choosing_doors = State()
    choosing_door_type = State()
    choosing_tubes = State()
    choosing_handles = State()
    choosing_drawers = State()
    choosing_antresol = State()


@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Главное меню каталога"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛋 Милан", callback_data="cat_milan")],
        [InlineKeyboardButton(text="✨ Элегант", callback_data="cat_elegant")],
        [InlineKeyboardButton(text="💎 Премиум", callback_data="cat_premium")],
        [InlineKeyboardButton(text="🔧 Техно", callback_data="cat_techno")],
        [InlineKeyboardButton(text="🚪 Прихожие", callback_data="cat_hallway")],
        [InlineKeyboardButton(text="📦 Комоды", callback_data="cat_dresser")],
        [InlineKeyboardButton(text="🪑 Тумбы", callback_data="cat_cabinet")],
    ])
    
    await message.answer(
        "📋 <b>Каталог мебели</b>\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cat_milan")
async def milan_start(callback: CallbackQuery, state: FSMContext):
    """Начало конфигурации Милан"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="2 двери", callback_data="milan_doors_2"),
            InlineKeyboardButton(text="3 двери", callback_data="milan_doors_3"),
        ],
        [
            InlineKeyboardButton(text="4 двери", callback_data="milan_doors_4"),
            InlineKeyboardButton(text="5 дверей", callback_data="milan_doors_5"),
        ],
        [
            InlineKeyboardButton(text="6 дверей", callback_data="milan_doors_6"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_text(
        "🛋 <b>Милан - Шкаф-купе</b>\n\n"
        "Выберите количество дверей:",
        reply_markup=keyboard
    )
    await state.set_state(MilanConfig.choosing_doors)


@router.callback_query(F.data.startswith("milan_doors_"))
async def milan_choose_door_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа дверей"""
    doors = int(callback.data.split("_")[-1])
    await state.update_data(doors=doors)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇹🇷 Турция/Рим", callback_data="milan_type_tr")],
        [InlineKeyboardButton(text="✨ Айша", callback_data="milan_type_aysha")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cat_milan")],
    ])
    
    await callback.message.edit_text(
        f"🛋 <b>Милан - {doors} дверей</b>\n\n"
        "Выберите тип дверей:",
        reply_markup=keyboard
    )
    await state.set_state(MilanConfig.choosing_door_type)


@router.callback_query(F.data.startswith("milan_type_"))
async def milan_choose_tubes(callback: CallbackQuery, state: FSMContext):
    """Выбор количества труб (для 6 дверей) или переход к ручкам"""
    door_type = callback.data.split("_")[-1]
    data = await state.get_data()
    doors = data['doors']
    
    await state.update_data(door_type=door_type)
    
    # Для 6 дверей спрашиваем про трубы
    if doors == 6:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 труба", callback_data="milan_tubes_1")],
            [InlineKeyboardButton(text="2 трубы", callback_data="milan_tubes_2")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_doors_{doors}")],
        ])
        
        await callback.message.edit_text(
            f"🛋 <b>Милан - {doors} дверей</b>\n"
            f"Тип: {'Турция/Рим' if door_type == 'tr' else 'Айша'}\n\n"
            "Выберите количество труб:",
            reply_markup=keyboard
        )
        await state.set_state(MilanConfig.choosing_tubes)
    else:
        # Переходим к выбору ручек
        await milan_choose_handles_start(callback, state, doors, door_type, None)


async def milan_choose_handles_start(callback: CallbackQuery, state: FSMContext, doors: int, door_type: str, tubes: int = None):
    """Выбор ручек"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30см (стандарт)", callback_data="milan_handle_30")],
        [InlineKeyboardButton(text="60см (+700₽/шт)", callback_data="milan_handle_60")],
        [InlineKeyboardButton(text="100см (+1000₽/шт)", callback_data="milan_handle_100")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_type_{door_type}")],
    ])
    
    # Получаем базовую цену
    async with pool.acquire() as conn:
        if tubes:
            price = await conn.fetchval(
                "SELECT price FROM milan_configs WHERE doors = $1 AND door_type LIKE $2",
                doors, f"%{tubes} труб%"
            )
        else:
            door_name = 'Турция/Рим' if door_type == 'tr' else 'Айша'
            price = await conn.fetchval(
                "SELECT price FROM milan_configs WHERE doors = $1 AND door_type = $2",
                doors, door_name
            )
    
    await state.update_data(base_price=price, tubes=tubes)
    
    text = f"🛋 <b>Милан - {doors} дверей</b>\n"
    text += f"Тип: {'Турция/Рим' if door_type == 'tr' else 'Айша'}\n"
    if tubes:
        text += f"Трубы: {tubes}\n"
    text += f"\n💰 Базовая цена: <b>{price:,}₽</b>\n\n"
    text += "Выберите ручки:"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_handles)


@router.callback_query(F.data.startswith("milan_tubes_"))
async def milan_tubes_selected(callback: CallbackQuery, state: FSMContext):
    """Трубы выбраны"""
    tubes = int(callback.data.split("_")[-1])
    data = await state.get_data()
    await milan_choose_handles_start(callback, state, data['doors'], data['door_type'], tubes)


@router.callback_query(F.data.startswith("milan_handle_"))
async def milan_handle_selected(callback: CallbackQuery, state: FSMContext):
    """Ручки выбраны, спрашиваем про ящики"""
    handle_size = int(callback.data.split("_")[-1])
    data = await state.get_data()
    
    handle_prices = {30: 0, 60: 700, 100: 1000}
    handle_price = handle_prices[handle_size] * data['doors']
    
    await state.update_data(handle_size=handle_size, handle_price=handle_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да (+2000₽)", callback_data="milan_drawers_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="milan_drawers_no")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_type_{data['door_type']}")],
    ])
    
    total_price = data['base_price'] + handle_price
    
    text = f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"Тип: {'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'}\n"
    if data.get('tubes'):
        text += f"Трубы: {data['tubes']}\n"
    text += f"Ручки: {handle_size}см\n\n"
    text += f"💰 Текущая цена: <b>{total_price:,}₽</b>\n\n"
    text += "Добавить выдвижные ящики?"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_drawers)


@router.callback_query(F.data.startswith("milan_drawers_"))
async def milan_drawers_selected(callback: CallbackQuery, state: FSMContext):
    """Ящики выбраны, спрашиваем про антресоль"""
    has_drawers = callback.data.split("_")[-1] == "yes"
    data = await state.get_data()
    
    drawers_price = 2000 if has_drawers else 0
    await state.update_data(has_drawers=has_drawers, drawers_price=drawers_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="milan_antresol_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="milan_antresol_no")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_handle_{data['handle_size']}")],
    ])
    
    total_price = data['base_price'] + data['handle_price'] + drawers_price
    
    text = f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"Тип: {'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'}\n"
    if data.get('tubes'):
        text += f"Трубы: {data['tubes']}\n"
    text += f"Ручки: {data['handle_size']}см\n"
    text += f"Ящики: {'Да' if has_drawers else 'Нет'}\n\n"
    text += f"💰 Текущая цена: <b>{total_price:,}₽</b>\n\n"
    text += "Добавить антресоль?"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_antresol)


@router.callback_query(F.data.startswith("milan_antresol_"))
async def milan_final(callback: CallbackQuery, state: FSMContext):
    """Финальная конфигурация"""
    has_antresol = callback.data.split("_")[-1] == "yes"
    data = await state.get_data()
    
    # Рассчитываем цену антресоли
    antresol_price = 0
    if has_antresol:
        doors = data['doors']
        door_type = data['door_type']
        
        # Антресоль по размеру шкафа
        antresol_doors = doors
        if doors in [3, 5]:
            antresol_doors = 4
        
        # Базовая цена антресоли
        async with pool.acquire() as conn:
            door_name = 'Турция/Рим' if door_type == 'tr' else 'Айша'
            antresol_base = await conn.fetchval(
                "SELECT price FROM milan_configs WHERE doors = $1 AND door_type = $2",
                antresol_doors, door_name
            )
        
        antresol_price = antresol_base
        
        # Айша +500₽ за дверь антресоли
        if door_type == 'aysha':
            antresol_price += 500 * antresol_doors
    
    total_price = data['base_price'] + data['handle_price'] + data['drawers_price'] + antresol_price
    
    await state.update_data(has_antresol=has_antresol, antresol_price=antresol_price, total_price=total_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data="milan_add_to_cart")],
        [InlineKeyboardButton(text="🔄 Изменить конфигурацию", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")],
    ])
    
    text = "✅ <b>Конфигурация готова!</b>\n\n"
    text += f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"Тип: {'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'}\n"
    if data.get('tubes'):
        text += f"Трубы: {data['tubes']}\n"
    text += f"Ручки: {data['handle_size']}см\n"
    text += f"Ящики: {'Да (+2000₽)' if data['has_drawers'] else 'Нет'}\n"
    text += f"Антресоль: {'Да (+' + f'{antresol_price:,}₽)' if has_antresol else 'Нет'}\n\n"
    text += f"💰 <b>ИТОГО: {total_price:,}₽</b>"
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    """Возврат в каталог"""
    await state.clear()
    await cmd_catalog(callback.message)
    await callback.answer()