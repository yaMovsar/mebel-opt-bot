from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


# ================= ЦЕНЫ И РАЗМЕРЫ (МЕНЯЙТЕ ЗДЕСЬ) =================

# Базовые цены Милан (цена за шкаф с дверями Турция)
MILAN_BASE_PRICES = {
    2: 11000,
    3: 14000,
    4: 21000,
    5: 24000,
    6: 25200
}

# Доплата за тип двери ЗА ШТУКУ
DOOR_PRICES = {
    'turk': 0,      # Турция - базовая цена
    'rim': 0,       # Рим - как Турция
    'aysha': 1000,  # Айша +1000₽ за дверь
    'mirror': 0     # Рамка с зеркалом - как Турция
}

# Названия дверей
DOOR_NAMES = {
    'turk': 'Турция',
    'rim': 'Рим',
    'aysha': 'Айша',
    'mirror': 'Рамка+Зеркало'
}

# Цены антресолей
ANTRESOL_PRICES = {
    2: 4000,
    3: 6000,
    4: 8000,
    5: 10000,
    6: 12000
}

# Размеры шкафов
MILAN_SIZES = {
    2: {"width": 90, "height": 220, "depth": 52},
    3: {"width": 135, "height": 220, "depth": 52},
    4: {"width": 180, "height": 220, "depth": 52},
    5: {"width": 235, "height": 220, "depth": 52},
    6: {"width": 270, "height": 220, "depth": 52}
}

# Цены ручек за штуку
HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}

# Цена ящиков
DRAWERS_PRICE = 2000

# ================= КОНЕЦ НАСТРОЕК =================


def parse_config(data: str) -> dict:
    """
    Формат: m_ДВЕРИ_ТИП1_КОЛ1_ТИП2_КОЛ2_РУЧКИ_ТРУБЫ_ЯЩИКИ_АНТРЕСОЛЬ_КОЛИЧЕСТВО
    Пример: m_6_aysha_4_mirror_2_30_2_0_0_1
    """
    parts = data.split("_")
    return {
        'doors': int(parts[1]),
        'door1_type': parts[2],
        'door1_count': int(parts[3]),
        'door2_type': parts[4],
        'door2_count': int(parts[5]),
        'handle_size': int(parts[6]),
        'tubes': int(parts[7]),
        'has_drawers': parts[8] == '1',
        'has_antresol': parts[9] == '1',
        'quantity': int(parts[10]) if len(parts) > 10 else 1
    }


def make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle, tubes, drawers, antresol, qty=1):
    """Создаём код конфигурации"""
    return f"m_{doors}_{d1_type}_{d1_count}_{d2_type}_{d2_count}_{handle}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}_{qty}"


def calculate_price(config: dict) -> dict:
    """Расчёт цены за 1 шкаф"""
    doors = config['doors']
    d1_type = config['door1_type']
    d1_count = config['door1_count']
    d2_type = config['door2_type']
    d2_count = config['door2_count']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    quantity = config.get('quantity', 1)
    
    # Базовая цена
    base_price = MILAN_BASE_PRICES[doors]
    
    # Доплата за двери (только за Айшу, остальные бесплатно)
    doors_extra = (DOOR_PRICES[d1_type] * d1_count) + (DOOR_PRICES.get(d2_type, 0) * d2_count)
    
    # 6 дверей, 1 труба
    tubes_extra = 2000 if (doors == 6 and tubes == 1) else 0
    
    # Ручки
    handle_price = HANDLE_PRICES.get(handle_size, 0) * doors
    
    # Ящики
    drawers_price = DRAWERS_PRICE if has_drawers else 0
    
    # Антресоль
    antresol_price = 0
    if has_antresol:
        antresol_doors = 4 if doors in [3, 5] else doors
        antresol_price = ANTRESOL_PRICES.get(antresol_doors, 0)
        # Айша на антресоли +500₽/дверь
        aysha_count = 0
        if d1_type == 'aysha':
            aysha_count += d1_count
        if d2_type == 'aysha':
            aysha_count += d2_count
        if aysha_count > 0:
            antresol_price += 500 * min(aysha_count, antresol_doors)
    
    price_one = base_price + doors_extra + tubes_extra + handle_price + drawers_price + antresol_price
    total = price_one * quantity
    
    return {
        'base_price': base_price,
        'doors_extra': doors_extra,
        'tubes_extra': tubes_extra,
        'handle_price': handle_price,
        'drawers_price': drawers_price,
        'antresol_price': antresol_price,
        'price_one': price_one,
        'quantity': quantity,
        'total': total
    }


def get_sizes_text(doors, has_antresol):
    """Текст с размерами"""
    size = MILAN_SIZES[doors]
    height = size["height"] + (50 if has_antresol else 0)
    return f"Ширина: {size['width']}см, Высота: {height}см, Глубина: {size['depth']}см"


def get_doors_text(d1_type, d1_count, d2_type, d2_count):
    """Текст с описанием дверей"""
    if d2_count == 0 or d2_type == 'none':
        return f"{d1_count} × {DOOR_NAMES[d1_type]}"
    else:
        return f"{d1_count} × {DOOR_NAMES[d1_type]} + {d2_count} × {DOOR_NAMES[d2_type]}"


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
        code = make_config_code(doors, 'turk', doors, 'none', 0, 30, 2, False, False, 1)
        text = f"{doors} {'двери' if doors < 5 else 'дверей'}"
        buttons.append(InlineKeyboardButton(text=text, callback_data=code))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons[0:2],
        buttons[2:4],
        [buttons[4]],
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
    d1_type = config['door1_type']
    d1_count = config['door1_count']
    d2_type = config['door2_type']
    d2_count = config['door2_count']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    quantity = config['quantity']
    
    # Текст карточки
    text = f"🛋 <b>Милан - Шкаф-купе {doors} дверей</b>\n\n"
    text += f"📐 <b>Размеры:</b>\n{get_sizes_text(doors, has_antresol)}\n\n"
    
    text += f"<b>Конфигурация:</b>\n"
    text += f"├ Двери: {get_doors_text(d1_type, d1_count, d2_type, d2_count)}"
    if prices['doors_extra'] > 0:
        text += f" (+{prices['doors_extra']:,}₽)"
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
    
    text += f"💰 <b>Цена за 1 шт: {prices['price_one']:,}₽</b>\n"
    text += f"📦 <b>Количество: {quantity} шт</b>\n"
    text += f"💵 <b>ИТОГО: {prices['total']:,}₽</b>"
    
    # === КНОПКИ ===
    buttons = []
    
    # Количество
    buttons.append([
        InlineKeyboardButton(
            text="➖",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, max(1, quantity - 1))
        ),
        InlineKeyboardButton(
            text=f"📦 {quantity} шт",
            callback_data="qty_info"
        ),
        InlineKeyboardButton(
            text="➕",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, quantity + 1)
        ),
    ])
    
    # Быстрый выбор количества
    buttons.append([
        InlineKeyboardButton(
            text="1" if quantity != 1 else "✅1",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, 1)
        ),
        InlineKeyboardButton(
            text="5" if quantity != 5 else "✅5",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, 5)
        ),
        InlineKeyboardButton(
            text="10" if quantity != 10 else "✅10",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, 10)
        ),
        InlineKeyboardButton(
            text="20" if quantity != 20 else "✅20",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol, 20)
        ),
    ])
    
    # Разделитель
    buttons.append([InlineKeyboardButton(text="── Тип дверей ──", callback_data="ignore")])
    
    # Выбор типа дверей
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if d1_type == 'turk' and d2_count == 0 else ''} Турция",
            callback_data=make_config_code(doors, 'turk', doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol, quantity)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if d1_type == 'rim' and d2_count == 0 else ''} Рим",
            callback_data=make_config_code(doors, 'rim', doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol, quantity)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if d1_type == 'aysha' and d2_count == 0 else ''} Айша",
            callback_data=make_config_code(doors, 'aysha', doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol, quantity)
        ),
    ])
    
    # Комбинации с рамкой
    if doors >= 3:
        if d2_type == 'mirror' and d2_count > 0:
            # Показываем текущую комбинацию и возможность изменить
            buttons.append([
                InlineKeyboardButton(
                    text=f"🪞 Рамки: {d2_count} шт (нажми чтобы изменить)",
                    callback_data=f"mirror_{callback.data}"
                ),
            ])
            buttons.append([
                InlineKeyboardButton(
                    text="❌ Убрать рамки",
                    callback_data=make_config_code(doors, d1_type, doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol, quantity)
                ),
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="🪞 Добавить рамки с зеркалом",
                    callback_data=f"mirror_{callback.data}"
                ),
            ])
    
    # Разделитель
    buttons.append([InlineKeyboardButton(text="── Опции ──", callback_data="ignore")])
    
    # Трубы для 6 дверей
    if doors == 6:
        buttons.append([
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 1 else ''} 1 труба (+1800₽)",
                callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, 1, has_drawers, has_antresol, quantity)
            ),
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 2 else ''} 2 трубы",
                callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, 2, has_drawers, has_antresol, quantity)
            ),
        ])
    
    # Ручки
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 30 else ''} 30см",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, 30, tubes, has_drawers, has_antresol, quantity)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 60 else ''} 60см (+)",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, 60, tubes, has_drawers, has_antresol, quantity)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if handle_size == 100 else ''} 100см (+)",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, 100, tubes, has_drawers, has_antresol, quantity)
        ),
    ])
    
    # Ящики и антресоль
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if has_drawers else '➕'} Ящики",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, not has_drawers, has_antresol, quantity)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if has_antresol else '➕'} Антресоль",
            callback_data=make_config_code(doors, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, not has_antresol, quantity)
        ),
    ])
    
    # Действия
    buttons.extend([
        [InlineKeyboardButton(text=f"🛒 В корзину ({prices['total']:,}₽)", callback_data=f"cart_{callback.data}")],
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


@router.callback_query(F.data == "qty_info")
async def qty_info(callback: CallbackQuery):
    await callback.answer("Используйте ➖ и ➕ для изменения количества", show_alert=False)


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("mirror_"))
async def milan_add_mirrors(callback: CallbackQuery):
    """Выбор количества рамок"""
    original_code = callback.data.replace("mirror_", "")
    config = parse_config(original_code)
    
    doors = config['doors']
    d1_type = config['door1_type']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_drawers = config['has_drawers']
    has_antresol = config['has_antresol']
    quantity = config['quantity']
    
    text = f"🪞 <b>Рамки с зеркалом</b>\n\n"
    text += f"Шкаф {doors} дверей\n"
    text += f"Основные двери: {DOOR_NAMES[d1_type]}\n\n"
    text += f"Выберите сколько дверей заменить на рамки:"
    
    buttons = []
    for mirror_count in range(1, doors):
        base_count = doors - mirror_count
        code = make_config_code(doors, d1_type, base_count, 'mirror', mirror_count, handle_size, tubes, has_drawers, has_antresol, quantity)
        buttons.append(
            InlineKeyboardButton(
                text=f"{base_count} {DOOR_NAMES[d1_type]} + {mirror_count} 🪞",
                callback_data=code
            )
        )
    
    keyboard_buttons = []
    for i in range(0, len(buttons), 2):
        keyboard_buttons.append(buttons[i:i+2])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=original_code)
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавление в корзину"""
    config_code = callback.data.replace("cart_", "")
    config = parse_config(config_code)
    prices = calculate_price(config)
    
    # TODO: Сохранение в БД
    
    doors_text = get_doors_text(config['door1_type'], config['door1_count'], config['door2_type'], config['door2_count'])
    
    await callback.answer(
        f"✅ Добавлено в корзину!\n"
        f"Милан {config['doors']} дв: {doors_text}\n"
        f"Кол-во: {config['quantity']} шт\n"
        f"Сумма: {prices['total']:,}₽",
        show_alert=True
    )
    
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