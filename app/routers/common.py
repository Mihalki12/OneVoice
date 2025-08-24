from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.db import upsert_user, get_user
from app.keyboards import role_choice_kb, passenger_menu_kb, driver_menu_kb, admin_menu_kb
from app.config import settings

router = Router(name="common")


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    await upsert_user(message.from_user.id, message.from_user.full_name)
    user = await get_user(message.from_user.id)
    await message.answer(
        "Привет! Выберите роль:", reply_markup=role_choice_kb()
    )


@router.callback_query(F.data.startswith("role:"))
async def on_role_choice(cb: CallbackQuery) -> None:
    role = cb.data.split(":", 1)[1]
    if role == "passenger":
        await cb.message.edit_text(
            "Режим пассажира.", reply_markup=passenger_menu_kb(has_active=False)
        )
    elif role == "driver":
        # Show driver menu regardless of registration, real access checks in driver router
        await cb.message.edit_text(
            "Режим водителя.", reply_markup=driver_menu_kb(has_active=False)
        )
    elif role == "admin":
        if cb.from_user.id in (settings.admin_ids if settings else []):
            await cb.message.edit_text(
                "Режим администратора.", reply_markup=admin_menu_kb()
            )
        else:
            await cb.answer("Нет доступа", show_alert=True)
    await cb.answer()