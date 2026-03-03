from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import pool

router = Router()


class MilanConfig(StatesGroup):
    choosing_doors = State()
    choosing_door_type = State()
    choosing_tubes = State()
    choosing_handles = State()
    choosing_drawers = State()
    choosing_antresol = State()


# Цены Милан
MILAN_PRICES = {
    'tr': {  # Турция/Рим
        2: 11000,
        3: 14000,
        4: 21000,
        5: 24000,
        '6_2': 25200,  # 6 дверей, 2 трубы
        '6_1': 27000   # 6 дверей, 1 труба
    },
    'aysha': {  # Айша
        2: 13000,
        3: 17000,
        4: 24000,
        5: 29000,
        '6_2': 30000,
        '6_1': 32000
    }
}

# Цены антресолей
ANTRESOL_PRICES = {
    'tr': {  # Турция/Рим
        2: 15000,
        4: 29000,
        6: 37000
    },
    'aysha': {  # Айша
        2: 18000,
        4: 34000,
        6: 45200
    }
}


@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Главное меню каталога"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛋 Милан", callback_data="cat_milan")],
        [InlineKeyboardButton(text="✨ Элегант (скоро)", callback_data="cat_soon")],
        [InlineKeyboardButton(text="💎 Премиум (скоро)", callback_data="cat_soon")],
        [InlineKeyboardButton(text="🔧 Техно (скоро)", callback_data="cat_soon")],
    ])
    
    await message.answer(
        "📋 <b>Каталог мебели</b>\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cat_soon")
async def catalog_soon(callback: CallbackQuery):
    await callback.answer("🚧 Раздел в разработке", show_alert=True)


@router.callback_query(F.data == "cat_milan")
async def milan_start(callback: CallbackQuery, state: FSMContext):
    """Начало конфигурации Милан"""
    await state.clear()
    
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
        [InlineKeyboardButton(text="🚪 Турция/Рим", callback_data="milan_type_tr")],
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
async def milan_after_door_type(callback: CallbackQuery, state: FSMContext):
    """После выбора типа дверей"""
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
        
        door_name = 'Турция/Рим' if door_type == 'tr' else 'Айша'
        
        await callback.message.edit_text(
            f"🛋 <b>Милан - {doors} дверей</b>\n"
            f"Тип дверей: {door_name}\n\n"
            "Выберите количество труб:",
            reply_markup=keyboard
        )
        await state.set_state(MilanConfig.choosing_tubes)
    else:
        # Переходим к выбору ручек
        await show_handles_menu(callback, state)


@router.callback_query(F.data.startswith("milan_tubes_"))
async def milan_tubes_selected(callback: CallbackQuery, state: FSMContext):
    """Трубы выбраны"""
    tubes = int(callback.data.split("_")[-1])
    await state.update_data(tubes=tubes)
    await show_handles_menu(callback, state)


async def show_handles_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню выбора ручек"""
    data = await state.get_data()
    doors = data['doors']
    door_type = data['door_type']
    tubes = data.get('tubes')
    
    # Получаем базовую цену
    if doors == 6 and tubes:
        base_price = MILAN_PRICES[door_type][f'6_{tubes}']
    else:
        base_price = MILAN_PRICES[door_type][doors]
    
    await state.update_data(base_price=base_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30см (стандарт)", callback_data="milan_handle_30")],
        [InlineKeyboardButton(text="60см (+700₽/шт)", callback_data="milan_handle_60")],
        [InlineKeyboardButton(text="100см (+1000₽/шт)", callback_data="milan_handle_100")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_type_{door_type}")],
    ])
    
    door_name = 'Турция/Рим' if door_type == 'tr' else 'Айша'
    
    text = f"🛋 <b>Милан - {doors} дверей</b>\n"
    text += f"Тип дверей: {door_name}\n"
    if tubes:
        text += f"Трубы: {tubes}\n"
    text += f"\n💰 Базовая цена: <b>{base_price:,}₽</b>\n\n"
    text += "Выберите ручки:"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_handles)


@router.callback_query(F.data.startswith("milan_handle_"))
async def milan_handle_selected(callback: CallbackQuery, state: FSMContext):
    """Ручки выбраны"""
    handle_size = int(callback.data.split("_")[-1])
    data = await state.get_data()
    
    # Расчёт цены ручек
    handle_prices = {30: 0, 60: 700, 100: 1000}
    handle_price = handle_prices[handle_size] * data['doors']
    
    await state.update_data(handle_size=handle_size, handle_price=handle_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да (+2000₽)", callback_data="milan_drawers_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="milan_drawers_no")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_type_{data['door_type']}")],
    ])
    
    total = data['base_price'] + handle_price
    door_name = 'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'
    
    text = f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"Тип дверей: {door_name}\n"
    if data.get('tubes'):
        text += f"Трубы: {data['tubes']}\n"
    text += f"Ручки: {handle_size}см"
    if handle_price > 0:
        text += f" (+{handle_price:,}₽)"
    text += f"\n\n💰 Текущая цена: <b>{total:,}₽</b>\n\n"
    text += "Добавить выдвижные ящики?"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_drawers)


@router.callback_query(F.data.startswith("milan_drawers_"))
async def milan_drawers_selected(callback: CallbackQuery, state: FSMContext):
    """Ящики выбраны"""
    has_drawers = callback.data.split("_")[-1] == "yes"
    data = await state.get_data()
    
    drawers_price = 2000 if has_drawers else 0
    await state.update_data(has_drawers=has_drawers, drawers_price=drawers_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="milan_antresol_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="milan_antresol_no")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"milan_handle_{data['handle_size']}")],
    ])
    
    total = data['base_price'] + data['handle_price'] + drawers_price
    door_name = 'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'
    
    text = f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"Тип дверей: {door_name}\n"
    if data.get('tubes'):
        text += f"Трубы: {data['tubes']}\n"
    text += f"Ручки: {data['handle_size']}см\n"
    text += f"Ящики: {'Да (+2000₽)' if has_drawers else 'Нет'}\n\n"
    text += f"💰 Текущая цена: <b>{total:,}₽</b>\n\n"
    text += "Добавить антресоль?"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.choosing_antresol)


@router.callback_query(F.data.startswith("milan_antresol_"))
async def milan_final(callback: CallbackQuery, state: FSMContext):
    """Финальная конфигурация"""
    has_antresol = callback.data.split("_")[-1] == "yes"
    data = await state.get_data()
    
    # Расчёт цены антресоли
    antresol_price = 0
    if has_antresol:
        doors = data['doors']
        door_type = data['door_type']
        
        # Антресоль по размеру шкафа (3,5 дв → 4 дв антресоль)
        antresol_doors = doors
        if doors in [3, 5]:
            antresol_doors = 4
        
        antresol_price = ANTRESOL_PRICES[door_type][antresol_doors]
    
    total = data['base_price'] + data['handle_price'] + data['drawers_price'] + antresol_price
    
    await state.update_data(
        has_antresol=has_antresol,
        antresol_price=antresol_price,
        total_price=total
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data="milan_add_cart")],
        [InlineKeyboardButton(text="🔄 Изменить конфигурацию", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")],
    ])
    
    door_name = 'Турция/Рим' if data['door_type'] == 'tr' else 'Айша'
    
    text = "✅ <b>Конфигурация готова!</b>\n\n"
    text += f"🛋 <b>Милан - {data['doors']} дверей</b>\n"
    text += f"├ Тип дверей: {door_name}\n"
    if data.get('tubes'):
        text += f"├ Трубы: {data['tubes']}\n"
    text += f"├ Ручки: {data['handle_size']}см"
    if data['handle_price'] > 0:
        text += f" (+{data['handle_price']:,}₽)"
    text += "\n"
    text += f"├ Ящики: {'Да (+2,000₽)' if data['has_drawers'] else 'Нет'}\n"
    text += f"└ Антресоль: {'Да (+' + f'{antresol_price:,}₽)' if has_antresol else 'Нет'}\n\n"
    text += f"💰 <b>ИТОГО: {total:,}₽</b>"
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "milan_add_cart")
async def milan_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавление в корзину"""
    data = await state.get_data()
    
    # TODO: Сохранение в БД корзины
    
    await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="go_to_cart")],
        [InlineKeyboardButton(text="🛋 Добавить ещё", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    """Возврат в каталог"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛋 Милан", callback_data="cat_milan")],
        [InlineKeyboardButton(text="✨ Элегант (скоро)", callback_data="cat_soon")],
        [InlineKeyboardButton(text="💎 Премиум (скоро)", callback_data="cat_soon")],
        [InlineKeyboardButton(text="🔧 Техно (скоро)", callback_data="cat_soon")],
    ])
    
    await callback.message.edit_text(
        "📋 <b>Каталог мебели</b>\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "go_to_cart")
async def go_to_cart(callback: CallbackQuery):
    """Переход в корзину"""
    await callback.answer("🛒 Корзина в разработке", show_alert=True)