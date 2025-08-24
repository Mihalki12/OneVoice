from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import (
    is_driver,
    list_new_orders,
    driver_accept_order,
    get_driver_active_order,
    driver_mark_arrived,
    driver_complete_order,
)
from app.keyboards import list_orders_kb, driver_actions_kb, driver_menu_kb

router = Router(name="driver")


@router.callback_query(F.data == "drv:new")
async def driver_list_new(cb: CallbackQuery) -> None:
    if not await is_driver(cb.from_user.id):
        await cb.answer("Вы не зарегистрированы водителем", show_alert=True)
        return
    orders = await list_new_orders(limit=10)
    await cb.message.edit_text(
        "Свободные заказы:" + ("\n" + "\n".join([f"#{o['id']}: {o['pickup']} → {o['destination']}" for o in orders]) if orders else "\nНет заказов"),
        reply_markup=list_orders_kb([o["id"] for o in orders]),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("drv:take:"))
async def driver_take_order(cb: CallbackQuery) -> None:
    if not await is_driver(cb.from_user.id):
        await cb.answer("Вы не зарегистрированы водителем", show_alert=True)
        return
    order_id = int(cb.data.rsplit(":", 1)[1])
    ok = await driver_accept_order(order_id, cb.from_user.id)
    if ok:
        order = await get_driver_active_order(cb.from_user.id)
        await cb.message.edit_text(
            f"Заказ принят #{order_id}. Едем: {order['pickup']} → {order['destination']}",
            reply_markup=driver_actions_kb(order_id, order["status"] if order else "accepted"),
        )
    else:
        await cb.answer("Не удалось принять заказ. Возможно, его уже взяли.", show_alert=True)
    await cb.answer()


@router.callback_query(F.data == "drv:my")
async def driver_my(cb: CallbackQuery) -> None:
    if not await is_driver(cb.from_user.id):
        await cb.answer("Вы не зарегистрированы водителем", show_alert=True)
        return
    order = await get_driver_active_order(cb.from_user.id)
    if not order:
        await cb.message.edit_text("У вас нет активного заказа.", reply_markup=driver_menu_kb(has_active=False))
    else:
        await cb.message.edit_text(
            f"Текущий заказ #{order['id']}: {order['pickup']} → {order['destination']} (статус: {order['status']})",
            reply_markup=driver_actions_kb(order["id"], order["status"]),
        )
    await cb.answer()


@router.callback_query(F.data.startswith("drv:arrived:"))
async def driver_arrived(cb: CallbackQuery) -> None:
    if not await is_driver(cb.from_user.id):
        await cb.answer("Вы не зарегистрированы водителем", show_alert=True)
        return
    order_id = int(cb.data.rsplit(":", 1)[1])
    ok = await driver_mark_arrived(order_id, cb.from_user.id)
    if not ok:
        await cb.answer("Не удалось отметить \"на месте\".", show_alert=True)
        return
    order = await get_driver_active_order(cb.from_user.id)
    if order:
        await cb.message.edit_text(
            f"Текущий заказ #{order['id']}: {order['pickup']} → {order['destination']} (статус: {order['status']})",
            reply_markup=driver_actions_kb(order["id"], order["status"]),
        )
    await cb.answer()


@router.callback_query(F.data.startswith("drv:complete:"))
async def driver_complete(cb: CallbackQuery) -> None:
    if not await is_driver(cb.from_user.id):
        await cb.answer("Вы не зарегистрированы водителем", show_alert=True)
        return
    order_id = int(cb.data.rsplit(":", 1)[1])
    ok = await driver_complete_order(order_id, cb.from_user.id)
    if ok:
        await cb.message.edit_text("Заказ завершен. Спасибо за поездку!", reply_markup=driver_menu_kb(has_active=False))
    else:
        await cb.answer("Не удалось завершить заказ.", show_alert=True)
    await cb.answer()