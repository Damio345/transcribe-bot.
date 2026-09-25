import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
import imageio_ffmpeg

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ALLOWED_USERNAMES = ["mikhailfizafk", "Damil54"]

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY)
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def is_allowed(message: types.Message):
    return message.from_user.username in ALLOWED_USERNAMES

@dp.message(Command("start"))
async def start(message: types.Message):
    if not is_allowed(message):
        await message.answer("Доступ закрыт.")
        return
    await message.answer("Привет! Кидай аудио или видео (m4a, mp3, mp4, ogg, wav) — я переведу в текст.")

@dp.message(lambda m: m.audio or m.document or m.voice or m.video)
async def handle_audio(message: types.Message):
    if not is_allowed(message):
        await message.answer("Доступ закрыт.")
        return

    await message.answer("Файл получен, обрабатываю...")

    if message.audio:
        file = message.audio
    elif message.voice:
        file = message.voice
    elif message.video:
        file = message.video
    else:
        file = message.document

    file_info = await bot.get_file(file.file_id)
    file_path = f"/tmp/{file.file_name or 'audio.m4a'}"
    await bot.download_file(file_info.file_path, file_path)

    wav_path = "/tmp/audio.wav"

    try:
        # Конвертируем в wav через встроенный ffmpeg
        os.system(f'"{ffmpeg_exe}" -i "{file_path}" -ar 16000 -ac 1 -c:a pcm_s16le "{wav_path}" -y')

        with open(wav_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(wav_path, f.read()),
                model="whisper-large-v3",
                language="ru",
                response_format="text"
            )
        text = transcription
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return

    out_path = "/tmp/result.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    await message.answer_document(types.FSInputFile(out_path, filename="transcription.txt"))

    os.remove(file_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)
    os.remove(out_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
