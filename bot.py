import os
import math
import json
import threading
from flask import Flask
import telebot
from telebot.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)

# --- Настройки из переменных окружения (Environment Variables) ---
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID_RAW = os.environ.get('ADMIN_ID')
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW and ADMIN_ID_RAW.isdigit() else 0
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://akkauntbravl549-afk.github.io/WaterMap/')

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)

# Хранилище временных заявок на добавление точек
pending_submissions = {}

# --- Функция расчета расстояния между координатами (в километрах) ---
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Радиус Земли в км
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- Загрузка точек из базы (JSON) ---
def load_points():
    try:
        with open('polyclinics.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Сохранение новой одобренной точки в JSON ---
def save_point_to_db(new_point):
    points = load_points()
    points.append(new_point)
    try:
        with open('polyclinics.json', 'w', encoding='utf-8') as f:
            json.dump(points, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении точки в файл: {e}")

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    
    text = (
        "💧 **WaterMap — твой навигатор по бесплатной питьевой воде.**\n\n"
        "Здесь ты можешь найти ближайший кулер, питьевой фонтанчик или заведение с бесплатной водой, "
        "а также пополнить карту новыми локациями.\n\n"
        "1. Нажми **«Где вода рядом?»** и отправь геолокацию — покажу ближайшие точки в радиусе 2 км.\n"
        "2. Или открой карту прямо в Telegram, чтобы посмотреть всё.\n"
        "3. Знаешь, где есть вода? Жми **«Добавить точку»**.\n\n"
        "Выберите, как удобнее начать 👇"
    )
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_geo = KeyboardButton(text="📍 Где вода рядом?", request_location=True)
    btn_map = KeyboardButton(text="🗺 Открыть карту", web_app=WebAppInfo(url=WEB_APP_URL))
    btn_add = KeyboardButton(text="➕ Добавить точку")
    
    markup.add(btn_geo, btn_map, btn_add)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- Поиск ближайшей воды по геолокации ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_lat = message.location.latitude
    user_lon = message.location.longitude
    
    points = load_points()
    if not points:
        bot.send_message(message.chat.id, "База точек пока пуста 😔. Стань первым, кто добавит кулер на карту!")
        return
        
    nearby_spots = []
    for p in points:
        if 'lat' in p and 'lng' in p:
            try:
                dist = get_distance(user_lat, user_lon, float(p['lat']), float(p['lng']))
                if dist <= 2.0:  # Ищем в радиусе 2 км
                    nearby_spots.append((p, dist))
            except (ValueError, TypeError):
                continue
                
    if not nearby_spots:
        bot.send_message(
            message.chat.id, 
            "В радиусе 2 км пока нет известных кулеров 🏜️\n\n"
            "Следите за обновлениями карты или добавьте свою точку, если нашли воду неподалеку!"
        )
        return
        
    nearby_spots.sort(key=lambda x: x[1])
    
    reply = "📍 **Ближайшие точки с водой:**\n\n"
    for i, (spot, dist) in enumerate(nearby_spots[:5]):
        meters = int(dist * 1000)
        address = spot.get('address', 'Адрес не указан')
        title = spot.get('title', 'Кулер / Питьевая вода')
        reply += f"{i+1}. **{title}** — {meters} м.\n└ {address}\n\n"
        
    bot.send_message(message.chat.id, reply, parse_mode="Markdown")

# --- Добавление точки (Предложка) ---
@bot.message_handler(func=lambda msg: msg.text in ["➕ Добавить точку", "/add"])
def start_add(message):
    msg = bot.send_message(
        message.chat.id, 
        "Отправьте геолокацию места (через иконку скрепки 📎 ➔ Геопозиция), где расположен кулер или фонтанчик:"
    )
    bot.register_next_step_handler(msg, process_add_location)

def process_add_location(message):
    if not message.location:
        bot.send_message(message.chat.id, "Это не геолокация. Добавление отменено. Попробуйте заново через «➕ Добавить точку».")
        return
        
    chat_id = message.chat.id
    pending_submissions[chat_id] = {
        'lat': message.location.latitude,
        'lng': message.location.longitude,
        'user_id': message.from_user.id,
        'username': message.from_user.username or "без username"
    }
    
    msg = bot.send_message(message.chat.id, "Отлично! Теперь введите название или краткое описание места (например: 'Кулер на 2 этаже ТЦ'):")
    bot.register_next_step_handler(msg, process_add_title)

def process_add_title(message):
    chat_id = message.chat.id
    if chat_id not in pending_submissions:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте начать заново.")
        return
        
    pending_submissions[chat_id]['title'] = message.text
    pending_submissions[chat_id]['address'] = message.text
    data = pending_submissions[chat_id]
    
    bot.send_message(message.chat.id, "Спасибо! Заявка отправлена модератору на проверку ⏳")
    
    # Отправка заявки администратору
    if ADMIN_ID != 0:
        admin_markup = InlineKeyboardMarkup()
        btn_approve = InlineKeyboardButton("✅ Одобрить", callback_data=f"app_{chat_id}")
        btn_reject = InlineKeyboardButton("❌ Отклонить", callback_data=f"rej_{chat_id}")
        admin_markup.add(btn_approve, btn_reject)
        
        admin_text = (
            f"🔔 **Новая точка на проверку!**\n\n"
            f"📍 Координаты: `{data['lat']}, {data['lng']}`\n"
            f"📝 Описание: {data['title']}\n"
            f"👤 От: @{data['username']} (ID: {data['user_id']})"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

# --- Обработка нажатий кнопок Одобрить / Отклонить админом ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_', 'rej_')))
def handle_moderation(call):
    action, user_chat_id_str = call.data.split('_')
    user_chat_id = int(user_chat_id_str)
    
    if action == 'app':
        if user_chat_id in pending_submissions:
            data = pending_submissions.pop(user_chat_id)
            save_point_to_db({
                'title': data['title'],
                'address': data['address'],
                'lat': data['lat'],
                'lng': data['lng']
            })
            bot.edit_message_text(f"✅ Точка **{data['title']}** одобрена и добавлена!", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            try:
                bot.send_message(user_chat_id, f"🎉 Ваша точка «{data['title']}» успешно добавлена на карту!")
            except Exception:
                pass
        else:
            bot.answer_callback_query(call.id, "Заявка устарела или уже обработана.")
            
    elif action == 'rej':
        if user_chat_id in pending_submissions:
            pending_submissions.pop(user_chat_id)
        bot.edit_message_text("❌ Заявка отклонена.", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_chat_id, "😔 К сожалению, ваша заявка на добавление точки была отклонена.")
        except Exception:
            pass

# --- Веб-сервер Flask для проверки работоспособности на Render ---
@app.route('/')
def home():
    return "WaterMap Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- Точка входа ---
if __name__ == '__main__':
    # 1. Запуск Flask в отдельном потоке (чтобы Render видел открытый порт)
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("Веб-сервер Flask запущен...")

    # 2. Бесконечный цикл прослушивания сообщений
    print("Бот WaterMap запущен и готов к работе!")
    bot.infinity_polling(skip_pending=True)
