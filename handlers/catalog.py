from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

router = Router()


# ================= НАСТРОЙКИ =================

PHOTOS = {
    2: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    3: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    4: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    5: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
    6: {"normal": "https://i.imgur.com/JqYQ5Zy.jpg", "ant": "https://i.imgur.com/JqYQ5Zy.jpg"},
}

SIZES = {
    2: {"h": 220, "w": 90, "d": 52},
    3: {"h": 220, "w": 135, "d": 52},
    4: {"h": 220, "w": 180, "d": 52},
    5: {"h": 220, "w": 225, "d": 52},
    6: {"h": 220, "w": 270, "d": 52}
}

# Базовые цены (Турция/Рим)
BASE_PRICES = {2: 11000, 3: 14000, 4: 21000, 5: 24000, 6: 25000}
BASE_PRICES_ANT = {2: 15000, 3: 20000, 4: 29000, 5: 35000, 6: 37000}
PRICES_6_1T = 27000
PRICES_6_1T_ANT = 39000

# Айша: -1000 + (кол-во × 1000)
AYSHA_BASE = -1000
AYSHA_PER_DOOR = 1000

HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}
HANDLE_TYPES = ['Скоба', 'Плоская', 'Корона']
HANDLE_COLORS = ['Чёрная', 'Серая', 'Золото']

DRAWERS_PRICE = 2000

COLORS = {'wh': 'Белый', 'gr': 'Серый', 'va': 'Ваниль', 'li': 'Лино', 'vt': 'Ватан'}
DOORS = {'turk': 'Турция', 'rim': 'Рим', 'aysha': 'Айша'}


def parse(data):
    """m_двери_цвет_дверь_рамки_размерР_типР_цветР_трубы_ящики_антр"""
    p = data.split("_")
    return {
        'doors': int(p[1]),
        'color': p[2],
        'door_type': p[3],      # turk/rim/aysha
        'mirrors': int(p[4]),    # кол-во рамок
        'h_size': int(p[5]),
        'h_type': int(p[6]),
        'h_color': int(p[7]),
        'tubes': int(p[8]),
        'drawers': p[9] == '1',
        'antresol': p[10] == '1'
    }


def code(doors, color, door, mirrors, h_size, h_type, h_color, tubes, drawers, antresol):
    return f"m_{doors}_{color}_{door}_{mirrors}_{h_size}_{h_type}_{h_color}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}"


def calc_price(c):
    doors = c['doors']
    door_type = c['door_type']
    mirrors = c['mirrors']
    h_size = c['h_size']
    tubes = c['tubes']
    drawers = c['drawers']
    antresol = c['antresol']
    
    # Базовая цена (Турция/Рим)
    if doors == 6 and tubes == 1:
        base = PRICES_6_1T_ANT if antresol else PRICES_6_1T
    else:
        base = BASE_PRICES_ANT[doors] if antresol else BASE_PRICES[doors]
    
    # Доплата за Айшу: -1000 + (кол-во Айша × 1000)
    # Кол-во Айша = doors - mirrors (если тип Айша)
    aysha_extra = 0
    if door_type == 'aysha':
        aysha_doors = doors - mirrors  # сколько дверей Айша
        aysha_extra = AYSHA_BASE + (aysha_doors * AYSHA_PER_DOOR)
    
    # Ручки
    handle_extra = HANDLE_PRICES[h_size] * doors
    
    # Ящики
    drawer_extra = DRAWERS_PRICE if drawers else 0
    
    return int(base + aysha_extra + handle_extra + drawer_extra)


def get_photo(c):
    return PHOTOS[c['doors']]["ant" if c['antresol'] else "normal"]


def get_text(c, price):
    doors = c['doors']
    s = SIZES[doors]
    h = s['h'] + (50 if c['antresol'] else 0)
    mirrors = c['mirrors']
    door_type = c['door_type']
    
    # Текст дверей
    if mirrors > 0:
        main_doors = doors - mirrors
        door_text = f"{main_doors}× {DOORS[door_type]} + {mirrors}× Рамка"
    else:
        door_text = f"{doors}× {DOORS[door_type]}"
    
    # Доплата за Айшу
    if door_type == 'aysha':
        aysha_doors = doors - mirrors
        aysha_extra = AYSHA_BASE + (aysha_doors * AYSHA_PER_DOOR)
        if aysha_extra > 0:
            door_text += f" (+{aysha_extra:,}₽)"
        elif aysha_extra < 0:
            door_text += f" ({aysha_extra:,}₽)"
    
    # Ручки
    handle_text = f"{c['h_size']}см {HANDLE_TYPES[c['h_type']]} {HANDLE_COLORS[c['h_color']]}"
    handle_extra = HANDLE_PRICES[c['h_size']] * doors
    
    text = f"🚪 <b>Шкаф МИЛАН {doors} дверей</b>\n\n"
    text += f"📐 Размеры: {s['w']}×{h}×{s['d']} см\n\n"
    text += f"<b>Комплектация:</b>\n"
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
    buttons = []
    for d in [2, 3, 4, 5, 6]:
        buttons.append(
            InlineKeyboardButton(text=f"{d} дв", callback_data=code(d, 'wh', 'turk', 0, 30, 0, 0, 2, False, False))
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_cat")]
    ])
    
    try:
        await cb.message.delete()
    except:
        pass
    await cb.message.answer("🚪 <b>Шкаф МИЛАН</b>\n\nВыберите количество дверей:", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("m_"))
async def milan_show(cb: CallbackQuery):
    c = parse(cb.data)
    price = calc_price(c)
    text = get_text(c, price)
    photo = get_photo(c)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎨 Цвет", callback_data=f"clr_{cb.data}"),
            InlineKeyboardButton(text="🚪 Двери", callback_data=f"dr_{cb.data}"),
        ],
        [
            InlineKeyboardButton(text="✋ Ручки", callback_data=f"hnd_{cb.data}"),
            InlineKeyboardButton(text="🪞 Рамки", callback_data=f"mir_{cb.data}"),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if c['antresol'] else '➕'} Антресоль",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], c['h_type'], c['h_color'], c['tubes'], c['drawers'], not c['antresol'])
            ),
            InlineKeyboardButton(
                text=f"{'✅' if c['drawers'] else '➕'} Ящики",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], c['h_type'], c['h_color'], c['tubes'], not c['drawers'], c['antresol'])
            ),
        ],
        *([
            [
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==1 else '⚪'} 1 труба",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], c['h_type'], c['h_color'], 1, c['drawers'], c['antresol'])
                ),
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==2 else '⚪'} 2 трубы",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], c['h_type'], c['h_color'], 2, c['drawers'], c['antresol'])
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
    
    rows = []
    row = []
    for col_code, col_name in COLORS.items():
        is_sel = col_code == c['color']
        row.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{col_name}",
                callback_data=code(c['doors'], col_code, c['door_type'], c['mirrors'], c['h_size'], c['h_type'], c['h_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=orig)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.edit_caption(caption="🎨 <b>Выберите цвет:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== ДВЕРИ =====
@router.callback_query(F.data.startswith("dr_"))
async def opt_door(cb: CallbackQuery):
    orig = cb.data.replace("dr_", "")
    c = parse(orig)
    
    buttons = []
    for d_code, d_name in DOORS.items():
        is_sel = d_code == c['door_type'] and c['mirrors'] == 0
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{d_name}",
                callback_data=code(c['doors'], c['color'], d_code, 0, c['h_size'], c['h_type'], c['h_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="🚪 <b>Выберите тип дверей:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РАМКИ (доступны с любым типом дверей) =====
@router.callback_query(F.data.startswith("mir_"))
async def opt_mirror(cb: CallbackQuery):
    orig = cb.data.replace("mir_", "")
    c = parse(orig)
    
    buttons = []
    for m in range(0, c['doors']):
        is_sel = m == c['mirrors']
        main_doors = c['doors'] - m
        
        if m == 0:
            label = f"Без рамок ({c['doors']} {DOORS[c['door_type']]})"
        else:
            label = f"{main_doors} {DOORS[c['door_type']]} + {m} Рамка"
        
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{label}",
                callback_data=code(c['doors'], c['color'], c['door_type'], m, c['h_size'], c['h_type'], c['h_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    rows = [[b] for b in buttons]
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=orig)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.edit_caption(caption="🪞 <b>Сколько рамок с зеркалом?</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ===== РУЧКИ =====
@router.callback_query(F.data.startswith("hnd_"))
async def opt_handle(cb: CallbackQuery):
    orig = cb.data.replace("hnd_", "")
    c = parse(orig)
    
    size_row = []
    for size in [30, 60, 100]:
        is_sel = size == c['h_size']
        extra = HANDLE_PRICES[size] * c['doors']
        label = f"{size}см"
        if extra > 0:
            label += f"(+{extra//1000}к)"
        size_row.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{label}",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], size, c['h_type'], c['h_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    type_row = []
    for i, t_name in enumerate(HANDLE_TYPES):
        is_sel = i == c['h_type']
        type_row.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{t_name}",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], i, c['h_color'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    color_row = []
    for i, col_name in enumerate(HANDLE_COLORS):
        is_sel = i == c['h_color']
        color_row.append(
            InlineKeyboardButton(
                text=f"{'✅' if is_sel else ''}{col_name}",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['h_size'], c['h_type'], i, c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📏 Размер:", callback_data="ignore")],
        size_row,
        [InlineKeyboardButton(text="✋ Тип:", callback_data="ignore")],
        type_row,
        [InlineKeyboardButton(text="🎨 Цвет:", callback_data="ignore")],
        color_row,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(caption="✋ <b>Настройте ручки:</b>", reply_markup=kb, parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "ignore")
async def ignore(cb: CallbackQuery):
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
    
    mirrors = c['mirrors']
    if mirrors > 0:
        main_doors = c['doors'] - mirrors
        door_text = f"{main_doors}× {DOORS[c['door_type']]} + {mirrors}× Рамка"
    else:
        door_text = f"{c['doors']}× {DOORS[c['door_type']]}"
    
    handle_text = f"{c['h_size']}см {HANDLE_TYPES[c['h_type']]} {HANDLE_COLORS[c['h_color']]}"
    
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