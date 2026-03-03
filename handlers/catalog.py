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
    6: 25200
}

# Цены антресолей
ANTRESOL_PRICES = {
    2: 4000,
    3: 6000,
    4: 8000,
    5: 11000,
    6: 11800
}

# Размеры шкафов (базовая высота 240см)
MILAN_SIZES = {
    2: {"width": 100, "height": 240, "depth": 60},
    3: {"width": 150, "height": 240, "depth": 60},
    4: {"width": 200, "height": 240, "depth": 60},
    5: {"width": 250, "height": 240, "depth": 60},
    6: {"width": 300, "height": 240, "depth": 60}
}


def calculate_price(doors, door_type, handle_size, tubes, has_antresol, has_drawers):
    """Расчёт цены"""
    # Базовая цена (Турция/Рим)
    base_price = MILAN_BASE_PRICES[doors]
    
    # Айша: -1000 + (1000 × кол-во дверей)
    aysha_extra = 0
    if door_type == 'Айша':
        aysha_extra = -1000 + (1000 * doors)
    
    # 6 дверей, 1 труба → +1800
    tubes_extra = 0
    if doors == 6 and tubes == 1:
        tubes_extra = 1800
    
    # Ручки
    handle_prices = {30: 0, 60: 700, 100: 1000}
    handle_price = handle_prices.get(handle_size, 0) * doors
    
    # Ящики
    drawers_price = 2000 if has_drawers else 0
    
    # Антресоль
    antresol_price = 0
    if has_antresol:
        antresol_doors = doors
        if doors in [3, 5]:
            antresol_doors = 4
        
        antresol_price = ANTRESOL_PRICES.get(antresol_doors, 0)
        
        # Айша антресоль +500₽/дверь
        if door_type == 'Айша':
            antresol_price += 500 * antresol_doors
    
    total = base_price + aysha_extra + tubes_extra + handle_price + drawers_price + antresol_price
    
    return {
        'base': base_price,
        'aysha_extra': aysha_extra,
        'tubes_extra': tubes_extra,
        'handle_price': handle_price,
        'drawers_price': drawers_price,
        'antresol_price': antresol_price,
        'total': total
    }


def get_sizes_text(doors, has_antresol):
    """Получить текст с размерами"""
    size = MILAN_SIZES[doors]
    height = size["height"]
    
    # Антресоль добавляет +50см к высоте
    if has_antresol:
        height += 50
    
    return f"Ширина: {size['width']}см, Высота: {height}см, Глубина: {size['depth']}см"


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
    
    # Стартовая конфигурация (Турция, 30см ручки, без доп)
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
    
    # Проверяем есть ли данные
    if 'doors' not in data:
        await callback.answer("⚠️ Сессия истекла. Выберите заново.", show_alert=True)
        await milan_start(callback, state)
        return
    
    doors = data['doors']
    door_type = data.get('door_type', 'Турция/Рим')
    handle_size = data.get('handle_size', 30)
    tubes = data.get('tubes')
    has_antresol = data.get('has_antresol', False)
    has_drawers = data.get('has_drawers', False)
    
    # Расчёт цены
    prices = calculate_price(doors, door_type, handle_size, tubes, has_antresol, has_drawers)
    
    await state.update_data(total_price=prices['total'])
    
    # Формируем текст
    text = f"🛋 <b>Милан - Шкаф-купе {doors} дверей</b>\n\n"
    
    # Размеры (с учётом антресоли)
    sizes_text = get_sizes_text(doors, has_antresol)
    text += f"📐 <b>Размеры:</b>\n{sizes_text}\n\n"
    
    text += f"<b>Конфигурация:</b>\n"
    text += f"├ Двери: {door_type}"
    if prices['aysha_extra'] != 0:
        text += f" ({'+' if prices['aysha_extra'] > 0 else ''}{prices['aysha_extra']:,}₽)"
    text += "\n"
    
    if tubes:
        text += f"├ Трубы: {tubes} шт"
        if prices['tubes_extra'] > 0:
            text += f" (+{prices['tubes_extra']:,}₽)"
        text += "\n"
    
    text += f"├ Ручки: {handle_size}см"
    if prices['handle_price'] > 0:
        text += f" (+{prices['handle_price']:,}₽)"
    text += "\n"
    
    text += f"├ Ящики: {'Да' if has_drawers else 'Нет'}"
    if has_drawers:
        text += f" (+{prices['drawers_price']:,}₽)"
    text += "\n"
    
    text += f"└ Антресоль: {'Да' if has_antresol else 'Нет'}"
    if has_antresol:
        text += f" (+{prices['antresol_price']:,}₽, высота +50см)"
    text += "\n\n"
    
    text += f"💰 <b>ЦЕНА: {prices['total']:,}₽</b>"
    
    # Кнопки
    buttons = [
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
    ]
    
    # Для 6 дверей — выбор труб
    if doors == 6:
        buttons.append([
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 1 else '⚙️'} 1 труба",
                callback_data="milan_tubes_1"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 2 else '⚙️'} 2 трубы",
                callback_data="milan_tubes_2"
            ),
        ])
    
    buttons.extend([
        [
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 30 else '🔧'} 30см",
                callback_data="milan_handle_30"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 60 else '🔧'} 60см",
                callback_data="milan_handle_60"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if handle_size == 100 else '🔧'} 100см",
                callback_data="milan_handle_100"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if has_drawers else '➕'} Ящики +2000₽",
                callback_data="milan_toggle_drawers"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if has_antresol else '➕'} Антресоль",
                callback_data="milan_toggle_antresol"
            ),
        ],
        [InlineKeyboardButton(text="🛒 В корзину", callback_data="milan_add_cart")],
        [
            InlineKeyboardButton(text="🔄 Другой размер", callback_data="cat_milan"),
            InlineKeyboardButton(text="◀️ Каталог", callback_data="back_to_catalog")
        ],
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)
    
    await state.set_state(MilanConfig.viewing)


@router.callback_query(F.data.startswith("milan_door_"))
async def milan_change_door_type(callback: CallbackQuery, state: FSMContext):
    """Смена типа дверей"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
    door_type = 'Турция/Рим' if callback.data.endswith('_tr') else 'Айша'
    await state.update_data(door_type=door_type)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Двери: {door_type}")


@router.callback_query(F.data.startswith("milan_handle_"))
async def milan_change_handles(callback: CallbackQuery, state: FSMContext):
    """Смена ручек"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
    handle_size = int(callback.data.split("_")[-1])
    await state.update_data(handle_size=handle_size)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Ручки: {handle_size}см")


@router.callback_query(F.data.startswith("milan_tubes_"))
async def milan_change_tubes(callback: CallbackQuery, state: FSMContext):
    """Смена количества труб"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
    tubes = int(callback.data.split("_")[-1])
    await state.update_data(tubes=tubes)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Трубы: {tubes} шт")


@router.callback_query(F.data == "milan_toggle_drawers")
async def milan_toggle_drawers(callback: CallbackQuery, state: FSMContext):
    """Переключение ящиков"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
    has_drawers = not data.get('has_drawers', False)
    await state.update_data(has_drawers=has_drawers)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Ящики: {'добавлены' if has_drawers else 'убраны'}")


@router.callback_query(F.data == "milan_toggle_antresol")
async def milan_toggle_antresol(callback: CallbackQuery, state: FSMContext):
    """Переключение антресоли"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
    has_antresol = not data.get('has_antresol', False)
    await state.update_data(has_antresol=has_antresol)
    await show_product_card(callback, state)
    await callback.answer(f"✅ Антресоль: {'добавлена (+50см высота)' if has_antresol else 'убрана'}")


@router.callback_query(F.data == "milan_add_cart")
async def milan_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавление в корзину"""
    data = await state.get_data()
    if 'doors' not in data:
        await callback.answer("⚠️ Выберите шкаф заново", show_alert=True)
        await milan_start(callback, state)
        return
    
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