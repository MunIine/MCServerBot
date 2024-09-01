import ctypes
import threading
import configparser
import asyncio
import signal
import os
import sys
import win32gui
import win32con
from PIL import Image
from colorama import init, Fore
from datetime import datetime
from pystray import Icon, MenuItem, Menu
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup

from server_utils import check

# Создание изображения для иконки
def create_image():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("assets")

    path = os.path.join(base_path, "icon.ico")
    return Image.open(path)

# Скрытие консоли
def hide_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Показ консоли
def show_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)

# Функция для выхода из приложения
def quit_app(icon):
    icon.stop()
    os.kill(os.getpid(), signal.SIGTERM)

# Трей-меню с опциями
def setup_tray():
    icon = Icon('tray_icon')
    icon.icon = create_image()
    icon.menu = Menu(
        MenuItem('Показать консоль', show_console),
        MenuItem('Скрыть консоль', hide_console),
        MenuItem('Выход', quit_app)
    )
    icon.run()


#Бот
init(autoreset=True)
def log(msg):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]", end=" ")
    print(msg)

def log_msg(msg, message):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]", end=" ")
    print(Fore.GREEN + f"[{msg}]", end=" ")
    print(f"@{message.from_user.username}, {message.from_user.id}")

try:
    with open("config.ini", "r") as file:
        config = configparser.ConfigParser()
        config.read_file(file)
        TOKEN = config["Settings"]["TOKEN"]
        PATH = config["Settings"]["PATH"]
        PASSWORD = config["Settings"]["PASSWORD"]
        log("Настройки успешно загружены")

except FileNotFoundError:
    log("Файл конфигурации не найден")
    log("Запущен мастер настройки")
    TOKEN = input(Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]{Fore.WHITE} Введите token бота: ").strip()
    PATH = os.path.abspath(input(Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]{Fore.WHITE} Введите путь до файла запуска сервера: ").strip())
    PASSWORD = input(Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]{Fore.WHITE} Введите пароль: ").strip()
    log("Настройка завершена")
    log("Cохранённые настройки можно изменить в файле config.ini")

    with open("config.ini", "w") as file:
        file.writelines([
            "[Settings]\n",
            ";Telegram bot token\n"
            f"TOKEN = {TOKEN}\n",
            ";Path to server run.bat\n"
            f"PATH = {PATH}\n",
            ";Session password\n"
            f"PASSWORD = {PASSWORD}"
        ])

bot = Bot(token=TOKEN)
dp = Dispatcher()
log("Бот запущен\n")

class Form(StatesGroup):
    password = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    log_msg("/start", message)
    await message.answer("Добро пожаловать в бота для работы с серверами")
    await message.answer("Введите пароль от сессии")
    await state.set_state(Form.password)

@dp.message(Form.password)
async def process_message(message: types.Message, state: FSMContext):
    if PASSWORD == message.text.strip():
        kb = [
            [types.KeyboardButton(text="Запустить"), 
            types.KeyboardButton(text="Статус"), 
            types.KeyboardButton(text="Остановить")]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
        await state.update_data(password=message.text)
        await state.clear()
        log_msg("Password correct", message)
        await message.reply("Сессия запущена", reply_markup=keyboard)
    else:
        log_msg("Password incorrect", message)
        await message.reply("Не правильный пароль")


@dp.message(F.text.lower() == "запустить")
async def turn_on(message: types.Message):
    log_msg("/turn_on", message)
    cmd = check(PATH)
    if cmd:
        await message.answer("Сервер уже запущен")
        return
    
    os.startfile(PATH)
    await message.answer("Сервер запущен")

@dp.message(F.text.lower() == "остановить")
async def turn_off(message: types.Message):
    log_msg("/turn_off", message)
    cmd = check(PATH)
    if not cmd:
        await message.answer("Сервер уже остановлен")
        return

    win32gui.PostMessage(cmd, win32con.WM_CLOSE, 0, 0)
    win32gui.PostMessage(cmd, win32con.WM_CLOSE, 0, 0)

    await message.answer("Сервер остановлен")

@dp.message(F.text.lower() == "статус")
async def status(message: types.Message):
    log_msg("/status", message)
    cmd = check(PATH)
    if cmd:
        await message.reply("Сервер онлайн")
        return
    
    await message.answer("Сервер офлайн")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск системного трея в отдельном потоке
    tray_thread = threading.Thread(target=setup_tray)
    tray_thread.start()
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGTERM)