import os
import time
import threading
import telebot
from flask import Flask
from bot_telegram import (
    handle_user_command,
    SYMBOLS,
    analyze_asset,
    format_signal_message
)
import bot_telegram

raw_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_TOKEN = raw_token if raw_token else "8515451267:AAGA4rS06pz9N-xdccO__kYJfdyUI7TYM3A"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

@bot.message_handler(func=lambda msg: True)
def on_message(message):
    try:
        reply = handle_user_command(message.from_user.id, message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        print(f"Error handling message: {e}")

def background_market_scanner():
    while True:
        try:
            if bot_telegram.AUTO_TRADING_ENABLED:
                for key in SYMBOLS:
                    signal = analyze_asset(key)
                    if signal:
                        msg = format_signal_message(signal)
                        for uid in bot_telegram.APPROVED_USERS:
                            try:
                                bot.send_message(uid, msg)
                            except Exception:
                                pass
            time.sleep(60)
        except Exception as e:
            time.sleep(30)

def start_bot_polling():
    # إلغاء أي ويب هوك أو اتصال معلق أولاً
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(2)
    except Exception:
        pass

    while True:
        try:
            print("🚀 البوت متصل بنجاح وجاهز لاستقبال الأوامر...")
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as ex:
            print(f"Conflict or network retry in 5s: {ex}")
            time.sleep(5)

# تشغيل البوت وفحص السوق
threading.Thread(target=start_bot_polling, daemon=True).start()
threading.Thread(target=background_market_scanner, daemon=True).start()

@app.route('/')
def home():
    return "<h2 style='color:#2ea043; text-align:center; padding-top:50px;'>🟢 البوت وسيرفر التداول يعملان بنجاح بدون تعارض!</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
