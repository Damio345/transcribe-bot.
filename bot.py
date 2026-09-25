import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
import os
TOKEN = os.environ.get("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Кидай m4a или mp3 — я переведу в текст с таймкодами.")

@dp.message(lambda m: m.audio or m.document or m.voice)
async def handle_audio(message: types.Message):
    await message.answer("Файл получен, обрабатываю...")

    if message.audio:
        file = message.audio
    elif message.voice:
        file = message.voice
    else:
        file = message.document

    file_info = await bot.get_file(file.file_id)
    file_path = f"/tmp/{file.file_name or 'audio.m4a'}"
    await bot.download_file(file_info.file_path, file_path)

    segments, _ = model.transcribe(file_path, language="ru")
    text = "\n".join([f"[{s.start:.2f} - {s.end:.2f}] {s.text.strip()}" for s in segments])

    out_path = "/tmp/result.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    await message.answer_document(types.FSInputFile(out_path, filename="transcription.txt"))

    os.remove(file_path)
    os.remove(out_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
