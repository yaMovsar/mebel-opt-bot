from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

router = Router()


# ================= НАСТРОЙКИ =================

# Фото шкафов (без антресоли / с антресолью)
PHOTOS = {
    2: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    3: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    4: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    5: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    6: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
}

# Размеры
SIZES = {
    2: {"h": 220, "w": 90, "d": 52},
    3: {"h": 220, "w": 135, "d": 52},
    4: {"h": 220, "w": 180, "d": 52},
    5: {"h": 220, "w": 225, "d": 52},
    6: {"h": 220, "w": 270, "d": 52}
}

# Цены БЕЗ антресоли
PRICES = {
    2: {'turk': 11000, 'rim': 11000, 'aysha': 13000},
    3: {'turk': 14000, 'rim': 14000, 'aysha': 17000},
    4: {'turk': 21000, 'rim': 21000, 'aysha': 24000},
    5: {'turk': 24000, 'rim': 24000, 'aysha': 29000},
    6: {'turk': 25000, 'rim': 25200, 'aysha': 30000}
}

# Цены С антресолью
PRICES_ANT = {
    2: {'turk': 15000, 'rim': 15000, 'aysha': 18000},
    3: {'turk': 20000, 'rim': 20000, 'aysha': 24500},
    4: {'turk': 29000, 'rim': 29000, 'aysha': 34000},
    5: {'turk': 35000, 'rim': 35000, 'aysha': 42000},
    6: {'turk': 37000, 'rim': 37000, 'aysha': 45000}
}

# 6 дверей 1 труба
PRICES_6_1T = {'turk': 27000, 'rim': 27000, 'aysha': 32000}
PRICES_6_1T_ANT = {'turk': 39000, 'rim': 39000, 'aysha': 47000}

# Ручки: цена за штуку (одинаковая для всех типов и цветов)
HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}
HANDLE_TYPES = {'skoba': 'Скоба', 'flat': 'Плоская', 'crown': 'Корона'}
HANDLE_COLORS = {'black': 'Чёрная', 'grey': 'Серая', 'gold': 'Золото'}

DRAWERS_PRICE = 2000

COLORS = {'wh': 'Белый', 'gr': 'Серый', 'va': 'Ваниль', 'li': 'Лино', 'vt': 'Ватан'}
DOORS = {'turk': 'Турция', 'rim': 'Рим', 'aysha': 'Айша', 'mirror': 'Рамка'}

# ================= ФУНКЦИИ =================

def parse(data):
    """m_двери_цвет_дверь_рамки_ручкиРазмер_ручкиТип_ручкиЦвет_трубы_ящики_антр"""
    p = data.split("_")
    return {
        'doors': int(p[1]),
        'color': p[2],
        'door_type': p[3],
        'mirrors': int(p[4]),
        'handle_size': int(p[5]),
        'handle_type': p[6],
        'handle_color': p[7],
        'tubes': int(p[8]),
        'drawers': p[9] == '1',
        'antresol': p[10] == '1'
    }

def code(doors, color, door, mirrors, h_size, h_type, h_color, tubes, drawers, antresol):
    return f"m_{doors}_{color}_{door}_{mirrors}_{h_size}_{h_type}_{h_color}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}"

def calc_price(c):
    """Расчёт цены"""
    doors = c['doors']
    door_type = c['door_type']
    mirrors = c['mirrors']
    h_size = c['handle_size']
    tubes = c['tubes']
    drawers = c['drawers']
    antresol = c['antresol']
    
    # Базовая цена
    if doors == 6 and tubes == 1:
        base = PRICES_6_1T_ANT.get(door_type, PRICES_6_1T_ANT['turk']) if antresol else PRICES_6_1T.get(door_type, PRICES_6_1T['turk'])
    else:
        base = PRICES_ANT[doors].get(door_type, PRICES_ANT[doors]['turk']) if antresol else PRICES[doors].get(door_type, PRICES[doors]['turk'])
    
    # Рамки: если Айша + рамки, пересчитываем
    # Рамки только на шкафу (не на антресоли), стоят как Турция
    if mirrors > 0 and door_type == 'aysha':
        # Цена Турции
        if doors == 6 and tubes == 1:
            turk_base = PRICES_6_1T_ANT['turk'] if antresol else PRICES_6_1T['turk']
            aysha_base = PRICES_6_1T_ANT['aysha'] if antresol else PRICES_6_1T['aysha']
        else:
            turk_base = PRICES_ANT[doors]['turk'] if antresol else PRICES[doors]['turk']
            aysha_base = PRICES_ANT[doors]['aysha'] if antresol else PRICES[doors]['aysha']
        
        # Разница за 1 дверь Айша
        diff_per_door = (aysha_base - turk_base) / doors
        
        # Платим только за (doors - mirrors) дверей Айша
        base = turk_base + diff_per_door * (doors - mirrors)
    
    # Ручки (цена одинаковая для всех типов и цветов)
    handle_extra = HANDLE_PRICES[h_size] * doors
    
    # Ящики
    drawer_extra = DRAWERS_PRICE if drawers else 0
    
    return int(base + handle_extra + drawer_extra)

def get_photo(c):
    """Получить URL фото"""
    key = "ant" if c['antresol'] else "normal"
    return PHOTOS[c['doors']][key]

def get_text(c, price):
    """Текст карточки"""
    doors = c['doors']
    s = SIZES[doors]
    h = s['h'] + (50 if c['antresol'] else 0)
    
    # Текст дверей
    if c['mirrors'] > 0:
        door_text = f"{doors - c['mirrors']}× {DOORS[c['door_type']]} + {c['mirrors']}× Рамка"
    else:
        door_text = f"{doors}× {DOORS[c['door_type']]}"
    
    # Текст ручек
    handle_text = f"{c['handle_size']}см {HANDLE_TYPES[c['handle_type']]} {HANDLE_COLORS[c['handle_color']]}"
    handle_extra = HANDLE_PRICES[c['handle_size']] * doors
    
    text = f"🚪 <b>Шкаф МИЛАН {doors} дверей</b>\n\n"
    text += f"📐 Размеры: {s['w']}×{h}×{s['d']} см\n\n"
    text += f"<b>Ваш выбор:</b>\n"
    text += f"├ Цвет: {COLORS[c['color']]}\n"
    text += f"├ Двери: {door_text}\n"
    if doors == 6:
        text += f"├ Трубы: {c['tubes']} шт\n"
    text += f"├ Ручки: {handle_text}"
    if handle_extra > 0:
        text += f" (+{handle_extra:,}₽)"
    text += "\n"
    text += f"├ Ящики: {'Да (+2,000₽)' if c['drawers'] else 'Нет'}\n"
    text += f"└ Антресоль: {'Да (+50см)' if c['antresol'] else 'Нет'}\n\n"
    text += f"💰 <b>Цена: {price:,} ₽</b>"
    
    return text


# ================= ОБРАБОТЧИКИ =================

@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Милан", callback_data="cat_milan")],
        [InlineKeyboardButton(text="✨ Элегант (скоро)", callback_data="soon")],
        [InlineKeyboardButton(text="💎 Премиум (скоро)", callback_data="soon")],
    ])
    await message.answer("📋 <b>Каталог мебели</b>\n\nВыберите:", reply_markup=kb)


@router.callback_query(F.data == "soon")
async def soon(cb: CallbackQuery):
    await cb.answer("🚧 В разработке", show_alert=True)


@router.callback_query(F.data == "cat_milan")
async def milan_start(cb: CallbackQuery):
    """Выбор размера"""
    buttons = []
    for d in [2, 3, 4, 5, 6]:
        buttons.append(
            InlineKeyboardButton(
                text=f"{d} дв",
                callback_data=code(d, 'wh', 'turk', 0, 30, 'skoba', 'black', 2, False, False)
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_cat")]
    ])
    
    try:
        await cb.message.edit_text(
            "🚪 <b>Шкаф МИЛАН</b>\n\nВыберите количество дверей:",
            reply_markup=kb
        )
    except:
        await cb.message.delete()
        await cb.message.answer(
            "🚪 <b>Шкаф МИЛАН</b>\n\nВыберите количество дверей:",
            reply_markup=kb
        )
    await cb.answer()


@router.callback_query(F.data.startswith("m_"))
async def milan_show(cb: CallbackQuery):
    """Карточка товара"""
    c = parse(cb.data)
    price = calc_price(c)
    text = get_text(c, price)
    photo = get_photo(c)
    
    # Основные кнопки
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎨 Цвет", callback_data=f"clr_{cb.data}"),
            InlineKeyboardButton(text="🚪 Двери", callback_data=f"dr_{cb.data}"),
            InlineKeyboardButton(text="🪞 Рамки", callback_data=f"mir_{cb.data}"),
        ],
        [
            InlineKeyboardButton(text="✋ Ручки", callback_data=f"hnd_{cb.data}"),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if c['antresol'] else '➕'} Антресоль",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], c['drawers'], not c['antresol'])
            ),
            InlineKeyboardButton(
                text=f"{'✅' if c['drawers'] else '➕'} Ящики",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], not c['drawers'], c['antresol'])
            ),
        ],
        # Трубы для 6 дверей
        *([
            [
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==1 else '⚪'} 1 труба",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handle_size'], c['handle_type'], c['handle_color'], 1, c['drawers'], c['antresol'])
                ),
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==2 else '⚪'} 2 трубы",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handle_size'], c['handle_type'], c['handle_color'], 2, c['drawers'], c['antresol'])
                ),
            ]
        ] if c['doors'] == 6 else []),
        [InlineKeyboardButton(text=f"🛒 В корзину • {price:,} ₽", callback_data=f"cart_{cb.data}")],
        [
            InlineKeyboardButton(text="🔄 Другой шкаф", callback_data="cat_milan"),
            InlineKeyboardButton(text="◀️ Каталог", callback_data="back_cat")
        ]
    ])
    
    try:
        await cb.message.edit_media(
            media=InputMediaPhoto(media=photo, caption=text, parse_mode="HTML"),
            reply_markup=kb
        )
    except:
        try:
            await cb.message.delete()
        except:
            pass
        await cb.message.answer_photo(photo=photo, caption=text, reply_markup=kb)
    
    await cb.answer()


# ===== ЦВЕТ =====
@router.callback_query(F.data.startswith("clr_"))
async def opt_color(cb: CallbackQuery):
    orig = cb.data.replace("clr_", "")
    c = parse(orig)
    
    buttons = []
    for col_code, col_name in COLORS.items():
        is_sel = col_code == c['color']
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{col_name}",
                callback_data=code(c['doors'], col_code, c['door_type'], c['mirrors'], c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="🎨 <b>Выберите цвет шкафа:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== ДВЕРИ =====
@router.callback_query(F.data.startswith("dr_"))
async def opt_door(cb: CallbackQuery):
    orig = cb.data.replace("dr_", "")
    c = parse(orig)
    
    buttons = []
    for d_code in ['turk', 'rim', 'aysha']:
        is_sel = d_code == c['door_type'] and c['mirrors'] == 0
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{DOORS[d_code]}",
                callback_data=code(c['doors'], c['color'], d_code, 0, c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="🚪 <b>Выберите тип дверей:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РАМКИ =====
@router.callback_query(F.data.startswith("mir_"))
async def opt_mirror(cb: CallbackQuery):
    orig = cb.data.replace("mir_", "")
    c = parse(orig)
    
    buttons = [
        InlineKeyboardButton(
            text=f"{'✅ ' if c['mirrors']==0 else ''}Без рамок",
            callback_data=code(c['doors'], c['color'], c['door_type'], 0, c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], c['drawers'], c['antresol'])
        )
    ]
    
    for m in range(1, c['doors']):
        is_sel = m == c['mirrors']
        label = f"{c['doors']-m} {DOORS[c['door_type']]} + {m} Рамка"
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{label}",
                callback_data=code(c['doors'], c['color'], c['door_type'], m, c['handle_size'], c['handle_type'], c['handle_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    rows = [[b] for b in buttons]
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=orig)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    
    await cb.message.edit_caption(caption="🪞 <b>Рамки с зеркалом (только на шкафу):</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РУЧКИ - РАЗМЕР =====
@router.callback_query(F.data.startswith("hnd_"))
async def opt_handle_size(cb: CallbackQuery):
    orig = cb.data.replace("hnd_", "")
    c = parse(orig)
    
    buttons = []
    for size in [30, 60, 100]:
        is_sel = size == c['handle_size']
        extra = HANDLE_PRICES[size] * c['doors']
        label = f"{size}см"
        if extra > 0:
            label += f" (+{extra:,}₽)"
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{label}",
                callback_data=f"htype_{size}_{orig}"
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="✋ <b>Выберите размер ручек:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РУЧКИ - ТИП =====
@router.callback_query(F.data.startswith("htype_"))
async def opt_handle_type(cb: CallbackQuery):
    parts = cb.data.split("_", 2)
    size = int(parts[1])
    orig = parts[2]
    c = parse(orig)
    
    buttons = []
    for t_code, t_name in HANDLE_TYPES.items():
        is_sel = t_code == c['handle_type'] and size == c['handle_size']
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{t_name}",
                callback_data=f"hcolor_{size}_{t_code}_{orig}"
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"hnd_{orig}")]
    ])
    
    await cb.message.edit_caption(caption=f"✋ <b>Ручки {size}см — выберите тип:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РУЧКИ - ЦВЕТ =====
@router.callback_query(F.data.startswith("hcolor_"))
async def opt_handle_color(cb: CallbackQuery):
    parts = cb.data.split("_", 3)
    size = int(parts[1])
    h_type = parts[2]
    orig = parts[3]
    c = parse(orig)
    
    buttons = []
    for col_code, col_name in HANDLE_COLORS.items():
        is_sel = col_code == c['handle_color'] and h_type == c['handle_type'] and size == c['handle_size']
        new_code = code(c['doors'], c['color'], c['door_type'], c['mirrors'], size, h_type, col_code, c['tubes'], c['drawers'], c['antresol'])
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{col_name}",
                callback_data=new_code
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"htype_{size}_{orig}")]
    ])
    
    await cb.message.edit_caption(
        caption=f"✋ <b>Ручки {size}см {HANDLE_TYPES[h_type]} — выберите цвет:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


# ===== КОРЗИНА =====
@router.callback_query(F.data.startswith("cart_"))
async def cart_qty(cb: CallbackQuery):
    orig = cb.data.replace("cart_", "")
    
    buttons = []
    for qty in [1, 2, 3, 5, 10, 20]:
        buttons.append(InlineKeyboardButton(text=str(qty), callback_data=f"addq_{qty}_{orig}"))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="📦 <b>Укажите количество:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("addq_"))
async def add_to_cart(cb: CallbackQuery):
    parts = cb.data.split("_", 2)
    qty = int(parts[1])
    c = parse(parts[2])
    price = calc_price(c)
    total = price * qty
    
    if c['mirrors'] > 0:
        door_text = f"{c['doors']-c['mirrors']}× {DOORS[c['door_type']]} + {c['mirrors']}× Рамка"
    else:
        door_text = f"{c['doors']}× {DOORS[c['door_type']]}"
    
    handle_text = f"{c['handle_size']}см {HANDLE_TYPES[c['handle_type']]} {HANDLE_COLORS[c['handle_color']]}"
    
    await cb.answer(
        f"✅ Добавлено в корзину!\n\n"
        f"Милан {c['doors']}дв • {COLORS[c['color']]}\n"
        f"Двери: {door_text}\n"
        f"Ручки: {handle_text}\n"
        f"Кол-во: {qty} шт\n"
        f"Сумма: {total:,} ₽",
        show_alert=True
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="go_cart")],
        [InlineKeyboardButton(text="➕ Добавить ещё", callback_data="cat_milan")],
        [InlineKeyboardButton(text="◀️ Каталог", callback_data="back_cat")]
    ])
    
    await cb.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data == "back_cat")
async def back_cat(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Милан", callback_data="cat_milan")],
        [InlineKeyboardButton(text="✨ Элегант (скоро)", callback_data="soon")],
        [InlineKeyboardButton(text="💎 Премиум (скоро)", callback_data="soon")],
    ])
    
    try:
        await cb.message.delete()
    except:
        pass
    await cb.message.answer("📋 <b>Каталог мебели</b>\n\nВыберите:", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "go_cart")
async def go_cart(cb: CallbackQuery):
    await cb.answer("🛒 Корзина в разработке", show_alert=True)