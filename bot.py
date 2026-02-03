from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
import logging
import os

BOT_TOKEN = "توکن_ربات_خودت_را_اینجا_قرار_ده"
ADMIN_IDS = [123456789]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_name TEXT,
    description TEXT
)''')
conn.commit()

class UploadState(StatesGroup):
    waiting_for_file = State()
    waiting_for_description = State()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📤 آپلود کانفیگ', '📂 مشاهده کانفیگ‌ها')
    await message.answer("🤖 Konfio فعال شد!", reply_markup=keyboard)

@dp.message_handler(commands=['upload'])
async def upload_cmd(message: types.Message):
    await UploadState.waiting_for_file.set()
    await message.answer("📤 فایل کانفیگ رو بفرست...")

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=UploadState.waiting_for_file)
async def get_file(message: types.Message, state: FSMContext):
    await state.update_data(
        file_id=message.document.file_id,
        file_name=message.document.file_name
    )
    await UploadState.next()
    await message.answer("📝 توضیح مختصر:")

@dp.message_handler(state=UploadState.waiting_for_description)
async def get_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("INSERT INTO configs (file_id, file_name, description) VALUES (?, ?, ?)",
                   (data['file_id'], data['file_name'], message.text))
    conn.commit()
    await state.finish()
    await message.answer("✅ کانفیگ ذخیره شد!")

@dp.message_handler(commands=['browse'])
async def browse_cmd(message: types.Message):
    cursor.execute("SELECT id, file_name FROM configs LIMIT 5")
    configs = cursor.fetchall()
    
    if not configs:
        await message.answer("📭 هیچ کانفیگی نیست")
        return
    
    text = "📂 کانفیگ‌ها:\n\n"
    for cfg in configs:
        text += f"📁 {cfg[1]}\n⬇️ /dl_{cfg[0]}\n\n"
    await message.answer(text)

@dp.message_handler(lambda m: m.text and m.text.startswith('/dl_'))
async def download_cmd(message: types.Message):
    try:
        cid = int(message.text.split('_')[1])
        cursor.execute("SELECT file_id FROM configs WHERE id=?", (cid,))
        cfg = cursor.fetchone()
        if cfg:
            await message.answer_document(cfg[0])
        else:
            await message.answer("❌ پیدا نشد")
    except:
        await message.answer("❌ خطا")

if __name__ == '__main__':
    print("✅ ربات روشن شد...")
    executor.start_polling(dp, skip_updates=True)
