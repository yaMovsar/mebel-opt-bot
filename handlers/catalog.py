from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


# ================= ЦЕНЫ И РАЗМЕРЫ МИЛАН =================

# Размеры шкафов (высота, ширина, глубина)
MILAN_SIZES = {
    2: {"h": 220, "w": 90, "d": 52},
    3: {"h": 220, "w": 135, "d": 52},
    4: {"h": 220, "w": 180, "d": 52},
    5: {"h": 220, "w": 225, "d": 52},
    6: {"h": 220, "w": 270, "d": 52}
}

# Цены БЕЗ антресоли (двери, 2 трубы для 6дв)
MILAN_PRICES = {
    2: {'turk': 11000, 'rim': 11000, 'aysha': 13000},
    3: {'turk': 14000, 'rim': 14000, 'aysha': 17000},
    4: {'turk': 21000, 'rim': 21000, 'aysha': 24000},
    5: {'turk': 24000, 'rim': 24000, 'aysha': 29000},
    6: {'turk': 25000, 'rim': 25200, 'aysha': 30000}  # 2 трубы
}

# Цены С антресолью (высота +50см)
MILAN_PRICES_ANTRESOL = {
    2: {'turk': 15000, 'rim': 15000, 'aysha': 18000},
    3: {'turk': 20000, 'rim': 20000, 'aysha': 24500},
    4: {'turk': 29000, 'rim': 29000, 'aysha': 34000},
    5: {'turk': 35000, 'rim': 35000, 'aysha': 42000},
    6: {'turk': 37000, 'rim': 37000, 'aysha': 45000}  # 2 трубы
}

# Цены 6 дверей 1 ТРУБА (без антресоли)
MILAN_6_1TUBE = {'turk': 27000, 'rim': 27000, 'aysha': 32000}

# Цены 6 дверей 1 ТРУБА (с антресолью)
MILAN_6_1TUBE_ANTRESOL = {'turk': 39000, 'rim': 39000, 'aysha': 47000}

# Доплата за рамку с зеркалом (как Турция = 0)
MIRROR_EXTRA = 0

# Цены ручек за штуку
HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}

# Цена выдвижных ящиков
DRAWERS_PRICE = 2000

# Цвета
COLORS = ['Белый', 'Серый', 'Ваниль', 'Лино', 'Ватан']

# Названия дверей
DOOR_NAMES = {
    'turk': 'Турция',
    'rim': 'Рим',
    'aysha': 'Айша',
    'mirror': 'Рамка'
}

# ================= КОНЕЦ НАСТРОЕК =================


def parse_config(data: str) -> dict:
    """
    Формат: m_ДВЕРИ_ЦВЕТ_ТИП1_КОЛ1_ТИП2_КОЛ2_РУЧКИ_ТРУБЫ_ЯЩИКИ_АНТРЕСОЛЬ
    """
    parts = data.split("_")
    return {
        'doors': int(parts[1]),
        'color': parts[2],
        'door1_type': parts[3],
        'door1_count': int(parts[4]),
        'door2_type': parts[5],
        'door2_count': int(parts[6]),
        'handle_size': int(parts[7]),
        'tubes': int(parts[8]),
        'has_drawers': parts[9] == '1',
        'has_antresol': parts[10] == '1'
    }


def make_code(doors, color, d1_type, d1_count, d2_type, d2_count, handle, tubes, drawers, antresol):
    """Создаём код конфигурации"""
    return f"m_{doors}_{color}_{d1_type}_{d1_count}_{d2_type}_{d2_count}_{handle}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}"


def get_base_price(doors, door_type, tubes, has_antresol):
    """Получить базовую цену из таблицы"""
    if doors == 6 and tubes == 1:
        if has_antresol:
            return MILAN_6_1TUBE_ANTRESOL.get(door_type, MILAN_6_1TUBE_ANTRESOL['turk'])
        else:
            return MILAN_6_1TUBE.get(door_type, MILAN_6_1TUBE['turk'])
    else:
        if has_antresol:
            return MILAN_PRICES_ANTRESOL[doors].get(door_type, MILAN_PRICES_ANTRESOL[doors]['turk'])
        else:
            return MILAN_PRICES[doors].get(door_type, MILAN_PRICES[doors]['turk'])


def calculate_price(config: dict) -> dict:
    """Расчёт цены"""
    doors = config['doors']
    d1_type = config['door1_type']
    d1_count = config['door1_count']
    d2_type = config['door2_type']
    d2_count = config['door2_count']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    
    # Базовая цена по основному типу дверей
    base_price = get_base_price(doors, d1_type, tubes, has_antresol)
    
    # Если есть рамки - они как Турция, доплаты нет
    # Но если основные двери Айша, а часть рамки - нужен пересчёт
    if d2_type == 'mirror' and d2_count > 0:
        # Считаем как: цена Турции + доплата за Айшу только за Айша-двери
        turk_price = get_base_price(doors, 'turk', tubes, has_antresol)
        if d1_type == 'aysha':
            # Доплата за Айшу = разница между Айша и Турция на всё, делим на двери, умножаем на кол-во Айша
            aysha_full = get_base_price(doors, 'aysha', tubes, has_antresol)
            extra_per_door = (aysha_full - turk_price) / doors
            base_price = turk_price + (extra_per_door * d1_count)
        else:
            base_price = turk_price
    
    # Ручки
    handle_price = HANDLE_PRICES.get(handle_size, 0) * doors
    
    # Ящики
    drawers_price = DRAWERS_PRICE if has_drawers else 0
    
    total = int(base_price + handle_price + drawers_price)
    
    return {
        'base_price': int(base_price),
        'handle_price': handle_price,
        'drawers_price': drawers_price,
        'total': total
    }


def get_sizes_text(doors, has_antresol):
    """Текст с размерами"""
    size = MILAN_SIZES[doors]
    height = size["h"] + (50 if has_antresol else 0)
    return f"Ширина: {size['w']}см, Высота: {height}см, Глубина: {size['d']}см"


def get_doors_text(d1_type, d1_count, d2_type, d2_count):
    """Текст с описанием дверей"""
    total = d1_count + d2_count
    if d2_count == 0 or d2_type == 'none':
        return f"{total} × {DOOR_NAMES[d1_type]}"
    else:
        return f"{d1_count} × {DOOR_NAMES[d1_type]} + {d2_count} × {DOOR_NAMES[d2_type]}"


def get_color_name(code):
    """Получить название цвета"""
    colors_map = {'wh': 'Белый', 'gr': 'Серый', 'va': 'Ваниль', 'li': 'Лино', 'vt': 'Ватан'}
    return colors_map.get(code, 'Белый')


def get_color_code(name):
    """Получить код цвета"""
    colors_map = {'Белый': 'wh', 'Серый': 'gr', 'Ваниль': 'va', 'Лино': 'li', 'Ватан': 'vt'}
    return colors_map.get(name, 'wh')


# ================= ОБРАБОТЧИКИ =================

@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Главное меню каталога"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Милан (распашной)", callback_data="cat_milan")],
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
        # Стартовая конфигурация
        tubes = 2 if doors == 6 else 0
        code = make_code(doors, 'wh', 'turk', doors, 'none', 0, 30, tubes, False, False)
        text = f"{doors} дв"
        buttons.append(InlineKeyboardButton(text=text, callback_data=code))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")],
    ])
    
    await callback.message.edit_text(
        "🚪 <b>Шкаф МИЛАН (распашной)</b>\n\n"
        "Выберите количество дверей:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("m_"))
async def milan_show(callback: CallbackQuery):
    """Показываем карточку товара"""
    config = parse_config(callback.data)
    prices = calculate_price(config)
    
    doors = config['doors']
    color = config['color']
    d1_type = config['door1_type']
    d1_count = config['door1_count']
    d2_type = config['door2_type']
    d2_count = config['door2_count']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_antresol = config['has_antresol']
    has_drawers = config['has_drawers']
    
        # === ТЕКСТ КАРТОЧКИ ===
    text = f"🚪 <b>Шкаф МИЛАН {doors} дверей</b>\n\n"
    
    text += f"📐 <b>Размеры:</b>\n{get_sizes_text(doors, has_antresol)}\n\n"
    
    text += f"<b>Комплектация:</b>\n"
    text += f"├ Цвет: {get_color_name(color)}\n"
    text += f"├ Двери: {get_doors_text(d1_type, d1_count, d2_type, d2_count)}\n"
    
    if doors == 6:
        text += f"├ Трубы: {tubes} шт\n"
    
    if prices['handle_price'] > 0:
        text += f"├ Ручки: {handle_size}см (+{prices['handle_price']:,}₽)\n"
    else:
        text += f"├ Ручки: {handle_size}см\n"
    
    if has_drawers:
        text += f"├ Доп.Ящики: Да (+{prices['drawers_price']:,}₽)\n"
    else:
        text += f"├ Доп.Ящики: Нет\n"
    
    if has_antresol:
        text += f"└ Антресоль: Да (+50см)\n\n"
    else:
        text += f"└ Антресоль: Нет\n\n"
    
    text += f"💰 <b>ЦЕНА: {prices['total']:,}₽</b>"
    
    # === КНОПКИ ===
    buttons = []
    
    # Цвета
    color_buttons = []
    for c in ['wh', 'gr', 'va', 'li', 'vt']:
        name = get_color_name(c)
        is_selected = (c == color)
        color_buttons.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_selected else ''}{name}",
                callback_data=make_code(doors, c, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, has_antresol)
            )
        )
    buttons.append(color_buttons[:3])
    buttons.append(color_buttons[3:])
    
    # Разделитель
    buttons.append([InlineKeyboardButton(text="── Двери ──", callback_data="ignore")])
    
    # Двери (основной тип - все двери одного типа)
    door_buttons = []
    for dt in ['turk', 'rim', 'aysha']:
        is_selected = (d1_type == dt and d2_count == 0)
        door_buttons.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_selected else ''}{DOOR_NAMES[dt]}",
                callback_data=make_code(doors, color, dt, doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol)
            )
        )
    buttons.append(door_buttons)
    
    # Рамки
    if doors >= 2:
        if d2_type == 'mirror' and d2_count > 0:
            buttons.append([
                InlineKeyboardButton(
                    text=f"🪞 Рамки: {d2_count} шт (изменить)",
                    callback_data=f"mir_{callback.data}"
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=make_code(doors, color, d1_type, doors, 'none', 0, handle_size, tubes, has_drawers, has_antresol)
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="🪞 + Рамки с зеркалом",
                    callback_data=f"mir_{callback.data}"
                )
            ])
    
    # Разделитель
    buttons.append([InlineKeyboardButton(text="── Опции ──", callback_data="ignore")])
    
    # Трубы (только для 6 дверей)
    if doors == 6:
        buttons.append([
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 1 else ''} 1 труба",
                callback_data=make_code(doors, color, d1_type, d1_count, d2_type, d2_count, handle_size, 1, has_drawers, has_antresol)
            ),
            InlineKeyboardButton(
                text=f"{'✅' if tubes == 2 else ''} 2 трубы",
                callback_data=make_code(doors, color, d1_type, d1_count, d2_type, d2_count, handle_size, 2, has_drawers, has_antresol)
            )
        ])
    
    # Ручки
    handle_buttons = []
    for h in [30, 60, 100]:
        is_selected = (handle_size == h)
        extra = HANDLE_PRICES[h] * doors
        label = f"{h}см"
        if extra > 0:
            label += f" +{extra}₽"
        handle_buttons.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_selected else ''}{label}",
                callback_data=make_code(doors, color, d1_type, d1_count, d2_type, d2_count, h, tubes, has_drawers, has_antresol)
            )
        )
    buttons.append(handle_buttons)
    
    # Доп опции
    buttons.append([
        InlineKeyboardButton(
            text=f"{'✅' if has_antresol else '➕'} Антресоль",
            callback_data=make_code(doors, color, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, has_drawers, not has_antresol)
        ),
        InlineKeyboardButton(
            text=f"{'✅' if has_drawers else '➕'} Ящики +{DRAWERS_PRICE}₽",
            callback_data=make_code(doors, color, d1_type, d1_count, d2_type, d2_count, handle_size, tubes, not has_drawers, has_antresol)
        )
    ])
    
    # В корзину
    buttons.append([
        InlineKeyboardButton(
            text=f"🛒 В корзину ({prices['total']:,}₽)",
            callback_data=f"cart_{callback.data}"
        )
    ])
    
    # Навигация
    buttons.append([
        InlineKeyboardButton(text="🔄 Другой размер", callback_data="cat_milan"),
        InlineKeyboardButton(text="◀️ Каталог", callback_data="back_to_catalog")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        pass
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("mir_"))
async def milan_mirrors(callback: CallbackQuery):
    """Выбор рамок"""
    original = callback.data.replace("mir_", "")
    config = parse_config(original)
    
    doors = config['doors']
    color = config['color']
    d1_type = config['door1_type']
    handle_size = config['handle_size']
    tubes = config['tubes']
    has_drawers = config['has_drawers']
    has_antresol = config['has_antresol']
    
    text = f"🪞 <b>Рамки с зеркалом</b>\n\n"
    text += f"Шкаф {doors} дверей, основа: {DOOR_NAMES[d1_type]}\n\n"
    text += "Сколько дверей заменить на рамки?"
    
    buttons = []
    row = []
    for i in range(1, doors):
        base = doors - i
        code = make_code(doors, color, d1_type, base, 'mirror', i, handle_size, tubes, has_drawers, has_antresol)
        row.append(InlineKeyboardButton(text=f"{base}+{i}🪞", callback_data=code))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=original)])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Выбор количества и добавление в корзину"""
    config_code = callback.data.replace("cart_", "")
    
    # Показываем выбор количества
    text = "📦 <b>Укажите количество:</b>"
    
    buttons = []
    for qty in [1, 2, 3, 5, 10, 15, 20]:
        buttons.append(
            InlineKeyboardButton(text=str(qty), callback_data=f"addq_{qty}_{config_code}")
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:4],
        buttons[4:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=config_code)]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("addq_"))
async def confirm_add(callback: CallbackQuery):
    """Подтверждение добавления"""
    parts = callback.data.split("_", 2)
    qty = int(parts[1])
    config_code = parts[2]
    
    config = parse_config(config_code)
    prices = calculate_price(config)
    total = prices['total'] * qty
    
    doors_text = get_doors_text(config['door1_type'], config['door1_count'], config['door2_type'], config['door2_count'])
    
    # TODO: Сохранение в БД
    
    await callback.answer(
        f"✅ Добавлено в корзину!\n\n"
        f"Милан {config['doors']}дв, {get_color_name(config['color'])}\n"
        f"Двери: {doors_text}\n"
        f"Кол-во: {qty} шт\n"
        f"Сумма: {total:,}₽",
        show_alert=True
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="go_to_cart")],
        [InlineKeyboardButton(text="🚪 Добавить ещё", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ В каталог", callback_data="back_to_catalog")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Милан (распашной)", callback_data="cat_milan")],
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
    await callback.answer("🛒 Корзина в разработке", show_alert=True)