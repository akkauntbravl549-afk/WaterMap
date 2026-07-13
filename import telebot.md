#   
import telebot  
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton  
  
# Твой токен от @BotFather  
TOKEN = '8609236930:AAHExw0HXJMBMTNSUPL1F5DXaqLZBmsiRS8'  
  
# ВСТАВЬ СЮДА СВОЙ ЦИФРОВОЙ ID, КОТОРЫЙ УЗНАЛ В @userinfobot  
ADMIN_ID = 5265210907   
  
bot = telebot.TeleBot(TOKEN)  
  
# Ссылка на твою карту на GitHub Pages  
WEB_APP_URL = 'https://akkauntbravl549-afk.github.io/WaterMap/'  
  
# Временная база данных в памяти бота для хранения шагов предложки  
# Структура: {user_id: {'coords': '...', 'photo': '...'}}  
pending_submissions = {}  
  
@bot.message_handler(commands=['start'])  
def start_message(message):  
    markup = ReplyKeyboardMarkup(resize_keyboard=True)  
    web_app = WebAppInfo(url=WEB_APP_URL)  
    btn = KeyboardButton(text="💧 Открыть карту воды", web_app=web_app)  
    markup.add(btn)  
      
    welcome_text = (  
        "Привет! Я бот для поиска бесплатной питьевой воды.\n\n"  
        "Нажми на кнопку ниже, чтобы открыть интерактивную карту.\n\n"  
        "✨ Нашел новый кулер, которого нет на карте? Напиши команду /add, чтобы предложить его!"  
    )  
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)  
  
  
# === БЛОК СБОРА ПРЕДЛОЖКИ (МЕХАНИКА ЮЗЕРА) ===  
  
@bot.message_handler(commands=['add'])  
def start_add(message):  
    user_id = message.chat.id  
    # Создаем пустой черновик для этого пользователя  
    pending_submissions[user_id] = {}  
      
    bot.send_message(user_id, "📍 Шаг 1/2:\nОтправь координаты кулера с Яндекс Карт.\n(Зажми точку на карте, скопируй цифры и пришли сюда, например: `55.868368, 37.491889`)")  
    # Перенаправляем следующий ответ пользователя в функцию сохранения координат  
    bot.register_next_step_handler(message, save_coordinates)  
  
def save_coordinates(message):  
    user_id = message.chat.id  
      
    # Защита от дурака: если пользователь вместо координат написал другую команду  
    if message.text and message.text.startswith('/'):  
        bot.send_message(user_id, "❌ Заполнение отменено. Вы ввели команду.")  
        return  
  
    pending_submissions[user_id]['coords'] = message.text  
    bot.send_message(user_id, "📸 Шаг 2/2:\nТеперь отправь ФОТОГРАФИЮ этого кулера, чтобы подтвердить его наличие:")  
    bot.register_next_step_handler(message, save_photo)  
  
def save_photo(message):  
    user_id = message.chat.id  
      
    # Проверяем, прислал ли пользователь именно фото  
    if message.content_type != 'photo':  
        bot.send_message(user_id, "⚠️ Это не фото! Пожалуйста, пришли именно фотографию кулера:")  
        bot.register_next_step_handler(message, save_photo)  
        return  
  
    # Получаем id фотографии самого лучшего качества (последняя в списке)  
    photo_id = message.photo[-1].file_id  
    pending_submissions[user_id]['photo'] = photo_id  
      
    # Сообщаем пользователю, что всё ок  
    bot.send_message(user_id, "⏳ Спасибо! Твоя предложка отправлена администратору на проверку. Я пришлю уведомление о решении!")  
      
    # Создаем админ-кнопки под фоткой  
    keyboard = InlineKeyboardMarkup()  
    # В callback_data зашиваем действие и ID юзера, чтобы знать, кого модерировать  
    btn_approve = InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}")  
    btn_reject = InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")  
    keyboard.add(btn_approve, btn_reject)  
      
    # Формируем сообщение для тебя  
    admin_text = (  
        "🚀 **НОВАЯ ПРЕДЛОЖКА ТОЧКИ!**\n\n"  
        f"От: @{message.from_user.username or 'Скрыт ник'}\n"  
        f"Координаты: `{pending_submissions[user_id]['coords']}`\n\n"  
        "Проверь фото ниже и выбери действие:"  
    )  
      
    # Бот присылает фотку кулера и инфо тебе в личку  
    bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, parse_mode="Markdown", reply_markup=keyboard)  
  
  
# === БЛОК МОДЕРАЦИИ (МЕХАНИКА АДМИНА) ===  
  
@bot.callback_query_handler(func=lambda call: True)  
def handle_moderation(call):  
    # Разделяем команду и ID пользователя (например, "approve_123456" -> "approve", "123456")  
    action, target_user_id = call.data.split('_')  
    target_user_id = int(target_user_id)  
      
    if action == "approve":  
        # 1. Пишем юзеру приятную новость  
        try:  
            bot.send_message(target_user_id, "🎉 Ура! Твоя предложка была одобрена модератором. Спасибо за вклад в карту, скоро точка появится!")  
        except Exception:  
            pass # На случай, если юзер заблокировал бота  
              
        # 2. Меняем текст сообщения у тебя, чтобы убрать кнопки и зафиксировать статус  
        updated_caption = call.message.caption + "\n\n🟢 **СТАТУС: ОДОБРЕНО**\n(Не забудь внести координаты в index.html!)"  
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption=updated_caption, reply_markup=None)  
        bot.answer_callback_query(call.id, "Точка одобрена!")  
          
    elif action == "reject":  
        # 1. Спрашиваем у тебя причину удаления  
        msg = bot.send_message(ADMIN_ID, "📝 Напиши в ответном сообщении причину отклонения (комментарий для пользователя):")  
        # Передаем управление в функцию отправки отказа, прокидывая ID юзера и инфо о сообщении  
        bot.register_next_step_handler(msg, lambda message: send_rejection(message, target_user_id, call.message.message_id, call.message.caption))  
        bot.answer_callback_query(call.id)  
  
def send_rejection(message, target_user_id, orig_msg_id, orig_caption):  
    reason = message.text # Твой текст с причиной  
      
    # 1. Отправляем пользователю отказ с твоим комментарием  
    try:  
        reject_text = f"❌ К сожалению, твоя предложка кулера была отклонена модератором.\n\n💬 **Причина:** {reason}"  
        bot.send_message(target_user_id, reject_text)  
    except Exception:  
        pass  
          
    # 2. Обновляем статус сообщения в твоей админке  
    updated_caption = orig_caption + f"\n\n🔴 **СТАТУС: ОТКЛОНЕНО**\n💬 **Причина:** {reason}"  
    bot.edit_message_caption(chat_id=ADMIN_ID, message_id=orig_msg_id, caption=updated_caption, reply_markup=None)  
    bot.send_message(ADMIN_ID, "🔴 Отклонено. Пользователю отправлено уведомление.")  
  
  
# Запуск бота  
print("Бот с админ-панелью успешно запущен!")  
bot.remove_webhook()  
bot.polling(none_stop=True)  
