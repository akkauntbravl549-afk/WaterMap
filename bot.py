import os
import telebot
import threading
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))
WEB_APP_URL = 'https://akkauntbravl549-afk.github.io/WaterMap/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
pending_submissions = {}

@app.route('/')
def home():
    return "Бот работает!"

# Команды
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn = KeyboardButton(text="💧 Открыть карту воды", web_app={"url": WEB_APP_URL})
    markup.add(btn)
    bot.send_message(message.chat.id, "Привет! Используй /add для предложки.", reply_markup=markup)

@bot.message_handler(commands=['add'])
def start_add(message):
    user_id = message.chat.id
    pending_submissions[user_id] = {}
    bot.send_message(user_id, "📍 Пришли координаты:")
    bot.register_next_step_handler(message, save_coordinates)

def save_coordinates(message):
    pending_submissions[message.chat.id]['coords'] = message.text
    bot.send_message(message.chat.id, "📸 Пришли фото кулера:")
    bot.register_next_step_handler(message, save_photo)

def save_photo(message):
    if not message.photo:
        bot.send_message(message.chat.id, "Нужно отправить фото!")
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
        bot.send_message(int(uid), "Твоя точка одобрена!")
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption=call.message.caption + "\n🟢 Одобрено", reply_markup=None)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.polling(none_stop=True)
