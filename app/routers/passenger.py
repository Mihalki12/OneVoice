from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.db import get_user, set_user_phone, create_order, get_passenger_active_order
from app.keyboards import request_phone_kb, passenger_menu_kb


class PassengerForm(StatesGroup):
    waiting_pickup = State()
    waiting_destination = State()


router = Router(name="passenger")


@router.callback_query(F.data == "pass:order")
async def passenger_order_entry(cb: CallbackQuery, state: FSMContext) -> None:
    user = await get_user(cb.from_user.id)
    if not user or not user.get("phone"):
        await cb.message.answer(
            "Отправьте номер телефона для регистрации.",
            reply_markup=request_phone_kb(),
        )
        await cb.answer()
        return

    active = await get_passenger_active_order(cb.from_user.id)
    if active:
        await cb.message.answer(
            f"У вас уже есть активный заказ #{active['id']}: {active['pickup']} → {active['destination']} (статус: {active['status']})",
            reply_markup=passenger_menu_kb(has_active=True),
        )
        await cb.answer()
        return

    await state.clear()
    await state.set_state(PassengerForm.waiting_pickup)
    await cb.message.answer("Где вас забрать? Укажите адрес отправления.")
    await cb.answer()


@router.message(F.contact)
async def on_contact(message: Message) -> None:
    phone = message.contact.phone_number
    await set_user_phone(message.from_user.id, phone)
    await message.answer("Телефон сохранен. Теперь можно оформить заказ.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Нажмите: 'Вызвать такси'", reply_markup=passenger_menu_kb(has_active=False))


@router.message(PassengerForm.waiting_pickup)
async def on_pickup(message: Message, state: FSMContext) -> None:
    await state.update_data(pickup=message.text.strip())
    await state.set_state(PassengerForm.waiting_destination)
    await message.answer("Куда поедем? Укажите адрес назначения.")


@router.message(PassengerForm.waiting_destination)
async def on_destination(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    pickup = data.get("pickup", "")
    destination = message.text.strip()
    order_id = await create_order(message.from_user.id, pickup, destination)
    await state.clear()
    await message.answer(
        f"Заказ создан #{order_id}: {pickup} → {destination}. Ожидайте подтверждения водителя.",
        reply_markup=passenger_menu_kb(has_active=True),
    )


@router.callback_query(F.data == "pass:my")
async def passenger_my_order(cb: CallbackQuery) -> None:
    active = await get_passenger_active_order(cb.from_user.id)
    if not active:
        await cb.message.edit_text("Активных заказов нет.", reply_markup=passenger_menu_kb(has_active=False))
    else:
        await cb.message.edit_text(
            f"Мой заказ #{active['id']}: {active['pickup']} → {active['destination']} (статус: {active['status']})",
            reply_markup=passenger_menu_kb(has_active=True),
        )
    await cb.answer()