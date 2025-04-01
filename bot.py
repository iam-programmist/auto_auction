import os
import django
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
import requests
from io import BytesIO
from django.utils import timezone
from secret import get_secret
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from auto_auction.models import Feedback

API_TOKEN = get_secret('API_TOKEN')
WEBHOOK_URL = get_secret('WEBHOOK_URL')

if not API_TOKEN:
    raise ValueError('API токен не найден')
if not WEBHOOK_URL:
    raise ValueError('WEBHOOK_URL не задан')

bot = telebot.TeleBot(API_TOKEN)
user_language = {}
user_sessions = {}

def get_cars():
    return [
        {
            "name": "Toyota Camry",
            "color": "White",
            "model": "2020",
            "photo_url": "https://avanta-avto-credit.ru/upload/resize_cache/iblock/31b/600_600_040cd750bba9870f18aada2478b24840a/xbw7atcn1ytuoitzvmz5wykypir21nq1.png.pagespeed.ce.Jkb-dsgAQ6.png",
            "info_url": "https://ru.wikipedia.org/wiki/Toyota_Camry"
        },
        {
            "name": "Ford Mustang",
            "color": "Red",
            "model": "2017",
            "photo_url": "https://imgd.aeplcdn.com/664x374/cw/ec/23766/Ford-Mustang-Exterior-126883.jpg?wm=0&q=80",
            "info_url": "https://ru.wikipedia.org/wiki/Ford_Mustang"
        },
        {
            "name": "Brabus 900",
            "color": "Black",
            "model": "2022",
            "photo_url": "https://daily-motor.ru/wp-content/uploads/2023/04/Brabus-900-Superblack-official-3.jpg",
            "info_url": "https://ru.wikipedia.org/wiki/Mercedes-Benz_G-%D0%BA%D0%BB%D0%B0%D1%81%D1%81"
        }
    ]

def create_collage(url1, url2):
    img1 = Image.open(BytesIO(requests.get(url1).content))
    img2 = Image.open(BytesIO(requests.get(url2).content))

    target_height = max(img1.height, img2.height)
    img1 = img1.resize((int(img1.width * target_height / img1.height), target_height))
    img2 = img2.resize((int(img2.width * target_height / img2.height), target_height))

    collage_width = img1.width + img2.width
    collage = Image.new('RGB', (collage_width, target_height))
    collage.paste(img1, (0, 0))
    collage.paste(img2, (img1.width, 0))

    collage_bytes = BytesIO()
    collage.save(collage_bytes, format="JPEG")
    collage_bytes.seek(0)

    return collage_bytes

@bot.message_handler(commands=['start'])
def start(message):
    language = user_language.get(message.chat.id, "ru")
    cars = get_cars()

    first_car = cars[0]
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(first_car['name'], url=first_car["info_url"])
    markup.add(button)

    bot.send_photo(
        message.chat.id,
        first_car["photo_url"],
        caption=f"{first_car['name']}, {first_car['color']}, {first_car['model']}",
        reply_markup=markup
    )

    collage_bytes = create_collage(cars[1]["photo_url"], cars[2]["photo_url"])
    
    caption = f"{cars[1]['name']}, {cars[1]['color']}, {cars[1]['model']} - {cars[2]['name']}, {cars[2]['color']}, {cars[2]['model']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(cars[1]['name'], url=cars[1]["info_url"]),
        types.InlineKeyboardButton(cars[2]['name'], url=cars[2]["info_url"])
    )

    bot.send_photo(
        message.chat.id,
        collage_bytes,
        caption=caption,
        reply_markup=markup
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    find_car_button = types.InlineKeyboardButton(
        "Найти машину",
        callback_data="find_car"
    )
    markup.add(find_car_button)

    bot.send_message(
        message.chat.id,
        "Выберите действие:" if language == "ru" else "Амалро интихоб кунед:",
        reply_markup=markup
    )
        
@bot.message_handler(commands=['find_car'])
def find_car(message):
    language = user_language.get(message.chat.id, "ru")
    messages = {
        "ru": "Введите название автомобиля:",
        "tj": "Номи мошинро ворид кунед:"
    }
    msg = bot.send_message(message.chat.id, messages[language])
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

def register_user(message):
    bot.send_message(message.chat.id, "Введите имя пользователя:")
    bot.register_next_step_handler(message, ask_password)

def ask_password(message):
    username = message.text
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, lambda msg: complete_registration(msg, username))

def complete_registration(message, username):
    password = message.text
    url = 'https://auto-auction-2025.el.r.appspot.com/api/register/'
    data = {'username': username, 'password': password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        bot.send_message(message.chat.id, "Регистрация успешна!")
    except requests.RequestException:
        bot.send_message(message.chat.id, "Ошибка регистрации. Попробуйте позже.")

@bot.message_handler(commands=['user_login'])
def user_login(message):
    language = user_language.get(message.chat.id, "ru")
    messages = {
        "ru": "Введите ваше имя пользователя:",
        "tj": "Номи корбарии худро ворид кунед:"
    }
    msg = bot.send_message(message.chat.id, messages[language])
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

def logout_user(message):
    if message.chat.id in user_sessions:
        del user_sessions[message.chat.id]
        bot.send_message(message.chat.id, "Вы успешно вышли из системы.")
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы.")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != f"/webhook/{API_TOKEN}":
            self.send_response(403)
            self.end_headers()
            return
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            update = telebot.types.Update.de_json(post_data)
            bot.process_new_updates([update])
            self.send_response(200)
        except Exception as e:
            print(f'Ошибка обработки вебхука: {e}')
            self.send_response(500)
        finally:
            self.send_header('Content-type', 'application/json')
            self.end_headers()

def clear_updates_queue():
    offset = None
    while True:
        updates = bot.get_updates(offset=offset, limit=100, timeout=0)
        if not updates:
            break
        offset = max(update.update_id for update in updates) + 1

if __name__ == '__main__':
    try:
        use_webhook = os.getenv('USE_WEBHOOK', 'False') == 'True'
        if use_webhook:
            bot.remove_webhook()
            bot.set_webhook(url=f"{WEBHOOK_URL}/webhook/{API_TOKEN}")
            
            server_address = ('', int(os.getenv('PORT', 8080)))
            httpd = HTTPServer(server_address, WebhookHandler)
            print(f"Запуск вебхука на {server_address}")
            httpd.serve_forever()
        else:
            bot.remove_webhook()
            clear_updates_queue()
            time.sleep(3)
            print("Запуск бота в режиме polling...")
            bot.infinity_polling()
    except Exception as e:
        print(f'Критическая ошибка: {e}')









# import os
# import django
# import telebot
# from telebot import types
# from http.server import BaseHTTPRequestHandler, HTTPServer
# import requests
# from django.utils import timezone
# from secret import get_secret

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
# django.setup()

# from auto_auction.models import Feedback

# API_TOKEN = get_secret('API_TOKEN')
# WEBHOOK_URL = get_secret('WEBHOOK_URL')

# if not API_TOKEN:
#     raise ValueError('API токен не найден')
# if not WEBHOOK_URL:
#     raise ValueError('WEBHOOK_URL не задан')

# bot = telebot.TeleBot(API_TOKEN)
# user_language = {}
# user_sessions = {}

# main_menu_ru = [
#     ("О нас 🏢", "about"),
#     ("Магазин 🛒", "shop"),
#     ("Помощь и поддержка 🆘", "support"),
#     ("Найти машину 🚗", "find_car"),
#     ("Обратная связь 💬", "feedback"),
#     ("Контактная информация 📞", "contact"),
#     ("Вход пользователя 🔑", "user_login"),
#     ("Наш опыт 🎓", "experience"),
#     ("Регистрация 📝", "register"),
#     ("Выход 🚪", "logout")
# ]

# main_menu_tj = [
#     ("Дар бораи мо 🏢", "about"),
#     ("Магоза 🛒", "shop"),
#     ("Мадад ва дастгири 🆘", "support"),
#     ("Ёфтани мошин 🚗", "find_car"),
#     ("Равобит бо мо 💬", "feedback"),
#     ("Иттилооти контакт 📞", "contact"),
#     ("Вориди корбар 🔑", "user_login"),
#     ("Тачрибаи мо 🎓", "experience"),
#     ("Сабти ном 📝", "register"),
#     ("Баромад 🚪", "logout")
# ]

# def create_inline_main_menu(language="ru"):
#     menu = main_menu_ru if language == "ru" else main_menu_tj
#     markup = types.InlineKeyboardMarkup()
#     for text, callback_data in menu:
#         markup.add(types.InlineKeyboardButton(text=text, callback_data=callback_data))
#     return markup

# @bot.message_handler(commands=['start'])
# def start(message):
#     markup = types.InlineKeyboardMarkup()
#     btn_ru = types.InlineKeyboardButton(text="🇷🇺 Русский ", callback_data="ru")
#     btn_tj = types.InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="tj")
#     markup.add(btn_ru, btn_tj)
#     bot.send_message(
#         message.chat.id,
#         "Пожалуйста, выберите язык / Лутфан забонро интихоб кунед:",
#         reply_markup=markup
#     )

# @bot.callback_query_handler(func=lambda call: call.data in ["ru", "tj"])
# def set_language(call):
#     if call.data == "ru":
#         user_language[call.message.chat.id] = "ru"
#         bot.send_message(
#             call.message.chat.id,
#             "Добро пожаловать! Выберите одну из опций:",
#             reply_markup=create_inline_main_menu("ru")
#         )
#     elif call.data == "tj":
#         user_language[call.message.chat.id] = "tj"
#         bot.send_message(
#             call.message.chat.id,
#             "Хуш омадед! Як опсияро интихоб кунед:",
#             reply_markup=create_inline_main_menu("tj")
#         )


# @bot.callback_query_handler(func=lambda call: True)
# def handle_callbacks(call):
#     language = user_language.get(call.message.chat.id, "ru")
    
#     if call.data == "about":
#         text = {
#             "ru": "Это бот, который поможет вам найти машины и получать информацию о них.",
#             "tj": "Ин ботест, ки ба шумо ёрдам мекунад, ки мошинҳоро пайдо кунед ва маълумотро дар бораи онҳо гиред."
#         }.get(language)
#         bot.send_message(call.message.chat.id, text)

#     elif call.data == "shop":
#         text = {
#             "ru": "Открыть магазин:",
#             "tj": "Кушодани магоза:"
#         }.get(language)
#         markup = types.InlineKeyboardMarkup()
#         button = types.InlineKeyboardButton(text=text, url="https://auto-auction-2025.el.r.appspot.com/api/shop/")
#         markup.add(button)
#         bot.send_message(call.message.chat.id, text, reply_markup=markup)

#     elif call.data == "support":
#         text = {
#             "ru": "Пожалуйста, отправьте сообщение в службу поддержки.",
#             "tj": "Лутфан, пахш кунед, ки муроҷиат кунед ба хидмати дастгирии мо."
#         }.get(language)
#         bot.send_message(call.message.chat.id, text)
#         bot.register_next_step_handler(call.message, handle_support_message)

#     elif call.data == "contact":
#         text = {
#             "ru": "Контактная информация:\n📞 Телефон: +992000444891\n🖊 Telegram: @apdyu\n🌍 Веб-сайт: apramz.com",
#             "tj": "Иттилооти контакт:\n📞 Телефон: +992000444891\n🖊 Telegram: @apdyu\n🌍 Веб-сайт: apramz.com"
#         }.get(language)
#         bot.send_message(call.message.chat.id, text)
    
#     elif call.data == "experience":
#         text = {
#             "ru": "Наш опыт включает более 10 лет работы в автомобильной индустрии. Мы помогли тысячам клиентов найти их идеальные автомобили.",
#             "tj": "Таҷрибаи мо зиёда аз 10 солро дар бар мегирад дар соҳаи мошинсозӣ. Мо ба ҳазорҳо муштарӣ кӯмак кардем, ки мошини орзушонро пайдо кунанд."
#         }.get(language)
#         bot.send_message(call.message.chat.id, text)

#     elif call.data == "register":
#         register_user(call.message)

#     elif call.data == "logout":
#         logout_user(call.message)

# def handle_support_message(message):
#     language = user_language.get(message.chat.id, "ru")
#     try:
#         Feedback.objects.create(user=None, message=message.text, created_at=timezone.now())
#         text = {
#             "ru": "Спасибо за ваше сообщение. Наша команда свяжется с вами в ближайшее время.",
#             "tj": "Ташаккур барои паёматон. Тимамон бо шумо дар замони наздик тамос мегирад."
#         }.get(language)
#         bot.send_message(message.chat.id, text)
#     except Exception as e:
#         error_text = {
#             "ru": f"Произошла ошибка: {e}",
#             "tj": f"Хатоги рӯй дод: {e}"
#         }.get(language)
#         bot.send_message(message.chat.id, error_text)

# @bot.callback_query_handler(func=lambda call: call.data == "find_car")
# def find_car(call):
#     language = user_language.get(call.message.chat.id, "ru")
#     messages = {
#         "ru": "Введите название автомобиля:",
#         "tj": "Номи мошинро ворид кунед:"
#     }
#     msg = bot.send_message(call.message.chat.id, messages[language])
#     bot.register_next_step_handler(msg, process_car_name)

# def process_car_name(message):
#     car_name = message.text
#     language = user_language.get(message.chat.id, "ru")
#     messages = {
#         "ru": "Введите цвет автомобиля:",
#         "tj": "Ранги мошинро ворид кунед:"
#     }
#     msg = bot.send_message(message.chat.id, messages[language])
#     bot.register_next_step_handler(msg, lambda m: process_car_color(m, car_name))

# def process_car_color(message, car_name):
#     car_color = message.text
#     language = user_language.get(message.chat.id, "ru")
#     messages = {
#         "ru": "Введите модель автомобиля:",
#         "tj": "Нусхаи мошинро ворид кунед:"
#     }
#     msg = bot.send_message(message.chat.id, messages[language])
#     bot.register_next_step_handler(msg, lambda m: process_car_model(m, car_name, car_color))

# def process_car_model(message, car_name, car_color):
#     car_model = message.text
#     language = user_language.get(message.chat.id, "ru")
#     try:
#         cars = search_car(car_name, car_color, car_model)
#         if cars:
#             for car in cars:
#                 messages = {
#                     "ru": f"Найден автомобиль: {car['car_name']}, {car['car_color']}, {car['car_model']}.",
#                     "tj": f"Мошини пайдо шуд: {car['car_name']}, {car['car_color']}, {car['car_model']}."
#                 }
#                 bot.send_message(message.chat.id, messages[language])
#         else:
#             no_cars_messages = {
#                 "ru": "Не удалось найти автомобили по вашему запросу.",
#                 "tj": "Мо ягон мошинеро пайдо карда натавонистем, ки ба дархости шумо мувофиқат кунад."
#             }
#             bot.send_message(message.chat.id, no_cars_messages[language])
#     except Exception as e:
#         error_messages = {
#             "ru": f"Произошла ошибка: {e}",
#             "tj": f"Хатоги рӯй дод: {e}"
#         }
#         bot.send_message(message.chat.id, error_messages[language])

# def search_car(car_name, car_color, car_model, language="ru"):
#     url = "http://127.0.0.1:8000/api/car-search/"
#     data = {
#         "name": car_name,
#         "color": car_color,
#         "model": car_model
#     }
#     try:
#         response = requests.post(url, json=data)
#         response.raise_for_status()
#         return response.json()
#     except requests.RequestException as e:
#         error_messages = {
#             "ru": f"Произошла ошибка при запросе к API: {e}",
#             "tj": f"Хатоги ҳангоми ирсоли дархост ба API: {e}"
#         }
#         print(error_messages.get(language, error_messages["ru"]))
#         return []

# def register_user(message):
#     bot.send_message(message.chat.id, "Введите имя пользователя:")
#     bot.register_next_step_handler(message, ask_password)

# def ask_password(message):
#     username = message.text
#     bot.send_message(message.chat.id, "Введите пароль:")
#     bot.register_next_step_handler(message, lambda msg: complete_registration(msg, username))

# def complete_registration(message, username):
#     password = message.text
#     url = 'https://auto-auction-2025.el.r.appspot.com/api/register/'
#     data = {'username': username, 'password': password}
#     try:
#         response = requests.post(url, json=data)
#         response.raise_for_status()
#         bot.send_message(message.chat.id, "Регистрация успешна!")
#     except requests.RequestException:
#         bot.send_message(message.chat.id, "Ошибка регистрации. Попробуйте позже.")

# @bot.callback_query_handler(func=lambda call: call.data == "user_login")
# def user_login(call):
#     language = user_language.get(call.message.chat.id, "ru")
#     messages = {
#         "ru": "Введите ваше имя пользователя:",
#         "tj": "Номи корбарии худро ворид кунед:"
#     }
#     msg = bot.send_message(call.message.chat.id, messages[language])
#     bot.register_next_step_handler(msg, ask_for_password)

# def ask_for_password(message):
#     username = message.text
#     language = user_language.get(message.chat.id, "ru")
#     messages = {
#         "ru": "Введите ваш пароль:",
#         "tj": "Пароли корбарии худро ворид кунед:"
#     }
#     msg = bot.send_message(message.chat.id, messages[language])
#     bot.register_next_step_handler(msg, lambda m: validate_login(m, username))

# def validate_login(message, username):
#     password = message.text
#     url = 'http://127.0.0.1:8000/api/user-login/'
#     data = {'username': username, 'password': password}
#     try:
#         response = requests.post(url, data=data)
#         response.raise_for_status()
#         language = user_language.get(message.chat.id, "ru")
#         success_messages = {
#             "ru": "Вы успешно вошли в систему!",
#             "tj": "Шумо муваффақона дар система ворид шудед!"
#         }
#         bot.send_message(message.chat.id, success_messages[language])
#     except requests.RequestException:
#         error_messages = {
#             "ru": "Неверное имя пользователя или пароль.",
#             "tj": "Номи корбарии шумо ё пароли шумо хато аст!"
#         }
#         bot.send_message(message.chat.id, error_messages[language])

# def logout_user(message):
#     if message.chat.id in user_sessions:
#         del user_sessions[message.chat.id]
#         bot.send_message(message.chat.id, "Вы успешно вышли из системы.")
#     else:
#         bot.send_message(message.chat.id, "Вы не авторизованы.")

# class WebhookHandler(BaseHTTPRequestHandler):
#     def do_POST(self):
#         if self.path != f"/webhook/{API_TOKEN}":
#             self.send_response(403)
#             self.end_headers()
#             return
        
#         try:
#             content_length = int(self.headers['Content-Length'])
#             post_data = self.rfile.read(content_length).decode('utf-8')
#             update = telebot.types.Update.de_json(post_data)
#             bot.process_new_updates([update])
#             self.send_response(200)
#         except Exception as e:
#             print(f'Ошибка обработки вебхука: {e}')
#             self.send_response(500)
#         finally:
#             self.send_header('Content-type', 'application/json')
#             self.end_headers()

# if __name__ == '__main__':
#     try:
#         use_webhook = os.getenv('USE_WEBHOOK', 'False') == 'True'
#         if use_webhook:
#             bot.remove_webhook()
#             bot.set_webhook(url=f"{WEBHOOK_URL}/webhook/{API_TOKEN}")
            
#             server_address = ('', int(os.getenv('PORT', 8080)))
#             httpd = HTTPServer(server_address, WebhookHandler)
#             print(f"Запуск вебхука на {server_address}")
#             httpd.serve_forever()
#         else:
#             bot.remove_webhook()
#             print("Запуск бота в режиме polling...")
#             bot.infinity_polling()
#     except Exception as e:
#         print(f'Критическая ошибка: {e}')