import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Получаем данные из настроек Render
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

bot = telebot.TeleBot(TOKEN)
WEB_APP_URL = 'https://akkauntbravl549-afk.github.io/WaterMap/'
pending_submissions = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = WebAppInfo(url=WEB_APP_URL)
    btn = KeyboardButton(text="💧 Открыть карту воды", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "Привет! Используй /add для предложки.", reply_markup=markup)

@bot.message_handler(commands=['add'])
def start_add(message):
    user_id = message.chat.id
    pending_submissions[user_id] = {}
    bot.send_message(user_id, "📍 Шаг 1/2: Пришли координаты:")
    bot.register_next_step_handler(message, save_coordinates)

def save_coordinates(message):
    pending_submissions[message.chat.id]['coords'] = message.text
    bot.send_message(message.chat.id, "📸 Шаг 2/2: Пришли фото кулера:")
    bot.register_next_step_handler(message, save_photo)

def save_photo(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "Это не фото!")
        bot.register_next_step_handler(message, save_photo)
        return
    
    photo_id = message.photo[-1].file_id
    user_id = message.chat.id
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"))
    keyboard.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}"))
    
    bot.send_photo(ADMIN_ID, photo_id, caption=f"Предложка от {user_id}\nКоорд: {pending_submissions[user_id]['coords']}", reply_markup=keyboard)
    bot.send_message(user_id, "Отправлено на проверку!")

@bot.callback_query_handler(func=lambda call: True)
def handle_mod(call):
    action, uid = call.data.split('_')
    if action == "approve":
        bot.send_message(int(uid), "Одобрено!")
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption=call.message.caption + "\n🟢 Одобрено", reply_markup=None)

bot.polling(none_stop=True)
