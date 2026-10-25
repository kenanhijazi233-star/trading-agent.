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

# تنظيف التوكن تلقائياً من أي مسافات أو أسطر إضافية
raw_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_TOKEN = raw_token if raw_token else "8515451267:AAGA4rS06pz9N-xdccO__kYJfdyUI7TYM3A"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# استقبال ومعالجة رسائل تيليجرام
@bot.message_handler(func=lambda msg: True)
def on_message(message):
    try:
        reply = handle_user_command(message.from_user.id, message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        print(f"Error handling message: {e}")

# فحص الأسواق دورياً وإرسال التنبيهات التلقائية
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
            print(f"Scanner exception: {e}")
            time.sleep(30)

def start_bot_polling():
    while True:
        try:
            print("🚀 البوت متصل ومستعد لاستقبال الأوامر...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as ex:
            print(f"Polling reconnecting: {ex}")
            time.sleep(5)

# تشغيل المهام في الخلفية
threading.Thread(target=start_bot_polling, daemon=True).start()
threading.Thread(target=background_market_scanner, daemon=True).start()

@app.route('/')
def home():
    return """
    <body style='background:#0d1117; color:#58a6ff; font-family:sans-serif; text-align:center; padding-top:60px;'>
        <h1 style='color:#2ea043;'>🟢 النظام السحابي لوكيل التداول وبوت تيليجرام يعمل بنجاح</h1>
        <p style='color:#8b949e;'>المحرك متصل بالأسواق الحية وجاهز لإرسال الإشارات وتأمين الصفقات.</p>
    </body>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
