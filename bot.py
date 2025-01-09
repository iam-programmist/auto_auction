import telebot
import requests
from django.core.management import BaseCommand
from django.utils import timezone
from auto_auction.models import UserProfile, Feedback, CarSearch

API_TOKEN = 'API_KEY'
bot = telebot.TeleBot(API_TOKEN)

main_menu = [
    ["О нас", "Магазин"],
    ["Помощь и поддержка", "Найти машину"],
    ["Обратная связь", "Контактная информация"],
    ["Вход пользователя", "Наш опыт"]
]

def create_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in main_menu:
        markup.row(*row)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите одну из опций:", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "О нас")
def about(message):
    bot.send_message(message.chat.id, "Это бот, который поможет вам найти машины и получать информацию о них.")
    bot.send_message(message.chat.id, "Вы можете вернуться в главное меню.", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "Магазин")
def shop(message):
    bot.send_message(message.chat.id, "Открыть магазин: [ссылка на сайт]", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "Помощь и поддержка")
def support(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте сообщение в службу поддержки.")
    bot.register_next_step_handler(message, handle_support_message)

def handle_support_message(message):
    bot.send_message(message.chat.id, "Спасибо за ваше сообщение. Наша команда свяжется с вами в ближайшее время.")
    Feedback.objects.create(user=None, message=message.text, created_at=timezone.now())  # Сохраняем сообщение

@bot.message_handler(func=lambda message: message.text == "Найти машину")
def find_car(message):
    msg = bot.send_message(message.chat.id, "Введите название автомобиля:")
    bot.register_next_step_handler(msg, process_car_name)

def process_car_name(message):
    car_name = message.text
    msg = bot.send_message(message.chat.id, "Введите цвет автомобиля:")
    bot.register_next_step_handler(msg, process_car_color, car_name)

def process_car_color(message, car_name):
    car_color = message.text
    msg = bot.send_message(message.chat.id, "Введите модель автомобиля:")
    bot.register_next_step_handler(msg, process_car_model, car_name, car_color)

def process_car_model(message, car_name, car_color):
    car_model = message.text
    bot.send_message(message.chat.id, f"Найден автомобиль {car_name}, {car_color}, {car_model}. Ссылки:")
    bot.send_message(message.chat.id, "Ссылка на автомобиль: [ссылка]")
    bot.send_message(message.chat.id, "Нажмите 'Выбрать' или 'Дополнительные параметры'.", reply_markup=create_main_menu())

def search_car(car_name, car_color, car_model):
    url = 'http://127.0.0.1:8000/api/car-search/'
    params = {
        'car_name': car_name,
        'car_color': car_color,
        'car_model': car_model
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        cars = response.json()
        return cars
    else:
        return None

def process_car_name(message):
    car_name = message.text
    msg = bot.send_message(message.chat.id, "Введите цвет автомобиля:")
    bot.register_next_step_handler(msg, process_car_color, car_name)

def process_car_color(message, car_name):
    car_color = message.text
    msg = bot.send_message(message.chat.id, "Введите модель автомобиля:")
    bot.register_next_step_handler(msg, process_car_model, car_name, car_color)

def process_car_model(message, car_name, car_color):
    car_model = message.text
    cars = search_car(car_name, car_color, car_model)
    if cars:
        for car in cars:
            bot.send_message(message.chat.id, f"Найден автомобиль: {car['car_name']}, {car['car_color']}, {car['car_model']}.")
            bot.send_message(message.chat.id, "Ссылка на детали автомобиля: [ссылка на страницу]", reply_markup=create_main_menu())
    else:
        bot.send_message(message.chat.id, "Не удалось найти автомобили по вашему запросу.")

@bot.message_handler(func=lambda message: message.text == "Вход пользователя")
def user_login(message):
    msg = bot.send_message(message.chat.id, "Введите ваше имя пользователя:")
    bot.register_next_step_handler(msg, ask_for_password)

def ask_for_password(message):
    username = message.text
    msg = bot.send_message(message.chat.id, "Введите ваш пароль:")
    bot.register_next_step_handler(msg, validate_login, username)

def validate_login(message, username):
    password = message.text
    url = 'http://127.0.0.1:8000/api/user-login/'
    data = {'username': username, 'password': password}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        bot.send_message(message.chat.id, "Вы успешно вошли в систему!")
        bot.send_message(message.chat.id, "Что вы хотите сделать?", reply_markup=create_main_menu())
    else:
        bot.send_message(message.chat.id, "Неверное имя пользователя или пароль.")

class Command(BaseCommand):
    help = 'Run the telegram bot'

    def handle(self, *args, **kwargs):
        bot.polling()