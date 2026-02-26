import asyncio
import logging
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

# ==========================================
# 1. SOZLAMALAR (O'ZINGIZNIKINI QO'YING)
# ==========================================
TOKEN = "8777219562:AAHfJ6DK7qDEJRwkCniHGQB6OIzIqD0CX8A"
ADMIN_ID = 5127908988  # O'zingizning Telegram ID raqamingizni yozing!
CHANNEL_ID = "-1003705464712"  # Bot admin bo'lgan kanalning ID raqami

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Vaqtinchalik baza (Keyinchalik SQL ga o'zgartirishingiz mumkin)
users_db = set()
stats_db = {"ads_posted": 0}

# ==========================================
# 2. HOLATLAR (FSM)
# ==========================================
class AdStates(StatesGroup):
    waiting_for_content = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# ==========================================
# 3. KLAVIATURALAR
# ==========================================
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📢 Reklama joylash", callback_data="add_ads"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="my_stats"))
    builder.row(types.InlineKeyboardButton(text="💳 Balans", callback_data="fill_balance"))
    builder.row(types.InlineKeyboardButton(text="🆘 Yordam", callback_data="get_help"))
    return builder.as_markup()

def get_admin_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Umumiy Statistika", callback_data="admin_stats"))
    builder.row(types.InlineKeyboardButton(text="✉️ Hammaga xabar yuborish", callback_data="admin_broadcast"))
    builder.row(types.InlineKeyboardButton(text="❌ Yopish", callback_data="close_admin"))
    return builder.as_markup()

# ==========================================
# 4. ASOSIY BUYRUQLAR VA MENYU LOGIKASI
# ==========================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    users_db.add(message.from_user.id) # Foydalanuvchini bazaga qo'shamiz
    await message.answer("Bot aktiv! Bo'limni tanlang:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "my_stats")
async def show_stats(call: types.CallbackQuery):
    await call.message.answer("📊 Sizning statistikangiz tez kunda ishga tushadi.", reply_markup=get_main_menu())
    await call.answer()

@dp.callback_query(F.data == "fill_balance")
async def fill_bal(call: types.CallbackQuery):
    await call.message.answer("💳 Hisobingiz: 0 so'm.", reply_markup=get_main_menu())
    await call.answer()

@dp.callback_query(F.data == "get_help")
async def help_me(call: types.CallbackQuery):
    await call.message.answer("🆘 Admin bilan bog'lanish: @admin_user", reply_markup=get_main_menu())
    await call.answer()

# ==========================================
# 5. REKLAMA JOYLASHTIRISH VA TASDIQLASH
# ==========================================
@dp.callback_query(F.data == "add_ads")
async def start_ad(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdStates.waiting_for_content)
    await call.message.answer("📝 Reklama matni, rasmi yoki videosini yuboring:")
    await call.answer()

@dp.message(AdStates.waiting_for_content)
async def get_ad_content(message: types.Message, state: FSMContext):
    # Xabarning ID sini FSM xotirasiga saqlaymiz
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)

    # Preview (qanday ko'rinishi)
    await message.copy_to(chat_id=message.chat.id)

    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✅ Adminga yuborish", callback_data="confirm_ok"))
    kb.row(types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad"))

    await message.answer("Ushbu reklama adminga tekshirish uchun yuborilsinmi?", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "confirm_ok")
async def confirm(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_id")
    chat_id = data.get("chat_id")

    # Adminga tasdiqlash uchun yuborish
    admin_kb = InlineKeyboardBuilder()
    # Call data ichida user va xabar ID sini berib yuboramiz
    admin_kb.button(text="✅ Kanalga chiqarish", callback_data=f"approve_{chat_id}_{msg_id}")
    admin_kb.button(text="❌ Rad etish", callback_data=f"reject_{chat_id}")
    admin_kb.adjust(1)

    await bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=chat_id,
        message_id=msg_id,
        reply_markup=admin_kb.as_markup()
    )

    await call.message.edit_text("🚀 Reklamangiz adminga tekshirish uchun yuborildi! Tasdiqlangach kanalga joylanadi.")
    await state.clear()
    await call.answer()


@dp.callback_query(F.data == "cancel_ad")
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Amal bekor qilindi.", reply_markup=get_main_menu())
    await call.answer()


# ==========================================
# 6. ADMIN PANEL VA ADMIN FUNKSIYALARI
# ==========================================
@dp.message(Command("admin"))
async def admin_panel_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Admin panelga xush kelibsiz!", reply_markup=get_admin_menu())
    else:
        await message.answer("Kechirasiz, siz admin emassiz.")


@dp.callback_query(F.data == "close_admin")
async def close_admin_panel(call: types.CallbackQuery):
    await call.message.delete()


@dp.callback_query(F.data == "admin_stats")
async def admin_statistics(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return

    text = (
        f"📊 <b>Umumiy statistika:</b>\n\n"
        f"👥 Foydalanuvchilar: {len(users_db)} ta\n"
        f"📢 Kanalga joylangan reklamalar: {stats_db['ads_posted']} ta"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


# --- Admin reklamani tasdiqlashi ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_ad_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return

    # Callback datadan ID larni ajratib olamiz
    _, user_id, msg_id = call.data.split("_")

    try:
        # Kanalga nusxasini yuborish (chiroyli ko'rinishda, "forwarded from" yozuvlarisiz)
        await bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=user_id, message_id=msg_id)

        # Foydalanuvchiga xabar berish
        await bot.send_message(chat_id=user_id, text="🎉 Tabriklaymiz! Reklamangiz kanalga joylandi.")

        stats_db["ads_posted"] += 1
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply("✅ Reklama kanalga muvaffaqiyatli joylandi.")
    except Exception as e:
        await call.message.reply(f"❌ Xatolik yuz berdi. Bot kanalga admin emasmi?\n{e}")
    await call.answer()


@dp.callback_query(F.data.startswith("reject_"))
async def reject_ad_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return

    _, user_id = call.data.split("_")
    await bot.send_message(chat_id=user_id, text="❌ Kechirasiz, reklamangiz admin tomonidan rad etildi.")

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply("Reklama rad etildi.")
    await call.answer()


# --- Hammaga xabar yuborish (Broadcast) ---
@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID: return
    await state.set_state(AdminStates.waiting_for_broadcast)
    await call.message.answer(
        "✉️ Barcha foydalanuvchilarga yuboriladigan xabarni (matn, rasm, video) yuboring:\n\n<i>Bekor qilish uchun /start ni bosing.</i>",
        parse_mode="HTML")
    await call.answer()


@dp.message(AdminStates.waiting_for_broadcast)
async def send_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    count = 0
    for user_id in users_db:
        try:
            await message.copy_to(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05)  # Telegram limitlariga tushmaslik uchun kichik tanaffus
        except Exception:
            pass  # Agar kishi botni bloklagan bo'lsa, o'tkazib yuboramiz

    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!")


# ==========================================
# 7. ISHGA TUSHIRISH
# ==========================================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
