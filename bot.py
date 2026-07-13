import os
import telebot
from flask import Flask
from threading import Thread

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Веб-сервер
app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Простейший обработчик
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Бот работает!")

# ЗАПУСК
if __name__ == '__main__':
    # Запускаем веб-сервер
    Thread(target=run_web).start()
    
    # Запускаем бота без infinity_polling, чтобы избежать конфликтов
    print("Бот запускается...")
    bot.polling(none_stop=True)
