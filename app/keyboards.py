from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def role_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧑‍🦱 Пассажир", callback_data="role:passenger")],
            [InlineKeyboardButton(text="🚕 Водитель", callback_data="role:driver")],
            [InlineKeyboardButton(text="🛠 Администратор", callback_data="role:admin")],
        ]
    )


def request_phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить телефон", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def passenger_menu_kb(has_active: bool) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append([InlineKeyboardButton(text="📲 Вызвать такси", callback_data="pass:order")])
    if has_active:
        buttons.append([InlineKeyboardButton(text="🧾 Мой заказ", callback_data="pass:my")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def driver_menu_kb(has_active: bool) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append([InlineKeyboardButton(text="🆕 Свободные заказы", callback_data="drv:new")])
    if has_active:
        buttons.append([InlineKeyboardButton(text="🚗 Мой заказ", callback_data="drv:my")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить водителя", callback_data="adm:add_driver")],
            [InlineKeyboardButton(text="👨‍🔧 Список водителей", callback_data="adm:list_drivers")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")],
        ]
    )


def list_orders_kb(order_ids: list[int]) -> InlineKeyboardMarkup:
    keyboard = []
    for oid in order_ids:
        keyboard.append([
            InlineKeyboardButton(text=f"Взять заказ #{oid}", callback_data=f"drv:take:{oid}")
        ])
    if not keyboard:
        keyboard = [[InlineKeyboardButton(text="Обновить", callback_data="drv:new")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def driver_actions_kb(order_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "accepted":
        buttons.append([InlineKeyboardButton(text="🅿️ На месте", callback_data=f"drv:arrived:{order_id}")])
    if status in {"accepted", "arrived"}:
        buttons.append([InlineKeyboardButton(text="✅ Завершить", callback_data=f"drv:complete:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)