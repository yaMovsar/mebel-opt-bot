from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()


class MilanConfig(StatesGroup):
    viewing = State()


# Цены Милан (Турция/Рим — базовые)
MILAN_BASE_PRICES = {
    2: 11000,
    3: 14000,
    4: 21000,
    5: 24000,
    6: 25200  # 6 дверей, 2 трубы по умолчанию
}

# Доплата за Айшу
AYSHA_EXTRA = {
    2: 2000,   # 13000 - 11000
    3: 3000,   # 17000 - 14000
    4: 3000,   # 24000 - 21000
    5: 5000,   # 29000 - 24000
    6: 4800    # 30000 - 25200
}

# Цены антресолей (Турция/Рим)
ANTRESOL_PRICES = {
    2: 4000,   # 15000 - 11000
    3: 6000,   # 20000 - 14000 (для 3дв антр 4дв)
    4: 8000,   # 29000 - 21000
    5: 11000,  # 35000 - 24000 (для 5дв антр 4дв)
    6: 11800   # 37000 - 25200
}

# Размеры шкафов (примерные)
MILAN_SIZES = {
    2: "Ширина: 100см, Высота: 240см, Глубина: 60см",
    3: "Ширина: 150см, Высота: 240см, Глубина: 60см",
    4: "Ширина: 200см, Высота: 240см, Глубина: 60см",
    5: "Ширина: 250см, Высота: 240см, Глубина: 60см",
    6: "Ширина: 300см, Высота: 240см, Глубина: 60см"
}


@router.message(Command("catalog"))
async def cmd_catalog(message: Message, state: FSMContext):
    """Главное меню каталога"""
    await state.clear()
    
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
    """Выбор количества дверей Милан"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="2 двери", callback_data="milan_show_2"),
            InlineKeyboardButton(text="3 двери", callback_data="milan_show_3"),
        ],
        [
            InlineKeyboardButton(text="4 двери", callback_data="milan_show_4"),
            InlineKeyboardButton(text="5 дверей", callback_data="milan_show_5"),
        ],
        [
            InlineKeyboardButton(text="6 дверей", callback_data="milan_show_6"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_text(
        "🛋 <b>Милан - Шкаф-купе</b>\n\n"
        "Выберите количество дверей:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("milan_show_"))
async def milan_show_config(callback: CallbackQuery, state: FSMContext):
    """Показываем готовую конфигурацию"""
    doors = int(callback.data.split("_")[-1])
    
    # Стартовая конфигурация
    config = {
        'doors': doors,
        'door_type': 'Турция/Рим',
        'handle_size': 30,
        'tubes': 2 if doors == 6 else None,
        'has_antresol': False,
        'has_drawers': False
    }
    
    await state.update_data(**config)
    await show_product_card(callback, state)


async def show_product_card(callback: CallbackQuery, state: FSMContext):
    """Карточка товара с ценой и опциями"""
    data = await state.get_data()
    doors = data['doors']
    door_type = data['door_type']
    handle_size = data['handle_size']
    tubes = data.get('tubes')
    has_antresol = data['has_antresol']
    has_drawers = data['has_drawers']
    
    # Расчёт цены
    base_price = MILAN_BASE_PRICES[doors]
    
    # Айша
    if door_type == 'Айша':
        base_price += AYSHA_EXTRA[doors]
    
    # 6 дверей, 1 труба
    if doors == 6 and tubes == 1:
        base_price += 1800  # 27000 - 25200
    
    # Ручки
    handle_prices = {30: 0, 60: 700, 100: 1000}
    handle_price = handle_prices[handle_size] * doors
    
    # Ящики
    drawers_price = 2000 if has_drawers else 0
    
    # Антресоль
    antresol_price = 0
    if has_antresol:
        antresol_doors = doors
        if doors in [3, 5]:
            antresol_doors = 4
        
        antresol_price = ANTRESOL_PRICES[antresol_doors]
        
        # Айша +500₽/дверь на антресоль
        if door_type == 'Айша':
            antresol_price += 500 * antresol_doors
    
    total_price = base_price + handle_price + drawers_price + antresol_price
    
    await state.update_data(total_price=total_price)
    
    # Формируем текст
    text = f"🛋 <b>Милан - Шкаф-купе {doors} дверей</b>\n\n"
    
    text += f"📐 <b>Размеры:</b>\n{MILAN_SIZES[doors]}\n\n"
    
    text += f"<b>Конфигурация:</b>\n"
    text += f"├ Двери: {door_type}\n"
    if tubes:
        text += f"├ Трубы: {tubes} шт\n"
    text += f"├ Ручки: {handle_size}см"
    if handle_price > 0:
        text += f" (+{handle_price:,}₽)"
    text += f"\n├ Выдвижные ящики: {'Да (+2,000₽)' if has_drawers else 'Нет'}\n"
    text += f"└ Антресоль: {'Да (+' + f'{antresol_price:,}₽)' if has_antresol else 'Нет'}\n\n"
    
    text += f"💰 <b>ЦЕНА: {total_price:,}₽</b>"
    
    # Кнопки для изменения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{'✅' if door_type == 'Турция/Рим' else '🚪'} Турция/Рим",
                callback_data="milan_door_tr"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if door_type == 'Айша' else '✨'} Айша",
                callback_data="milan_door_aysha"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 30 else '🔧'} Ручки 30см",
                callback_data="milan_handle_30"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 60 else '🔧'} Ручки 60см",
                callback_data="milan_handle_60"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 100 else '🔧'} Ручки 100см",
                callback_data="milan_handle_100"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if has_drawers else '➕'} Выдвижные ящики",
                callback_data="milan_toggle_drawers"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if has_antresol else '➕'} Антресоль",
                callback_data="milan_toggle_antresol"
            ),
        ],
    ])
    
    # Для 6 дверей добавляем выбор труб
    if doors == 6:
        keyboard.inline_keyboard.insert(1, [
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 1 else '⚙️'} 1 труба",
                callback_data="milan_tubes_1"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 2 else '⚙️'} 2 трубы",
                callback_data="milan_tubes_2"
            ),
        ])
    
    # Кнопки действий
    keyboard.inline_keyboard.extend([
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data="milan_add_cart")],
        [
            InlineKeyboardButton(text="🔄 Другой размер", callback_data="cat_milan"),
            InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")
        ],
    ])
    
    # TODO: Здесь можно добавить фото
    # await callback.message.answer_photo(
    #     photo="URL_ФОТО",
    #     caption=text,
    #     reply_markup=keyboard
    # )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MilanConfig.viewing)


# Обработчики изменения опций
@router.callback_query(F.data.startswith("milan_door_"))
async def milan_change_door_type(callback: CallbackQuery, state: FSMContext):
    """Смена типа дверей"""
    door_type = 'Турция/Рим' if callback.data.endswith('_tr') else 'Айша'
    await state.update_data(door_type=door_type)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Двери: {door_type}")


@router.callback_query(F.data.startswith("milan_handle_"))
async def milan_change_handles(callback: CallbackQuery, state: FSMContext):
    """Смена ручек"""
    handle_size = int(callback.data.split("_")[-1])
    await state.update_data(handle_size=handle_size)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Ручки: {handle_size}см")


@router.callback_query(F.data.startswith("milan_tubes_"))
async def milan_change_tubes(callback: CallbackQuery, state: FSMContext):
    """Смена количества труб"""
    tubes = int(callback.data.split("_")[-1])
    await state.update_data(tubes=tubes)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Трубы: {tubes} шт")


@router.callback_query(F.data == "milan_toggle_drawers")
async def milan_toggle_drawers(callback: CallbackQuery, state: FSMContext):
    """Переключение ящиков"""
    data = await state.get_data()
    has_drawers = not data.get('has_drawers', False)
    await state.update_data(has_drawers=has_drawers)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Ящики: {'добавлены' if has_drawers else 'убраны'}")


@router.callback_query(F.data == "milan_toggle_antresol")
async def milan_toggle_antresol(callback: CallbackQuery, state: FSMContext):
    """Переключение антресоли"""
    data = await state.get_data()
    has_antresol = not data.get('has_antresol', False)
    await state.update_data(has_antresol=has_antresol)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Антресоль: {'добавлена' if has_antresol else 'убрана'}")


@router.callback_query(F.data == "milan_add_cart")
async def milan_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавление в корзину"""
    data = await state.get_data()
    
    # TODO: Сохранение в БД
    
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