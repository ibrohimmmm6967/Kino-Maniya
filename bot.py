import os
import asyncio
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db_api import *
from db import init_db


# ================= CONFIG =================
TOKEN = "8713766431:AAFrkUH_OK3sl98PRgB2HCAow39gjhddEOw"
ADMIN_ID = 7406341580

def is_admin(user_id):
    return user_id == ADMIN_ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = set()
waiting_name_search = set()
waiting_order = set()
adding_movie = {}
deleting_movie = set()

# ================= HELPERS =================
def normalize_text(s: str) -> str:
    return "".join(s.lower().split())

async def send_movie(message, code):
    row = get_movie_by_code(code)
    if not row:
        return False
        
    movie = movie_row_to_dict(row)
    if not movie:
        return False

    file_id = movie.get("file_id")
    name = movie.get("name", "Noma'lum")
    views = movie.get("views", 0) + 1

    if file_id:
        try:
            caption_text = (
                f"🎬 <b>{name}</b>\n\n"
                f"📥 <b>Yuklashlar soni:</b> {views}\n\n"
                f"🤖 <b>Bizning bot:</b> @kino1_maniya_bot"
            )
            await message.answer_video(file_id, caption=caption_text, parse_mode="HTML")
            increment_views(code)
            return True
        except Exception as e:
            print("VIDEO SEND (file_id) ERROR:", e)

    await message.answer("⚠️ Bu filmni yuborib bo'lmadi – video yo'q yoki fayl topilmadi.")
    return False


def movie_row_to_dict(row):
    if not row:
        return None
    if isinstance(row, dict):
        return row
    try:
        # DB row: id, code, name, file_id, views
        return {
            "id": row[0],
            "code": str(row[1]),
            "name": row[2],
            "file_id": row[3],
            "views": row[4] if len(row) > 4 else 0
        }
    except Exception:
        return None

# ==================== MENUS ====================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Film qidirish"), KeyboardButton(text="🔥 Top filmlar")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

search_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Nom orqali")],
        [KeyboardButton(text="🎬 Barcha filmlar")],
        [KeyboardButton(text="📦 Film buyurtma qilish")],
        [KeyboardButton(text="🏠 Bosh menyu")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Kino qo‘shish"), KeyboardButton(text="❌ Kino o‘chirish")],
        [KeyboardButton(text="📊 Admin Statistika")],
        [KeyboardButton(text="🏠 Asosiy menyu")]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    users.add(message.from_user.id)
    user_name = message.from_user.first_name
    photo_path = "banner.jpg"
    text = (
        f"🎬 Salom, {user_name}!\n"
        f"KinoManiya botiga xush kelibsiz!\n\n"
        f"👇 Filmlar uchun menyudan foydalaning."
    )
    await message.answer(text,reply_markup=main_menu)

# ================= MENUS =================
@dp.message(F.text == "🔍 Film qidirish")
async def open_search_menu(message: types.Message):
    await message.answer("🎯 Qidiruv menyusi:", reply_markup=search_menu)

@dp.message(F.text.in_(["🏠 Bosh menyu", "🏠 Asosiy menyu"]))
async def back_to_main(message: types.Message):
    uid = message.from_user.id

    waiting_name_search.discard(uid)
    waiting_order.discard(uid)
    adding_movie.pop(uid, None)
    deleting_movie.discard(uid)

    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu)


# ================= SEARCH =================
@dp.message(F.text == "🔍 Nom orqali")
async def ask_name(message: types.Message):
    waiting_name_search.add(message.from_user.id)
    await message.answer("✍️ Film nomini yoki kodini yozing:")

@dp.message(F.text == "🎬 Barcha filmlar")
async def show_all(message: types.Message):
    rows = get_all_movies()  # или функция получения всех фильмов из db_api
    if not rows:
        await message.answer("🎬 Hozircha hech qanday film yo'q.")
        return

    text = "🎬 <b>Mavjud filmlar:</b>\n\n"
    for r in rows:
        m = movie_row_to_dict(r)
        if not m:
            continue
        text += f'🎬 {m.get("name", "Nomalum")} | 🆔 <code>{m.get("code", "-")}</code>\n'

    text += "\n💡 Kinoni ko'rish uchun uning kodini yuboring."
    await message.answer(text, parse_mode="HTML")

# ================= ORDER =================
@dp.message(F.text == "📦 Film buyurtma qilish")
async def order_film(message: types.Message):
    waiting_name_search.discard(message.from_user.id)
    waiting_order.add(message.from_user.id)
    await message.answer("📩 Qaysi film kerak? Nomini yozib yuboring:")

# ================= TOP =================
@dp.message(F.text == "🔥 Top filmlar")
async def show_top_movies(message: types.Message):
    movies = get_top_movies()

    if not movies:
        await message.answer("📭 Filmlar yo‘q.")
        return

    text = "🔥 TOP FILMLAR:\n\n"

    for i, m in enumerate(movies, start=1):
        # get_top_movies() qaytaradi: (name, views)
        name = m[0]
        views = m[1]

        text += f"{i}. {name} — 👁 {views}\n"

    await message.answer(text)


# ================= STATS =================
@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    total_movies = count_movies()
    total_views = count_views()
    text = (
        "📊 STATISTIKA\n\n"
        f"🎞 Filmlar: {total_movies}\n"
        f"👁 Ko‘rishlar: {total_views}\n"
    )
    await message.answer(text)

# ================= ADMIN =================
@dp.message(Command("admin"))
async def open_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Admin emassan.")
        return
    await message.answer("🛠 Admin panel:", reply_markup=admin_menu)

@dp.message(F.text == "➕ Kino qo‘shish")
async def admin_add_movie_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    adding_movie[message.from_user.id] = {"step": "code"}
    await message.answer("🆔 Kino kodini yubor:")

@dp.message(lambda msg: msg.from_user.id in adding_movie)
async def admin_add_movie_process(message: types.Message):
    uid = message.from_user.id
    data = adding_movie[uid]

    if data["step"] == "code":
        data["code"] = message.text.strip()
        data["step"] = "name"
        await message.answer("🎬 Kino nomini yubor:")
        return

    if data["step"] == "name":
        data["name"] = message.text.strip()
        data["step"] = "genre"
        await message.answer("🎭 Janrini yozing:")
        return

    if data["step"] == "genre":
        data["genre"] = message.text.strip()
        data["step"] = "video"
        await message.answer("📹 Videoni yuboring:")
        return

    if data["step"] == "video":
        if not message.video:
            await message.answer("❌ Video yuboring.")
            return
        add_movie(
            code=data["code"],
            name=data["name"],
            genre=data["genre"],
            file_id=message.video.file_id
        )
        adding_movie.pop(uid)
        await message.answer("✅ Kino qo‘shildi!")

# ================= DELETE =================
@dp.message(F.text == "❌ Kino o‘chirish")
async def admin_delete_movie_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    deleting_movie.add(message.from_user.id)
    await message.answer("🗑 Kino kodini yuboring:")

@dp.message(lambda msg: msg.from_user.id in deleting_movie)
async def admin_delete_movie_process(message: types.Message):
    delete_movie(message.text.strip())
    deleting_movie.remove(message.from_user.id)
    await message.answer("✅ Kino o‘chirildi.")

# ================= ADMIN STATS =================
@dp.message(F.text == "📊 Admin Statistika")
async def admin_stats(message: types.Message):
    total_movies = count_movies()
    total_views = count_views()
    text = (
        "🛠 ADMIN STATISTIKA\n\n"
        f"🎬 Filmlar: {total_movies}\n"
        f"👁 Jami ko‘rishlar: {total_views}\n"
    )
    await message.answer(text)

# ================= CANCEL =================
@dp.message(F.text == "❌ Bekor qilish")
async def cancel_all(message: types.Message):
    uid = message.from_user.id
    waiting_name_search.discard(uid)
    waiting_order.discard(uid)
    adding_movie.pop(uid, None)
    deleting_movie.discard(uid)
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu)

# ================= USER HANDLER =================
@dp.message()
async def user_text_handler(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id
    text = message.text.strip().lower()

# 📦 ORDER HANDLER
    if user_id in waiting_order:
        waiting_order.remove(user_id)

        username = message.from_user.username or "Username yo‘q"
        order_text = message.text.strip()

        admin_text = (
            "📦 YANGI FILM BUYURTMA!\n\n"
            f"👤 User: @{username}\n"
            f"🆔 ID: {user_id}\n"
            f"🎬 So‘rov: {order_text}"
        )

        await bot.send_message(ADMIN_ID, admin_text)
        await message.answer("✅ Buyurtmangiz qabul qilindi!")
        return

    # SEARCH BY CODE
    row = get_movie_by_code(text)
    if row:
        await send_movie(message, text)
        return

    # SEARCH BY NAME
    if user_id in waiting_name_search:
        waiting_name_search.remove(user_id)
        rows = get_all_movies()
        found = False
        for r in rows:
            m = movie_row_to_dict(r)
            if not m:
                continue
            if normalize_text(text) in normalize_text(m["name"]):
                await send_movie(message, m["code"])
                found = True
                break
        if not found:
            await message.answer("❓ Film topilmadi.")
    return

from aiogram import F
from aiogram.types import Message

@dp.message(F.video)
async def handle_video(message: Message):
    file_id = message.video.file_id

    await message.answer(
        f"✅ Video qabul qilindi!\n\n"
        f"📦 File ID:\n<code>{file_id}</code>",
        parse_mode="HTML"
    )


# ================= RUN =================
async def main():
    init_db()
    print("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



