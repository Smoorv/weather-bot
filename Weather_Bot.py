import telebot
from telebot import types
import requests
import config
from datetime import datetime

OPENWEATHER_TOKEN = config.OPENWEATHER_TOKEN
TOKEN = config.TOKEN
bot = telebot.TeleBot(TOKEN)

#Отслеживание режима работы
user_mode = {}

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🌤Текущая погода"),
        types.KeyboardButton("📆Прогноз на 5 дней")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_mode[message.chat.id] = None
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Smoorv weather!", 
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda msg: msg.text == "🌤Текущая погода")
def ask_weather(message):
    user_mode[message.chat.id] = 'current'
    markup = types.InlineKeyboardMarkup()
    btn_location = types.InlineKeyboardButton(
        "📍 Определить автоматически", 
        callback_data="request_location_current"
    )
    markup.add(btn_location)

    bot.send_message(
        message.chat.id, 
        "Введите название города или нажмите кнопку ниже:",
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == "📆Прогноз на 5 дней")
def ask_forecast(message):
    user_mode[message.chat.id] = 'forecast'
    markup = types.InlineKeyboardMarkup()
    btn_location = types.InlineKeyboardButton(
        "📍 Определить автоматически", 
        callback_data="request_location_forecast"
    )
    markup.add(btn_location)
    
    bot.send_message(
        message.chat.id, 
        "Введите город для прогноза или нажмите кнопку:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("request_location_"))
def handle_location_request(call):
    mode = call.data.split('_')[-1]
    user_mode[call.message.chat.id] = mode
    
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    ).add(
        types.KeyboardButton(
            "📍 Поделиться местоположением",
            request_location=True
        )
    )
    
    text = "Нажмите кнопку, чтобы отправить вашу геопозицию для "
    text += "текущей погоды" if mode == 'current' else "прогноза на 5 дней"
    
    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=markup
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.chat.id not in user_mode:
        return
    
    lat = message.location.latitude
    lon = message.location.longitude
    
    if user_mode[message.chat.id] == 'current':
        get_current_weather_by_coords(lat, lon, message.chat.id)
    elif user_mode[message.chat.id] == 'forecast':
        get_forecast_by_coords(lat, lon, message.chat.id)

def get_current_weather_by_coords(lat, lon, chat_id):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            weather_info = (
                f"🌤 Погода в *{data['name']}*:\n"
                f"• Температура: {data['main']['temp']}°C\n"
                f"• Ощущается как: {data['main']['feels_like']}°C\n"
                f"• Ветер: {data['wind']['speed']} м/с\n"
                f"• {data['weather'][0]['description'].capitalize()}"
            )
            
            bot.send_message(
                chat_id,
                weather_info,
                parse_mode="Markdown",
                reply_markup=main_keyboard()
            )
        else:
            bot.send_message(
                chat_id, 
                "Не удалось определить погоду",
                reply_markup=main_keyboard()
            )

    except Exception as e:
        bot.send_message(
            chat_id, 
            f"Ошибка: {str(e)}",
            reply_markup=main_keyboard()
        )

def get_forecast_by_coords(lat, lon, chat_id):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") == "200":
            forecast_info = f"📆 Прогноз на 5 дней для вашего местоположения:\n\n"
            
            prev_date = ""
            for day in data['list']:
                current_date = day['dt_txt'].split()[0]
                if current_date != prev_date and '12:00:00' in day['dt_txt']:
                    forecast_info += (
                        f"📅 {datetime.strptime(current_date, '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
                        f"🌡 Днём: {day['main']['temp']}°C\n"
                        f"☁️ {day['weather'][0]['description']}\n"
                        f"💨 Ветер: {day['wind']['speed']} м/с\n"
                        f"💧 Влажность: {day['main']['humidity']}%\n\n"
                    )
                    prev_date = current_date
            
            bot.send_message(
                chat_id, 
                forecast_info, 
                reply_markup=main_keyboard()
            )
        else:
            error = data.get("message", "Ошибка API")
            bot.send_message(
                chat_id, 
                f"Ошибка: {error}", 
                reply_markup=main_keyboard()
            )

    except Exception as e:
        bot.send_message(
            chat_id, 
            f"Ошибка: {str(e)}", 
            reply_markup=main_keyboard()
        )

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if message.chat.id not in user_mode:
        return
    
    if user_mode[message.chat.id] == 'current':
        get_current_weather_by_city(message)
    elif user_mode[message.chat.id] == 'forecast':
        get_forecast_by_city(message)

def get_current_weather_by_city(message):
    city = message.text.strip()
    if not city:
        bot.send_message(
            message.chat.id,
            "Укажите город:",
            reply_markup=main_keyboard()
        )
        return
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            weather = (
                f"🌆 Город: {data['name']}\n"
                f"🌡 Температура: {data['main']['temp']}°C\n"
                f"💨 Ветер: {data['wind']['speed']} м/с\n"
                f"☁️ Погода: {data['weather'][0]['description']}\n"
                f"💧 Влажность: {data['main']['humidity']}%"
            )
            bot.send_message(
                message.chat.id, 
                weather, 
                reply_markup=main_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id, 
                "Город не найден. Попробуй ещё раз!", 
                reply_markup=main_keyboard()
            )
    
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            "Ошибка! Попробуй позже.", 
            reply_markup=main_keyboard()
        )

def get_forecast_by_city(message):
    city = message.text.strip()
    if not city:
        bot.send_message(
            message.chat.id, 
            "Укажи город!", 
            reply_markup=main_keyboard()
        )
        return

    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") == "200":
            forecast_info = f"📆 Прогноз на 5 дней для города {city}:\n\n"
            
            prev_date = ""
            for day in data['list']:
                current_date = day['dt_txt'].split()[0]
                if current_date != prev_date and '12:00:00' in day['dt_txt']:
                    forecast_info += (
                        f"📅 {datetime.strptime(current_date, '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
                        f"🌡 Днём: {day['main']['temp']}°C\n"
                        f"☁️ {day['weather'][0]['description']}\n"
                        f"💨 Ветер: {day['wind']['speed']} м/с\n"
                        f"💧 Влажность: {day['main']['humidity']}%\n\n"
                    )
                    prev_date = current_date
            
            bot.send_message(
                message.chat.id, 
                forecast_info, 
                reply_markup=main_keyboard()
            )
        else:
            error = data.get("message", "Ошибка API")
            bot.send_message(
                message.chat.id, 
                f"Ошибка: {error}", 
                reply_markup=main_keyboard()
            )

    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"Ошибка: {str(e)}", 
            reply_markup=main_keyboard()
        )

if __name__ == "__main__":
    print("Бот запущен")
    bot.polling(none_stop=True)