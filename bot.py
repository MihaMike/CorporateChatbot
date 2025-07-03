import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "7906249510:AAE6CF_uP9N7ZQIS1BOH6sr_A9QpRjz6rCU"
ADMIN_CHAT_ID = -1002726322624

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

WELCOME_BUTTON = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Оформить пропуск", callback_data="start_form")]
    ]
)

class GuestForm(StatesGroup):
    full_name = State()
    is_foreign = State()
    citizenship = State()
    organization = State()
    visit_date = State()
    visit_time = State()
    need_parking = State()
    car_plate = State()
    car_brand = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Уважаемые Коллеги!\n\n"
        "Просим Вас заполнить форму для каждого приглашенного лица. "
        "Указанная информация будет использована исключительно в целях пропускного режима.",
        reply_markup=WELCOME_BUTTON
    )
    await state.clear()

@dp.callback_query(F.data == "start_form")
async def process_start_form(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Пожалуйста, введите ФИО гостя:")
    await state.set_state(GuestForm.full_name)
    await call.answer()

@dp.message(StateFilter(GuestForm.full_name))
async def step_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="foreign_yes"),
                InlineKeyboardButton(text="Нет", callback_data="foreign_no")
            ]
        ]
    )
    await message.answer("Гость — иностранный гражданин?", reply_markup=kb)
    await state.set_state(GuestForm.is_foreign)

@dp.callback_query(StateFilter(GuestForm.is_foreign))
async def step_is_foreign(call: types.CallbackQuery, state: FSMContext):
    if call.data == "foreign_yes":
        await state.update_data(is_foreign="Да")
        await call.message.answer("Укажите гражданство гостя:")
        await state.set_state(GuestForm.citizenship)
    else:
        await state.update_data(is_foreign="Нет", citizenship="-")
        await call.message.answer("Укажите организацию гостя и цель визита:")
        await state.set_state(GuestForm.organization)
    await call.answer()

@dp.message(StateFilter(GuestForm.citizenship))
async def step_citizenship(message: types.Message, state: FSMContext):
    await state.update_data(citizenship=message.text)
    await message.answer("Укажите организацию гостя и цель визита:")
    await state.set_state(GuestForm.organization)

@dp.message(StateFilter(GuestForm.organization))
async def step_organization(message: types.Message, state: FSMContext):
    await state.update_data(organization=message.text)
    await message.answer("Дата визита (ДД.ММ.ГГГГ):")
    await state.set_state(GuestForm.visit_date)

@dp.message(StateFilter(GuestForm.visit_date))
async def step_date(message: types.Message, state: FSMContext):
    await state.update_data(visit_date=message.text)
    await message.answer("Время визита (например, 14:00):")
    await state.set_state(GuestForm.visit_time)


@dp.message(StateFilter(GuestForm.visit_time))
async def step_time(message: types.Message, state: FSMContext):
    await state.update_data(visit_time=message.text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="parking_yes"),
                InlineKeyboardButton(text="Нет", callback_data="parking_no")
            ]
        ]
    )
    await message.answer(
        "Гостю необходима парковка для транспортного средства? (Количество парковочных мест строго ограничено (предоставляется в случае крайней необходимости, возможен отказ АЦ)",
        reply_markup=kb
    )
    await state.set_state(GuestForm.need_parking)

@dp.callback_query(StateFilter(GuestForm.need_parking))
async def step_parking(call: types.CallbackQuery, state: FSMContext):
    need_parking = "Да" if call.data == "parking_yes" else "Нет"
    await state.update_data(need_parking=need_parking)
    if need_parking == "Да":
        await call.message.answer("Пожалуйста, укажите госномер транспортного средства:")
        await state.set_state(GuestForm.car_plate)
    else:
        await call.message.answer("✅ Спасибо! Пропуск оформлен.")
        await send_summary(call.message, state)
        await call.answer()

@dp.message(StateFilter(GuestForm.car_plate))
async def step_car_plate(message: types.Message, state: FSMContext):
    await state.update_data(car_plate=message.text)
    await message.answer("Пожалуйста, укажите марку транспортного средства:")
    await state.set_state(GuestForm.car_brand)

@dp.message(StateFilter(GuestForm.car_brand))
async def step_car_brand(message: types.Message, state: FSMContext):
    await state.update_data(car_brand=message.text)
    await message.answer("✅ Спасибо! Пропуск оформлен.")
    await send_summary(message, state)

async def send_summary(message_or_call, state: FSMContext):
    data = await state.get_data()
    car_plate = data.get('car_plate', '-')
    car_brand = data.get('car_brand', '-')
    need_parking = data.get('need_parking', 'Нет')
    if need_parking == "Нет":
        car_plate = car_brand = '-'

    summary = (
        "📝 Новый запрос на пропуск:\n\n"
        f"👤 ФИО: {data.get('full_name','-')}\n"
        f"🌎 Иностранец: {data.get('is_foreign','-')}\n"
        f"🌍 Гражданство: {data.get('citizenship','-')}\n"
        f"🏢 Организация/цель визита: {data.get('organization','-')}\n"
        f"📅 Дата визита: {data.get('visit_date','-')}\n"
        f"⏰ Время визита: {data.get('visit_time','-')}\n"
        f"🚗 Парковка: {need_parking}\n"
        f"🔢 Госномер ТС: {car_plate}\n"
        f"🚘 Марка ТС: {car_brand}"
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    await message_or_call.answer(
        "Хотите оформить ещё один пропуск?",
        reply_markup=WELCOME_BUTTON
    )
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("start")
    asyncio.run(main())
