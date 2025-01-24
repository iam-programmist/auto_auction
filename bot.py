import os
import django
import telebot
from telebot import types
import requests
from django.utils import timezone
from dotenv import load_dotenv
from server.settings import get_secret

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from auto_auction.models import Feedback

load_dotenv('./.env')

API_TOKEN = get_secret('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

user_language = {}

main_menu_ru = [
    ("О нас", "about"),
    ("Магазин", "shop"),
    ("Помощь и поддержка", "support"),
    ("Найти машину", "find_car"),
    ("Обратная связь", "feedback"),
    ("Контактная информация", "contact"),
    ("Вход пользователя", "user_login"),
    ("Наш опыт", "experience")
]

main_menu_tj = [
    ("Дар бораи мо", "about"),
    ("Магоза", "shop"),
    ("Мадад ва дастгири", "support"),
    ("Ёфтани мошин", "find_car"),
    ("Равобит бо мо", "feedback"),
    ("Иттилооти контакт", "contact"),
    ("Вориди корбар", "user_login"),
    ("Тачрибаи мо", "experience")
]

def create_inline_main_menu(language="ru"):
    menu = main_menu_ru if language == "ru" else main_menu_tj
    markup = types.InlineKeyboardMarkup()
    for text, callback_data in menu:
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback_data))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Русский", "Тоҷикӣ")
    bot.send_message(
        message.chat.id,
        "Пожалуйста, выберите язык / Лутфан забонро интихоб кунед:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in ["Русский", "Тоҷикӣ"])
def set_language(message):
    if message.text == "Русский":
        user_language[message.chat.id] = "ru"
        bot.send_message(
            message.chat.id,
            "Добро пожаловать! Выберите одну из опций:",
            reply_markup=create_inline_main_menu("ru")
        )
    elif message.text == "Тоҷикӣ":
        user_language[message.chat.id] = "tj"
        bot.send_message(
            message.chat.id,
            "Хуш омадед! Як опсияро интихоб кунед:",
            reply_markup=create_inline_main_menu("tj")
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    language = user_language.get(call.message.chat.id, "ru")
    
    if call.data == "about":
        text = {
            "ru": "Это бот, который поможет вам найти машины и получать информацию о них.",
            "tj": "Ин ботест, ки ба шумо ёрдам мекунад, ки мошинҳоро пайдо кунед ва маълумотро дар бораи онҳо гиред."
        }.get(language)
        bot.send_message(call.message.chat.id, text)

    elif call.data == "shop":
        text = {
            "ru": "Открыть магазин:",
            "tj": "Кушодани магоза:"
        }.get(language)
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text=text, url="http://127.0.0.1:8000/api/shop/")
        markup.add(button)
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

    elif call.data == "support":
        text = {
            "ru": "Пожалуйста, отправьте сообщение в службу поддержки.",
            "tj": "Лутфан, пахш кунед, ки муроҷиат кунед ба хидмати дастгирии мо."
        }.get(language)
        bot.send_message(call.message.chat.id, text)
        bot.register_next_step_handler(call.message, handle_support_message)

def handle_support_message(message):
    language = user_language.get(message.chat.id, "ru")
    try:
        Feedback.objects.create(user=None, message=message.text, created_at=timezone.now())
        text = {
            "ru": "Спасибо за ваше сообщение. Наша команда свяжется с вами в ближайшее время.",
            "tj": "Ташаккур барои паёматон. Тимамон бо шумо дар замони наздик тамос мегирад."
        }.get(language)
        bot.send_message(message.chat.id, text)
    except Exception as e:
        error_text = {
            "ru": f"Произошла ошибка: {e}",
            "tj": f"Хатоги рӯй дод: {e}"
        }.get(language)
        bot.send_message(message.chat.id, error_text)

@bot.callback_query_handler(func=lambda call: call.data == "find_car")
def find_car(call):
    language = user_language.get(call.message.chat.id, "ru")
    messages = {
        "ru": "Введите название автомобиля:",
        "tj": "Номи мошинро ворид кунед:"
    }
    msg = bot.send_message(call.message.chat.id, messages[language])
    bot.register_next_step_handler(msg, process_car_name)

def process_car_name(message):
    car_name = message.text
    language = user_language.get(message.chat.id, "ru")
    messages = {
        "ru": "Введите цвет автомобиля:",
        "tj": "Ранги мошинро ворид кунед:"
    }
    msg = bot.send_message(message.chat.id, messages[language])
    bot.register_next_step_handler(msg, lambda m: process_car_color(m, car_name))

def process_car_color(message, car_name):
    car_color = message.text
    language = user_language.get(message.chat.id, "ru")
    messages = {
        "ru": "Введите модель автомобиля:",
        "tj": "Нусхаи мошинро ворид кунед:"
    }
    msg = bot.send_message(message.chat.id, messages[language])
    bot.register_next_step_handler(msg, lambda m: process_car_model(m, car_name, car_color))

def process_car_model(message, car_name, car_color):
    car_model = message.text
    language = user_language.get(message.chat.id, "ru")
    try:
        cars = search_car(car_name, car_color, car_model)
        if cars:
            for car in cars:
                messages = {
                    "ru": f"Найден автомобиль: {car['car_name']}, {car['car_color']}, {car['car_model']}.",
                    "tj": f"Мошини пайдо шуд: {car['car_name']}, {car['car_color']}, {car['car_model']}."
                }
                bot.send_message(message.chat.id, messages[language])
        else:
            no_cars_messages = {
                "ru": "Не удалось найти автомобили по вашему запросу.",
                "tj": "Мо ягон мошинеро пайдо карда натавонистем, ки ба дархости шумо мувофиқат кунад."
            }
            bot.send_message(message.chat.id, no_cars_messages[language])
    except Exception as e:
        error_messages = {
            "ru": f"Произошла ошибка: {e}",
            "tj": f"Хатоги рӯй дод: {e}"
        }
        bot.send_message(message.chat.id, error_messages[language])

def search_car(car_name, car_color, car_model, language="ru"):
    url = "http://127.0.0.1:8000/api/car-search/"
    data = {
        "name": car_name,
        "color": car_color,
        "model": car_model
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_messages = {
            "ru": f"Произошла ошибка при запросе к API: {e}",
            "tj": f"Хатоги ҳангоми ирсоли дархост ба API: {e}"
        }
        print(error_messages.get(language, error_messages["ru"]))
        return []

@bot.callback_query_handler(func=lambda call: call.data == "user_login")
def user_login(call):
    language = user_language.get(call.message.chat.id, "ru")
    messages = {
        "ru": "Введите ваше имя пользователя:",
        "tj": "Номи корбарии худро ворид кунед:"
    }
    msg = bot.send_message(call.message.chat.id, messages[language])
    bot.register_next_step_handler(msg, ask_for_password)

def ask_for_password(message):
    username = message.text
    language = user_language.get(message.chat.id, "ru")
    messages = {
        "ru": "Введите ваш пароль:",
        "tj": "Пароли корбарии худро ворид кунед:"
    }
    msg = bot.send_message(message.chat.id, messages[language])
    bot.register_next_step_handler(msg, lambda m: validate_login(m, username))

def validate_login(message, username):
    password = message.text
    url = 'http://127.0.0.1:8000/api/user-login/'
    data = {'username': username, 'password': password}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        language = user_language.get(message.chat.id, "ru")
        success_messages = {
            "ru": "Вы успешно вошли в систему!",
            "tj": "Шумо муваффақона дар система ворид шудед!"
        }
        bot.send_message(message.chat.id, success_messages[language])
    except requests.RequestException:
        error_messages = {
            "ru": "Неверное имя пользователя или пароль.",
            "tj": "Номи корбарии шумо ё пароли шумо хато аст!"
        }
        bot.send_message(message.chat.id, error_messages[language])


if __name__ == '__main__':
    bot.infinity_polling()
