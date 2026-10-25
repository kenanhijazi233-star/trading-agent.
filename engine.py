import os
import time
import threading
import telebot
from flask import Flask
from bot_telegram import handle_user_command

BOT_TOKEN = "8515451267:AAGA4rS06pz9N-xdccO__kYJfdyUI7TYM3A"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

@bot.message_handler(func=lambda msg: True)
def on_message(message):
    try:
        reply_text, keyboard = handle_user_command(message.from_user.id, message.text)
        if keyboard:
            bot.send_message(message.chat.id, reply_text, reply_markup=keyboard)
        else:
            bot.reply_to(message, reply_text)
    except Exception as e:
        print(f"Message handling error: {e}")

def run_bot():
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            print("🚀 البوت بدأ العمل واستقبال الأزرار بنجاح...")
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception as e:
            print(f"Bot error, restarting in 5s: {e}")
            time.sleep(5)

# تشغيل خيط البوت
threading.Thread(target=run_bot, daemon=True).start()

@app.route('/')
def home():
    return "<h2 style='color:#2ea043; text-align:center; padding-top:50px;'>🟢 سيرفر التداول وبوت تيليجرام يعملان بنجاح تام!</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
