from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

router = Router()


# ================= НАСТРОЙКИ МИЛАН =================

# Фото шкафов (замените на реальные URL)
MILAN_PHOTOS = {
    2: "https://i.imgur.com/JqYQ5Zy.jpg",
    3: "https://i.imgur.com/JqYQ5Zy.jpg",
    4: "https://i.imgur.com/JqYQ5Zy.jpg",
    5: "https://i.imgur.com/JqYQ5Zy.jpg",
    6: "https://i.imgur.com/JqYQ5Zy.jpg"
}

# Размеры (высота, ширина, глубина)
MILAN_SIZES = {
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

HANDLE_PRICES = {30: 0, 60: 700, 100: 1000}
DRAWERS_PRICE = 2000

COLORS = {'wh': 'Белый', 'gr': 'Серый', 'va': 'Ваниль', 'li': 'Лино', 'vt': 'Ватан'}
DOORS = {'turk': 'Турция', 'rim': 'Рим', 'aysha': 'Айша', 'mirror': 'Рамка'}

# ================= ФУНКЦИИ =================

def parse(data):
    """m_двери_цвет_дверь_рамки_ручки_трубы_ящики_антр"""
    p = data.split("_")
    return {
        'doors': int(p[1]),
        'color': p[2],
        'door_type': p[3],
        'mirrors': int(p[4]),
        'handles': int(p[5]),
        'tubes': int(p[6]),
        'drawers': p[7] == '1',
        'antresol': p[8] == '1'
    }

def code(doors, color, door, mirrors, handles, tubes, drawers, antresol):
    return f"m_{doors}_{color}_{door}_{mirrors}_{handles}_{tubes}_{1 if drawers else 0}_{1 if antresol else 0}"

def calc_price(c):
    """Расчёт цены"""
    doors = c['doors']
    door_type = c['door_type']
    mirrors = c['mirrors']
    handles = c['handles']
    tubes = c['tubes']
    drawers = c['drawers']
    antresol = c['antresol']
    
    # Базовая цена
    if doors == 6 and tubes == 1:
        base = PRICES_6_1T_ANT[door_type] if antresol else PRICES_6_1T[door_type]
    else:
        base = PRICES_ANT[doors][door_type] if antresol else PRICES[doors][door_type]
    
    # Рамки = как Турция, пересчёт если Айша
    if mirrors > 0 and door_type == 'aysha':
        turk_base = PRICES_ANT[doors]['turk'] if antresol else PRICES[doors]['turk']
        aysha_base = base
        diff_per_door = (aysha_base - turk_base) / doors
        base = turk_base + diff_per_door * (doors - mirrors)
    
    # Ручки
    handle_extra = HANDLE_PRICES[handles] * doors
    
    # Ящики
    drawer_extra = DRAWERS_PRICE if drawers else 0
    
    return int(base + handle_extra + drawer_extra)

def get_text(c, price):
    """Текст карточки"""
    doors = c['doors']
    s = MILAN_SIZES[doors]
    h = s['h'] + (50 if c['antresol'] else 0)
    
    door_text = DOORS[c['door_type']]
    if c['mirrors'] > 0:
        door_text = f"{doors - c['mirrors']}× {DOORS[c['door_type']]} + {c['mirrors']}× Рамка"
    else:
        door_text = f"{doors}× {DOORS[c['door_type']]}"
    
    text = f"🚪 <b>Шкаф МИЛАН {doors} дверей</b>\n\n"
    text += f"📐 Размеры: {s['w']}×{h}×{s['d']} см\n\n"
    text += f"<b>Ваш выбор:</b>\n"
    text += f"├ Цвет: {COLORS[c['color']]}\n"
    text += f"├ Двери: {door_text}\n"
    if doors == 6:
        text += f"├ Трубы: {c['tubes']} шт\n"
    text += f"├ Ручки: {c['handles']} см"
    if HANDLE_PRICES[c['handles']] > 0:
        text += f" (+{HANDLE_PRICES[c['handles']] * doors:,}₽)"
    text += "\n"
    text += f"├ Ящики: {'Да (+2,000₽)' if c['drawers'] else 'Нет'}\n"
    text += f"└ Антресоль: {'Да (+50 см)' if c['antresol'] else 'Нет'}\n\n"
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="2 дв", callback_data=code(2,'wh','turk',0,30,2,False,False)),
            InlineKeyboardButton(text="3 дв", callback_data=code(3,'wh','turk',0,30,2,False,False)),
            InlineKeyboardButton(text="4 дв", callback_data=code(4,'wh','turk',0,30,2,False,False)),
        ],
        [
            InlineKeyboardButton(text="5 дв", callback_data=code(5,'wh','turk',0,30,2,False,False)),
            InlineKeyboardButton(text="6 дв", callback_data=code(6,'wh','turk',0,30,2,False,False)),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_cat")]
    ])
    
    await cb.message.edit_text(
        "🚪 <b>Шкаф МИЛАН</b>\n\n"
        "Выберите количество дверей:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("m_"))
async def milan_show(cb: CallbackQuery):
    """Карточка товара"""
    c = parse(cb.data)
    price = calc_price(c)
    text = get_text(c, price)
    
    # Кнопки опций
    kb = InlineKeyboardMarkup(inline_keyboard=[
        # Опции
        [
            InlineKeyboardButton(text="🎨 Цвет", callback_data=f"opt_color_{cb.data}"),
            InlineKeyboardButton(text="🚪 Двери", callback_data=f"opt_door_{cb.data}"),
        ],
        [
            InlineKeyboardButton(text="✋ Ручки", callback_data=f"opt_handle_{cb.data}"),
            InlineKeyboardButton(text="🪞 Рамки", callback_data=f"opt_mirror_{cb.data}"),
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if c['antresol'] else '➕'} Антресоль",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handles'], c['tubes'], c['drawers'], not c['antresol'])
            ),
            InlineKeyboardButton(
                text=f"{'✅' if c['drawers'] else '➕'} Ящики",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handles'], c['tubes'], not c['drawers'], c['antresol'])
            ),
        ],
        # Трубы для 6 дверей
        *([
            [
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==1 else '⚪'} 1 труба",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handles'], 1, c['drawers'], c['antresol'])
                ),
                InlineKeyboardButton(
                    text=f"{'✅' if c['tubes']==2 else '⚪'} 2 трубы",
                    callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], c['handles'], 2, c['drawers'], c['antresol'])
                ),
            ]
        ] if c['doors'] == 6 else []),
        # Корзина
        [InlineKeyboardButton(text=f"🛒 В корзину • {price:,} ₽", callback_data=f"cart_{cb.data}")],
        # Навигация
        [
            InlineKeyboardButton(text="🔄 Размер", callback_data="cat_milan"),
            InlineKeyboardButton(text="◀️ Каталог", callback_data="back_cat")
        ]
    ])
    
    # Отправляем фото с текстом
    photo_url = MILAN_PHOTOS.get(c['doors'], MILAN_PHOTOS[2])
    
    try:
        # Пробуем редактировать как фото
        await cb.message.edit_media(
            media=InputMediaPhoto(media=photo_url, caption=text, parse_mode="HTML"),
            reply_markup=kb
        )
    except:
        try:
            # Пробуем редактировать текст
            await cb.message.edit_text(text, reply_markup=kb)
        except:
            # Отправляем новое сообщение с фото
            await cb.message.delete()
            await cb.message.answer_photo(photo=photo_url, caption=text, reply_markup=kb)
    
    await cb.answer()


# ===== ВЫБОР ЦВЕТА =====
@router.callback_query(F.data.startswith("opt_color_"))
async def opt_color(cb: CallbackQuery):
    orig = cb.data.replace("opt_color_", "")
    c = parse(orig)
    
    buttons = []
    for col_code, col_name in COLORS.items():
        is_sel = col_code == c['color']
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{col_name}",
                callback_data=code(c['doors'], col_code, c['door_type'], c['mirrors'], c['handles'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(
        caption="🎨 <b>Выберите цвет:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


# ===== ВЫБОР ДВЕРЕЙ =====
@router.callback_query(F.data.startswith("opt_door_"))
async def opt_door(cb: CallbackQuery):
    orig = cb.data.replace("opt_door_", "")
    c = parse(orig)
    
    buttons = []
    for d_code, d_name in [('turk', 'Турция'), ('rim', 'Рим'), ('aysha', 'Айша')]:
        is_sel = d_code == c['door_type'] and c['mirrors'] == 0
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{d_name}",
                callback_data=code(c['doors'], c['color'], d_code, 0, c['handles'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(
        caption="🚪 <b>Выберите тип дверей:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


# ===== ВЫБОР РУЧЕК =====
@router.callback_query(F.data.startswith("opt_handle_"))
async def opt_handle(cb: CallbackQuery):
    orig = cb.data.replace("opt_handle_", "")
    c = parse(orig)
    
    buttons = []
    for h in [30, 60, 100]:
        is_sel = h == c['handles']
        extra = HANDLE_PRICES[h] * c['doors']
        label = f"{h} см"
        if extra > 0:
            label += f" (+{extra:,}₽)"
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{label}",
                callback_data=code(c['doors'], c['color'], c['door_type'], c['mirrors'], h, c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(
        caption="✋ <b>Выберите размер ручек:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


# ===== ВЫБОР РАМОК =====
@router.callback_query(F.data.startswith("opt_mirror_"))
async def opt_mirror(cb: CallbackQuery):
    orig = cb.data.replace("opt_mirror_", "")
    c = parse(orig)
    
    buttons = []
    for m in range(0, c['doors']):
        is_sel = m == c['mirrors']
        if m == 0:
            label = "Без рамок"
        else:
            label = f"{c['doors']-m}× {DOORS[c['door_type']]} + {m}× Рамка"
        buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_sel else ''}{label}",
                callback_data=code(c['doors'], c['color'], c['door_type'], m, c['handles'], c['tubes'], c['drawers'], c['antresol'])
            )
        )
    
    # Разбиваем на ряды по 2
    rows = [buttons[i:i+1] for i in range(0, len(buttons))]
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=orig)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    
    await cb.message.edit_caption(
        caption="🪞 <b>Добавить рамки с зеркалом:</b>",
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
        buttons.append(
            InlineKeyboardButton(text=str(qty), callback_data=f"addq_{qty}_{orig}")
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:3],
        buttons[3:],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=orig)]
    ])
    
    await cb.message.edit_caption(
        caption="📦 <b>Укажите количество:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("addq_"))
async def add_to_cart(cb: CallbackQuery):
    parts = cb.data.split("_", 2)
    qty = int(parts[1])
    c = parse(parts[2])
    price = calc_price(c)
    total = price * qty
    
    door_text = DOORS[c['door_type']]
    if c['mirrors'] > 0:
        door_text = f"{c['doors']-c['mirrors']}× {DOORS[c['door_type']]} + {c['mirrors']}× Рамка"
    
    # TODO: Сохранить в БД
    
    await cb.answer(
        f"✅ Добавлено!\n\n"
        f"Милан {c['doors']}дв • {COLORS[c['color']]}\n"
        f"Двери: {door_text}\n"
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
        await cb.message.edit_text("📋 <b>Каталог мебели</b>\n\nВыберите:", reply_markup=kb)
    except:
        await cb.message.delete()
        await cb.message.answer("📋 <b>Каталог мебели</b>\n\nВыберите:", reply_markup=kb)


@router.callback_query(F.data == "go_cart")
async def go_cart(cb: CallbackQuery):
    await cb.answer("🛒 Корзина в разработке", show_alert=True)