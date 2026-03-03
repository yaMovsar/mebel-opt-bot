from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


# ================= ЦЕНЫ И РАЗМЕРЫ (МЕНЯЙТЕ ЗДЕСЬ) =================

# Базовые цены Милан (Турция/Рим)
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

# Размеры шкафов
MILAN_SIZES = {
    2: {"width": 100, "height": 240, "depth": 60},
    3: {"width": 150, "height": 240, "depth": 60},
    4: {"width": 200, "height": 240, "depth": 60},
    5: {"width": 250, "height": 240, "depth": 60},
    6: {"width": 300, "height": 240, "depth": 60}
}

# Цены ручек за штуку
HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}

# Цена ящиков
DRAWERS_PRICE = 2000

# ================= КОНЕЦ НАСТРОЕК =================


def parse_config(data: str) -> dict:
    """Парсим конфигурацию из callback_data"""
    # Формат: m_ДВЕРИ_ТИП_РУЧКИ_ТРУБЫ_ЯЩИКИ_АНТРЕСОЛЬ
    # Пример: m_6_tr_30_2_0_0
    parts = data.split("_")
    return {
        'doors': int(parts[1]),
        'door_type': 'Турция/Рим' if parts[2] == 'tr' else 'Айша',
        'door_code': parts[2],
        'handle_size': int(parts[3]),
        'tubes': int(parts[4]) if int(parts[1]) == 6 else None,
        'has_drawers': parts[5] == '1',
        'has_antresol': parts[6] == '1'
    }


def make_config_code(doors, door_code, handle, tubes, drawers, antresol):
    """Создаём код конфигурации для callback_data"""
    return f"m_{doors}_{door_code}_{handle}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}"


def calculate_price(config: dict) -> dict:
    """Расчёт цены"""
    doors = config['doors']
    door_type = config['door_type']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    
    # Базовая цена
    base_price = MILAN_BASE_PRICES[doors]
    
    # Айша: -1000 + (1000 × кол-во дверей)
    aysha_extra = 0
    if door_type == 'Айша':
        aysha_extra = -1000 + (1000 * doors)
    
    # 6 дверей, 1 труба
    tubes_extra = 0
    if doors == 6 and tubes == 1:
        tubes_extra = 1800
    
    # Ручки
    handle_price = HANDLE_PRICES.get(handle_size, 0) * doors
    
    # Ящики
    drawers_price = DRAWERS_PRICE if has_drawers else 0
    
    # Антресоль
    antresol_price = 0
    if has_antresol:
        antresol_doors = 4 if doors in [3, 5] else doors
        antresol_price = ANTRESOL_PRICES.get(antresol_doors, 0)
        if door_type == 'Айша':
            antresol_price += 500 * antresol_doors
    
    total = base_price + aysha_extra + tubes_extra + handle_price + drawers_price + antresol_price
    
    return {
        'aysha_extra': aysha_extra,
        'tubes_extra': tubes_extra,
        'handle_price': handle_price,
        'drawers_price': drawers_price,
        'antresol_price': antresol_price,
        'total': total
    }


def get_sizes_text(doors, has_antresol):
    """Текст с размерами"""
    size = MILAN_SIZES[doors]
    height = size["height"] + (50 if has_antresol else 0)
    return f"Ширина: {size['width']}см, Высота: {height}см, Глубина: {size['depth']}см"


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
async def milan_start(callback: CallbackQuery):
    """Выбор количества дверей"""
    buttons = []
    for doors in [2, 3, 4, 5, 6]:
        # Стартовая конфигурация: Турция, 30см, 2 трубы, без ящиков, без антресоли
        code = make_config_code(doors, 'tr', 30, 2, False, False)
        text = f"{doors} {'двери' if doors < 5 else 'дверей'}"
        buttons.append(InlineKeyboardButton(text=text, callback_data=code))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons[0:2],  # 2, 3
        buttons[2:4],  # 4, 5
        [buttons[4]],  # 6
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_text(
        "🛋 <b>Милан - Шкаф-купе</b>\n\n"
        "Выберите количество дверей:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("m_"))
async def milan_show_config(callback: CallbackQuery):
    """Показываем карточку товара"""
    config = parse_config(callback.data)
    prices = calculate_price(config)
    
    doors = config['doors']
    door_type = config['door_type']
    door_code = config['door_code']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    
    # Формируем текст
    text = f"🛋 <b>Милан - Шкаф-купе {doors} дверей</b>\n\n"
    text += f"📐 <b>Размеры:</b>\n{get_sizes_text(doors, has_antresol)}\n\n"
    
    text += f"<b>Конфигурация:</b>\n"
    text += f"├ Двери: {door_type}"
    if prices['aysha_extra'] != 0:
        text += f" ({'+' if prices['aysha_extra'] > 0 else ''}{prices['aysha_extra']:,}₽)"
    text += "\n"
    
    if doors == 6:
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
        text += f" (+{prices['antresol_price']:,}₽, +50см)"
    text += "\n\n"
    
    text += f"💰 <b>ЦЕНА: {prices['total']:,}₽</b>"
    
    # Кнопки
    other_door = 'aysha' if door_code == 'tr' else 'tr'
    other_door_name = 'Айша' if door_code == 'tr' else 'Турция/Рим'
    
    buttons = [
        # Тип дверей
        [
            InlineKeyboardButton(
                text=f"{'✅' if door_code == 'tr' else '🚪'} Турция/Рим",
                callback_data=make_config_code(doors, 'tr', handle_size, tubes or 2, has_drawers, has_antresol)
            ),
            InlineKeyboardButton(
                text=f"{'✅' if door_code == 'aysha' else '✨'} Айша",
                callback_data=make_config_code(doors, 'aysha', handle_size, tubes or 2, has_drawers, has_antresol)
            ),
        ],
    ]
    
    # Трубы для 6 дверей
    if doors == 6:
        buttons.append([
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 1 else '⚙️'} 1 труба",
                callback_data=make_config_code(doors, door_code, handle_size, 1, has_drawers, has_antresol)
            ),
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 2 else '⚙️'} 2 трубы",
                callback_data=make_config_code(doors, door_code, handle_size, 2, has_drawers, has_antresol)
            ),
        ])
    
    # Ручки
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 30 else '🔧'} 30см",
            callback_data=make_config_code(doors, door_code, 30, tubes or 2, has_drawers, has_antresol)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 60 else '🔧'} 60см",
            callback_data=make_config_code(doors, door_code, 60, tubes or 2, has_drawers, has_antresol)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 100 else '🔧'} 100см",
            callback_data=make_config_code(doors, door_code, 100, tubes or 2, has_drawers, has_antresol)
        ),
    ])
    
    # Ящики и антресоль
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if has_drawers else '➕'} Ящики +{DRAWERS_PRICE}₽",
            callback_data=make_config_code(doors, door_code, handle_size, tubes or 2, not has_drawers, has_antresol)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if has_antresol else '➕'} Антресоль",
            callback_data=make_config_code(doors, door_code, handle_size, tubes or 2, has_drawers, not has_antresol)
        ),
    ])
    
    # Действия
    buttons.extend([
        [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"cart_{callback.data}")],
        [
            InlineKeyboardButton(text="🔄 Другой размер", callback_data="cat_milan"),
            InlineKeyboardButton(text="◀️ Каталог", callback_data="back_to_catalog")
        ],
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавление в корзину"""
    config_code = callback.data.replace("cart_", "")
    config = parse_config(config_code)
    prices = calculate_price(config)
    
    # TODO: Сохранение в БД
    
    await callback.answer(f"✅ Добавлено в корзину!\nЦена: {prices['total']:,}₽", show_alert=True)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="go_to_cart")],
        [InlineKeyboardButton(text="🛋 Добавить ещё", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Возврат в каталог"""
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