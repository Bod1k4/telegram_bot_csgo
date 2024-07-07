import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

VIDEOS_DIR = 'bot/videos'
MAPS = ['mirage', 'dust2', 'inferno', 'ancient']
SIDES = ['CT', 'T']
POSITIONS = ['Side A', 'Side B', 'Mid']

map_keyboard = ReplyKeyboardBuilder()
map_keyboard.add(*[types.KeyboardButton(text=map_name) for map_name in MAPS])
map_keyboard.adjust(2)

side_keyboard = ReplyKeyboardBuilder()
side_keyboard.add(*[types.KeyboardButton(text=side_name) for side_name in SIDES])
side_keyboard.adjust(2)

position_keyboard = ReplyKeyboardBuilder()
position_keyboard.add(*[types.KeyboardButton(text=position_name) for position_name in POSITIONS])
position_keyboard.adjust(2)

user_choices = {}

@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    await message.answer('Привіт! Обери мапу:', reply_markup=map_keyboard.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text in MAPS)
async def choose_map(message: types.Message):
    user_choices[message.from_user.id] = {'map': message.text}
    await message.answer(
        f'Ти обрав мапу {message.text}. \nТепер обери сторону:',
        reply_markup=side_keyboard.as_markup(resize_keyboard=True),
    )

@dp.message(lambda message: message.text in SIDES)
async def choose_side(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_choices and 'map' in user_choices[user_id]:
        user_choices[user_id]['side'] = message.text.lower()
        await message.answer(
            f'Ти обрав сторону {message.text}. \nТепер обери позицію:',
            reply_markup=position_keyboard.as_markup(resize_keyboard=True),
        )
    else:
        await message.answer(
            'Спочатку треба обрати мапу.',
            reply_markup=map_keyboard.as_markup(resize_keyboard=True),
        )

@dp.message(lambda message: message.text in POSITIONS)
async def choose_position(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_choices and 'map' in user_choices[user_id] and 'side' in user_choices[user_id]:
        user_choices[user_id]['position'] = message.text.lower().replace(' ', '_')
        map_name = user_choices[user_id]['map']
        side = user_choices[user_id]['side']
        position = user_choices[user_id]['position']

        await send_video(message=message, map_name=map_name, side=side, position=position)
    else:
        await message.answer(
            'Спочатку треба обрати мапу та сторону.',
            reply_markup=map_keyboard.as_markup(resize_keyboard=True),
        )

async def send_video(message: types.Message, map_name: str, side: str, position: str):
    videos_dir = os.path.join(VIDEOS_DIR, map_name, side, position)

    if not os.path.exists(videos_dir):
        await message.answer('Вибач, такого відео немає.')
        return

    videos = os.listdir(videos_dir)

    if not videos:
        await message.answer('Немає відео для такої комбінації.')
        return

    for video_file in videos:
        video_path = os.path.join(videos_dir, video_file)
        video = FSInputFile(video_path)
        caption = os.path.splitext(video_file)[0].split('_', 2)[-1].replace('_', ' ')
        await bot.send_video(chat_id=message.chat.id, video=video, caption=caption)

    await message.answer('Ось всі відео для тебе!')

if __name__ == '__main__':
    dp.run_polling(bot)
