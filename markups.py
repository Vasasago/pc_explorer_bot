import math
import os

import psutil
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

drives_in = []
drives_names = []

folders_names = {}

all_path = ''


def scanning_drives():
    # Получаем список дисков, записываем в drives_in и создаём инлайн - кнопки
    drives = psutil.disk_partitions()

    drives_in.clear()
    drives_names.clear()

    # Проверяем диски на заполненность
    for drive in drives:
        try:
            drive_usage = psutil.disk_usage(drive.mountpoint)

            # Если объем диска больше 0, добавляем инлайн кнопку в массив
            if drive_usage.total > 0:
                drives_in.append(InlineKeyboardButton(drive.device, callback_data=drive.device))
                drives_names.append(drive.device)

        except Exception as e:
            print(f"{e}\n\n")

    # Создаем маркап с дисками
    drives_markup = InlineKeyboardMarkup(row_width=4).add(*drives_in)

    return drives_markup


def scanning_folders(path, page=1, items_per_page=20):
    global all_path

    if path in drives_in:
        all_path = path

    if path in folders_names.keys():
        slash = ''

        if all_path[-1] != '\\':
            slash = '\\'

        all_path = all_path + slash + folders_names.get(path)
        direct = os.listdir(all_path)  # Получаем список папок по пути
    else:
        all_path = path
        direct = os.listdir(path)

    folders = []  # Список папок

    for folder in direct:
        # Если папка не системная, добавляем ее в список
        if folder[0] != '.' and folder[0] != '$':
            folders.append(folder)

    if path in drives_in:  # Если директория корневая (начало одного из дисков) прибавляем к диску папку
        name = folders_names.get(path)  # Получаем имя файла или папки по ее ключу
        path += f'{name}'
    else:
        name = folders_names.get(path)
        path += f'\\{name}'

    # Рассчитываем начальный и конечный индексы для текущей страницы
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    pages = math.ceil((len(folders) / items_per_page))  # Рассчитываем количество страниц

    inline_folders = []  # Пустой массив для инлайн кнопок с названиями папок и коллбэками в виде их ключей
    folders_names.clear()

    i = 0

    # Создаем список с Inline-кнопками только для элементов на текущей странице
    for folder in folders[start_index:end_index]:
        #  Меняем название папки на users
        if folder.lower() == 'пользователи' or folder.lower() == '%1$d пользователей':
            name_folder = 'Users'

        # Присваиваем имя папки
        else:
            name_folder = folder

        # Если имя папки длиннее 20 символов, укорачиваем его
        if len(name_folder) > 20:
            name_folder = name_folder[:10] + '...' + name_folder[-10:]

        # Добавляем в массив кнопку с папкой
        inline_folders.append(InlineKeyboardButton(f'{name_folder}', callback_data=str(i)))
        # Добавляем папку в словарь по ее ключу
        folders_names[str(i)] = folder
        i += 1

    # Создаем маркап с кнопками папок
    folders_markup = InlineKeyboardMarkup(row_width=2).add(*inline_folders)

    # Создаем кнопки для переключения между страницами
    previous_button = InlineKeyboardButton('◀ Предыдущая страница', callback_data='previous_page')
    next_button = InlineKeyboardButton('Следующая страница ▶', callback_data='next_page')

    # Добавляем кнопки в маркап

    if page == 1 and pages > 1:
        folders_markup.row(next_button)
    elif page > 1 and pages > 1:
        folders_markup.row(previous_button)
    elif pages <= 1:
        pass
    else:
        folders_markup.row(previous_button, next_button)

    # Если путь это диск из массива
    path = path.replace('None', '')

    if comparison_path(path):
        go_back_to_drives = InlineKeyboardButton('◀ К дискам', callback_data='back_to_drives')
        folders_markup.row(go_back_to_drives)
    else:
        go_back_to_drives = InlineKeyboardButton('◀ К дискам', callback_data='back_to_drives')
        go_back_explorer = InlineKeyboardButton('◀ Назад', callback_data='back_explorer')
        folders_markup.row(go_back_explorer, go_back_to_drives)

    return all_path, page, folders_markup


def comparison_path(path):
    for i in drives_names:
        i += '\\'
        if path == i:
            return True
        else:
            pass
    return False


script_file_btns = [InlineKeyboardButton('🖥 Запустить', callback_data='run'),
                    InlineKeyboardButton('📲 Скачать', callback_data='download'),
                    InlineKeyboardButton('🗑 Удалить', callback_data='delete'),
                    InlineKeyboardButton('◀ Назад', callback_data='back_explorer')]

script_file_markup = InlineKeyboardMarkup(row_width=1).add(*script_file_btns)

