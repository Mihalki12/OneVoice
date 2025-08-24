from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.config import settings
from app.db import add_driver, remove_driver, list_drivers, order_stats
from app.keyboards import admin_menu_kb


class AdminForm(StatesGroup):
    add_driver_wait_id = State()
    remove_driver_wait_id = State()


router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return bool(settings and (user_id in settings.admin_ids))


@router.callback_query(F.data == "adm:add_driver")
async def admin_add_driver(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.add_driver_wait_id)
    await cb.message.edit_text("Отправьте tg_id водителя (число). Либо /cancel.")
    await cb.answer()


@router.message(AdminForm.add_driver_wait_id)
async def admin_add_driver_input(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Нужно число tg_id. Попробуйте снова или /cancel")
        return
    tg_id = int(text)
    ok = await add_driver(tg_id, f"driver_{tg_id}")
    if ok:
        await message.answer("Водитель добавлен.", reply_markup=admin_menu_kb())
        await state.clear()
    else:
        await message.answer("Не удалось добавить (возможно уже существует). Попробуйте другой tg_id.")


@router.callback_query(F.data == "adm:list_drivers")
async def admin_list_drivers(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    drivers = await list_drivers()
    if not drivers:
        await cb.message.edit_text("Список водителей пуст.", reply_markup=admin_menu_kb())
    else:
        lines = [f"{d['tg_id']} — {d['full_name']} (добавлен: {d['added_at']})" for d in drivers]
        await cb.message.edit_text("Зарегистрированные водители:\n" + "\n".join(lines), reply_markup=admin_menu_kb())
    await cb.answer()


@router.callback_query(F.data == "adm:stats")
async def admin_show_stats(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    stats = await order_stats()
    parts = [f"Всего заказов: {stats.get('total', 0)}"]
    for k, v in stats.items():
        if k == "total":
            continue
        parts.append(f"{k}: {v}")
    await cb.message.edit_text("Статистика:\n" + "\n".join(parts), reply_markup=admin_menu_kb())
    await cb.answer()