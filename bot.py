import os
import telebot
import threading
import time
import math
import json
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Настройки (твои текущие)
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID_RAW = os.environ.get('ADMIN_ID')
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else 0
WEB_APP_URL = 'https://akkauntbravl549-afk.github.io/WaterMap/'

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)
pending_submissions = {}

# --- Функция расчета расстояния (в километрах) ---
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Радиус Земли
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
        # Сюда будет грузиться твой файл polyclinics.json или файл с кулерами
        with open('polyclinics.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return [] # Если файла пока нет, возвращаем пустой список

# --- Красивая команда /start ---
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
    # Кнопка запроса геопозиции
    btn_geo = KeyboardButton(text="📍 Где вода рядом?", request_location=True)
    btn_map = KeyboardButton(text="🗺 Открыть карту", web_app=WebAppInfo(url=WEB_APP_URL))
    btn_add = KeyboardButton(text="➕ Добавить точку")
    
    markup.add(btn_geo, btn_map, btn_add)
    # parse_mode="Markdown" делает текст жирным (где **)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- Обработчик геолокации от пользователя ---
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
        # Проверяем, есть ли координаты у точки
        if 'lat' in p and 'lng' in p:
            dist = get_distance(user_lat, user_lon, float(p['lat']), float(p['lng']))
            if dist <= 2.0: # Ищем в радиусе 2 км
                nearby_spots.append((p, dist))
                
    if not nearby_spots:
        bot.send_message(
            message.chat.id, 
            "В радиусе 2 км пока нет известных кулеров 🏜️\n\n"
            "Следите за обновлениями карты или добавьте свою точку, если нашли воду неподалеку!"
        )
        return
        
    # Сортируем от ближайшего к дальнему
    nearby_spots.sort(key=lambda x: x[1])
    
    reply = "📍 **Ближайшие точки с водой:**\n\n"
    # Показываем топ-5 ближайших мест
    for i, (spot, dist) in enumerate(nearby_spots[:5]):
        meters = int(dist * 1000)
        address = spot.get('address', 'Адрес не указан')
        title = spot.get('title', 'Кулер')
        reply += f"{i+1}. **{title}** — {meters} м.\n└ {address}\n\n"
        
    bot.send_message(message.chat.id, reply, parse_mode="Markdown")

# --- Твой старый код /add и Flask (оставь как было) ---
# ... (здесь функции start_add, save_coordinates, save_photo, handle_mod, run_web и while True) ...
