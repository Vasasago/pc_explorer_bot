import configparser
import os
import subprocess

import requests

from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types

import markups

config = configparser.ConfigParser()  # Создание конфига

# Проверяем, существует ли файл "config.txt"
if not os.path.isfile("config.ini"):
    # Если файл не существует, создаем его
    with open("config.ini", "w") as file:
        pass


# Проверка токена бота перед созданием экземпляра
def check_bot_token(token):
    try:
        url = f'https://api.telegram.org/bot{token}/getMe'
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False


# Проверяем, пустой ли файл "config.txt"
if os.stat("config.ini").st_size == 0:
    # Если файл пустой, запрашиваем у пользователя необходимую информацию

    while True:
        bot_token = input('Введите токен бота: ')
        if check_bot_token(bot_token):
            break

    config.add_section('tg-bot')

    config.set('tg-bot', 'bot_token', f'{bot_token}')
    config.set('tg-bot', 'user_id', '')

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    config.read('config.ini')

    bot_token = config.get('tg-bot', 'bot_token')
    USER_ID = config.get('tg-bot', 'user_id')

else:

    config.read('config.ini')

    bot_token = config.get('tg-bot', 'bot_token')
    USER_ID = config.get('tg-bot', 'user_id')

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

edit_msg = None
path = ''
page = 1


# При старте
async def on_startup(dp):
    if USER_ID != '':
        print('Start polling...')
        await bot.send_message(chat_id=USER_ID, text="✅ Бот запущен!")
    else:
        print('User id не найден.\nНажмите /start, чтобы добавить ID.')


# При отключении
async def on_shutdown(dp):
    print('Stop polling...')
    await bot.send_message(chat_id=USER_ID, text="📴 Бот отключен!")


# проверка id пользователя
async def check_user_id(id_from_user):
    if str(id_from_user) != str(USER_ID):
        await bot.send_message(chat_id=id_from_user, text="❗ У вас нет доступа к этому боту!")
        return False
    else:
        return True


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global USER_ID
    # Если есть User_id, ничего не делаем. Если нет - записываем в файл.
    if USER_ID == '':
        config.set('tg-bot', 'user_id', f'{message.from_user.id}')

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
            USER_ID = message.from_user.id
            print(f'User ID: {str(USER_ID)}')

    if await check_user_id(message.from_user.id) is False:
        return

    await message.answer("🙋 *Добро пожаловать в бот-проводник для вашего пк!\n💿Выберите диск:",
                         reply_markup=markups.scanning_drives())


@dp.message_handler(commands=['explorer'])
async def start(message: types.Message):
    global edit_msg

    if await check_user_id(message.from_user.id) is False:
        return

    edit_msg = await bot.send_message(chat_id=USER_ID, text="💿Выберите диск:",
                                      reply_markup=markups.scanning_drives())


def back_path():
    global path

    path_list = path.split('\\')
    path_list.pop(-1)
    path = ''

    for i in path_list:
        if i != '':
            path += i
        if i != path_list[-1] or path[-1] == ':':
            path += '\\'


@dp.callback_query_handler()
async def main_explorer(callback_query: types.CallbackQuery):
    global edit_msg, path, page

    if await check_user_id(callback_query.from_user.id) is False:
        return

    await callback_query.answer()

    command = callback_query.data

    path = path.replace('None', '')

    if command == 'previous_page':
        if page != 1:
            page -= 1

        path, page, markup = markups.scanning_folders(path, page)

        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id,
                                               text=f'➡ Текущий путь: {path}\n📃 Страница: {page}', reply_markup=markup)
    elif command == 'next_page':
        path, page, markup = markups.scanning_folders(path, page + 1)

        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id,
                                               text=f'➡ Текущий путь: {path}\n📃 Страница: {page}', reply_markup=markup)
    elif command == 'back_to_drives':
        print(path)
        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id, text="💿Выберите диск:",
                                               reply_markup=markups.scanning_drives())
    elif command == 'back_explorer':

        back_path()

        print(path)

        path, page, markup = markups.scanning_folders(path)

        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id,
                                               text=f'➡ Текущий путь: {path}\n📃 Страница: {page}', reply_markup=markup)

    elif command == 'run':
        subprocess.run(['start', '', path], shell=True)

    elif command == 'download':
        edit_msg = await bot.edit_message_text(chat_id=USER_ID,
                                               message_id=callback_query.message.message_id,
                                               text='⏳ Идёт загрузка файла.')

        with open(path, 'rb') as file:
            await bot.send_document(chat_id=USER_ID, document=file)

        await bot.delete_message(chat_id=USER_ID, message_id=edit_msg.message_id)

        back_path()

        print(path)

        path, page, markup = markups.scanning_folders(path)

        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id,
                                               text=f'➡ Текущий путь: {path}\n📃 Страница: {page}', reply_markup=markup)

    elif command == 'delete':
        os.remove(path)

    elif os.path.isfile(path + "\\" + str(markups.folders_names.get(command)))\
            and os.access(path + "\\" + str(markups.folders_names.get(command)), os.X_OK):
        path = path + "\\" + str(markups.folders_names.get(command))
        print(path)
        edit_msg = await bot.edit_message_text(chat_id=USER_ID,
                                               message_id=callback_query.message.message_id,
                                               text=f'➡ Текущий путь:\n{path}' + '\n📂 Выберите действие:',
                                               reply_markup=markups.script_file_markup)

    else:
        path, page, markup = markups.scanning_folders(command)

        edit_msg = await bot.edit_message_text(chat_id=USER_ID, message_id=edit_msg.message_id,
                                               text=f'➡ Текущий путь: {path}\n📃 Страница: {page}', reply_markup=markup)


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, on_startup=on_startup, on_shutdown=on_shutdown, timeout=30)
