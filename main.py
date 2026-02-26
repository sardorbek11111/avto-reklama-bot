import asyncio
from os import getenv
from dotenv import load_dotenv
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage  # BU JUDA MUHIM!
from aiogram.utils.keyboard import InlineKeyboardBuilder
load_dotenv()
# 1. SOZLAMALAR
TOKEN = "8777219562:AAHfJ6DK7qDEJRwkCniHGQB6OIzIqD0CX8A"  # @BotFather'dan olgan tokenni bura qo'ying
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # Xotirani ulash


# 2. HOLATLAR
class AdStates(StatesGroup):
    waiting_for_content = State()


# 3. ASOSIY MENYU (4 TA TUGMA)
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📢 Reklama joylash", callback_data="add_ads"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="my_stats"))
    builder.row(types.InlineKeyboardButton(text="💳 Balans", callback_data="fill_balance"))
    builder.row(types.InlineKeyboardButton(text="🆘 Yordam", callback_data="get_help"))
    return builder.as_markup()


@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Bot aktiv! Bo'limni tanlang:", reply_markup=get_main_menu())


# --- REKLAMA JOYLASHTIRISH (ISHLAYDIGAN QISMI) ---

@dp.callback_query(F.data == "add_ads")
async def start_ad(call: types.CallbackQuery, state: FSMContext):
    # Botni reklama kutish holatiga o'tkazamiz
    await state.set_state(AdStates.waiting_for_content)
    await call.message.answer("📝 Reklama matni yoki rasmini yuboring:")
    await call.answer()


@dp.message(AdStates.waiting_for_content)
async def get_ad_content(message: types.Message, state: FSMContext):
    # Foydalanuvchi rasm yoki matn yuborganda shu yerga keladi
    await message.answer("✅ Siz yuborgan reklama qabul qilindi:")

    # Kelgan postni (rasm, video yoki matn) preview qilish
    await message.copy_to(chat_id=message.from_user.id)

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_ok"))
    kb.row(types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad"))

    await message.answer("Tasdiqlaysizmi?", reply_markup=kb.as_markup())
    # Diqqat: Bu yerda state.clear() qilmaymiz, tasdiqlash tugmasini kutamiz!


# --- QOLGAN 3 TA TUGMA LOGIKASI ---

@dp.callback_query(F.data == "my_stats")
async def show_stats(call: types.CallbackQuery):
    await call.message.answer("📊 Statistikangiz: 0 ta reklama.", reply_markup=get_main_menu())
    await call.answer()


@dp.callback_query(F.data == "fill_balance")
async def fill_bal(call: types.CallbackQuery):
    await call.message.answer("💳 Hisobingiz: 0 so'm.", reply_markup=get_main_menu())
    await call.answer()


@dp.callback_query(F.data == "get_help")
async def help_me(call: types.CallbackQuery):
    await call.message.answer("🆘 Admin: @admin_user", reply_markup=get_main_menu())
    await call.answer()


# TASDIQLASH VA BEKOR QILISH
@dp.callback_query(F.data == "confirm_ok")
async def confirm(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚀 Reklama tekshirishga yuborildi!")
    await call.answer()


@dp.callback_query(F.data == "cancel_ad")
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Amal bekor qilindi.", reply_markup=get_main_menu())
    await call.answer()


# --- ISHGA TUSHIRISH ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

