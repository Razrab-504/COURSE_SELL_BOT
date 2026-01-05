from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kbd():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users:page:0")],
        [InlineKeyboardButton(text="💰 Продажи", callback_data="admin:purchases")],
        [InlineKeyboardButton(text="📚 Курсы", callback_data="admin:courses")],
        [InlineKeyboardButton(text="➕ Создать курс", callback_data="admin:courses:create")],
        [InlineKeyboardButton(text="✉️ Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin:settings")],
    ])


def users_page_kbd(page: int, has_prev: bool, has_next: bool):
    kb = []
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:users:page:{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin:users:page:{page+1}"))
    if nav_row:
        kb.append(nav_row)
    kb.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def user_detail_kbd(user_id: int, is_banned: bool):
    ban_text = "Разбанить" if is_banned else "Забанить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ban_text, callback_data=f"admin:user:{user_id}:toggle_ban")],
        [InlineKeyboardButton(text="✉️ Отправить сообщение", callback_data=f"admin:user:{user_id}:message")],
        [InlineKeyboardButton(text="🔙 К списку пользователей", callback_data="admin:users:page:0")]
    ])


def confirm_kbd(action: str, obj_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin:confirm:{action}:{obj_id}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin:cancel:{action}:{obj_id}")]
    ])


def courses_list_kbd(courses: list):
    kb = []
    for c in courses:
        kb.append([InlineKeyboardButton(text=f"{c.title} — ${c.price}", callback_data=f"admin:courses:detail:{c.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def course_detail_kbd(course_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin:courses:edit:{course_id}"), InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin:courses:delete:{course_id}")],
        [InlineKeyboardButton(text="🔙 К списку курсов", callback_data="admin:courses")]
    ])


def content_type_kbd():
    from src.db.enums import ContentType
    kb = []
    for ct in ContentType:
        kb.append([InlineKeyboardButton(text=ct.value, callback_data=f"admin:courses:content_type:{ct.name}")])
    kb.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="admin:cancel:content_type:0")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def settings_kbd(currency: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Валюта: {currency}", callback_data="admin:settings:currency")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin:menu")]
    ])