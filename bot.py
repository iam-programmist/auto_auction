import os
import django
import telebot
from telebot import types
import requests
from django.utils import timezone
from dotenv import load_dotenv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from auto_auction.models import Feedback

load_dotenv('./.env')

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

main_menu = [
    ("О нас", "about"),
    ("Магазин", "shop"),
    ("Помощь и поддержка", "support"),
    ("Найти машину", "find_car"),
    ("Обратная связь", "feedback"),
    ("Контактная информация", "contact"),
    ("Вход пользователя", "user_login"),
    ("Наш опыт", "experience")
]

def create_inline_main_menu():
    markup = types.InlineKeyboardMarkup()
    for text, callback_data in main_menu:
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback_data))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "Добро пожаловать! Выберите одну из опций:", 
        reply_markup=create_inline_main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    bot.send_message(call.message.chat.id, "Это бот, который поможет вам найти машины и получать информацию о них.")

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop(call):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Открыть магазин", url="http://127.0.0.1:8000/api/shop/")
    markup.add(button)
    bot.send_message(call.message.chat.id, "Открыть магазин:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    bot.send_message(call.message.chat.id, "Пожалуйста, отправьте сообщение в службу поддержки.")
    bot.register_next_step_handler(call.message, handle_support_message)

def handle_support_message(message):
    try:
        Feedback.objects.create(user=None, message=message.text, created_at=timezone.now())
        bot.send_message(message.chat.id, "Спасибо за ваше сообщение. Наша команда свяжется с вами в ближайшее время.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "find_car")
def find_car(call):
    msg = bot.send_message(call.message.chat.id, "Введите название автомобиля:")
    bot.register_next_step_handler(msg, process_car_name)

def process_car_name(message):
    car_name = message.text
    msg = bot.send_message(message.chat.id, "Введите цвет автомобиля:")
    bot.register_next_step_handler(msg, lambda m: process_car_color(m, car_name))

def process_car_color(message, car_name):
    car_color = message.text
    msg = bot.send_message(message.chat.id, "Введите модель автомобиля:")
    bot.register_next_step_handler(msg, lambda m: process_car_model(m, car_name, car_color))

def process_car_model(message, car_name, car_color):
    car_model = message.text
    try:
        cars = search_car(car_name, car_color, car_model)
        if cars:
            for car in cars:
                bot.send_message(
                    message.chat.id, 
                    f"Найден автомобиль: {car['car_name']}, {car['car_color']}, {car['car_model']}."
                )
        else:
            bot.send_message(message.chat.id, "Не удалось найти автомобили по вашему запросу.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

def search_car(car_name, car_color, car_model):
    url = 'http://127.0.0.1:8000/api/car-search/'
    params = {'car_name': car_name, 'car_color': car_color, 'car_model': car_model}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

@bot.callback_query_handler(func=lambda call: call.data == "user_login")
def user_login(call):
    msg = bot.send_message(call.message.chat.id, "Введите ваше имя пользователя:")
    bot.register_next_step_handler(msg, ask_for_password)

def ask_for_password(message):
    username = message.text
    msg = bot.send_message(message.chat.id, "Введите ваш пароль:")
    bot.register_next_step_handler(msg, lambda m: validate_login(m, username))

def validate_login(message, username):
    password = message.text
    url = 'http://127.0.0.1:8000/api/user-login/'
    data = {'username': username, 'password': password}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        bot.send_message(message.chat.id, "Вы успешно вошли в систему!")
    except requests.RequestException:
        bot.send_message(message.chat.id, "Неверное имя пользователя или пароль.")

if __name__ == '__main__':
    bot.infinity_polling()
