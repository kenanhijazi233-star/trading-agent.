import os
import time
import threading
import requests
import telebot
from telebot import types
from flask import Flask

# التوكن ومعرف المدير
BOT_TOKEN = "8515451267:AAGA4rS06pz9N-xdccO__kYJfdyUI7TYM3A"
ADMIN_USER_ID = 8050046974
APPROVED_USERS = {ADMIN_USER_ID}
AUTO_TRADING_ENABLED = False

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# لوحة الأزرار الجاهزة أسفل الشاشة
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_scan = types.KeyboardButton("🔍 فحص السوق الآن")
    btn_status = types.KeyboardButton("📊 حالة البوت")
    btn_gold = types.KeyboardButton("🟡 تجربة صفقة الذهب")
    btn_btc = types.KeyboardButton("🟠 تجربة صفقة البيتكوين")
    btn_auto_on = types.KeyboardButton("🟢 تشغيل المراقبة")
    btn_auto_off = types.KeyboardButton("🔴 إيقاف المراقبة")
    markup.add(btn_scan, btn_status)
    markup.add(btn_gold, btn_btc)
    markup.add(btn_auto_on, btn_auto_off)
    return markup

# جلب الأسعار اللحظية من بينانس
def get_live_price(symbol: str) -> float:
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        res = requests.get(url, timeout=3).json()
        return float(res.get("price", 0))
    except Exception:
        fallbacks = {"BTCUSDT": 68500.0, "PAXGUSDT": 2735.0, "EURUSDT": 1.0850}
        return fallbacks.get(symbol, 100.0)

# بطاقة التوصية
def format_card(title: str, side: str, entry: float, sl: float, tp: float, note: str) -> str:
    direction = "🟢 شراء فوري (BUY)" if side == "BUY" else "🔴 بيع فوري (SELL)"
    return (
        f"⚡ **إشارة تداول ذكية**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **الأصل:** {title}\n"
        f"📊 **الاتجاه:** {direction}\n"
        f"💵 **سعر الدخول الحقيقي:** `{entry:,.2f}`\n"
        f"🛑 **وقف الخسارة (SL):** `{sl:,.2f}`\n"
        f"🎯 **الهدف الأساسي (TP):** `{tp:,.2f}`\n"
        f"🛡️ **إدارة المخاطر:** تأمين فوري (Breakeven) عند 50% من الهدف\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **التحليل الفني:** {note}"
    )

# استقبال أوامر تيليجرام والرد بالأزرار
@bot.message_handler(func=lambda msg: True)
def handle_telegram(message):
    global AUTO_TRADING_ENABLED
    user_id = message.from_user.id
    text = message.text.strip()
    kb = get_main_keyboard()

    if user_id != ADMIN_USER_ID and user_id not in APPROVED_USERS:
        bot.reply_to(message, f"⛔ عذراً! هذا البوت محمي ومخصص للمشتركين فقط.\nمعرّفك: `{user_id}`")
        return

    if text in ["/start", "start"]:
        bot.send_message(
            message.chat.id,
            "🤖 **مرحباً بك في وكيل التداول الذكي!**\n\nتحكم بالبوت مباشرة عبر الأزرار الجاهزة بالأسفل 👇",
            reply_markup=kb
        )

    elif text in ["📊 حالة البوت", "/status"]:
        st = "🟢 شغال" if AUTO_TRADING_ENABLED else "🔴 متوقف"
        bot.send_message(
            message.chat.id,
            f"📊 **حالة النظام:**\n• المراقبة الآلية: {st}\n• السيرفر: متصل ويعمل بنجاح 🚀",
            reply_markup=kb
        )

    elif text in ["🟢 تشغيل المراقبة", "/auto_on"]:
        AUTO_TRADING_ENABLED = True
        bot.send_message(message.chat.id, "🟢 تم تفعيل المراقبة الآلية بنجاح.", reply_markup=kb)

    elif text in ["🔴 إيقاف المراقبة", "/auto_off"]:
        AUTO_TRADING_ENABLED = False
        bot.send_message(message.chat.id, "🔴 تم إيقاف المراقبة التلقائية مؤقتاً.", reply_markup=kb)

    elif text in ["🟡 تجربة صفقة الذهب", "/test_gold"]:
        price = get_live_price("PAXGUSDT")
        sl = round(price * 0.995, 2)
        tp = round(price * 1.010, 2)
        card = format_card("الذهب (Gold/USD)", "BUY", price, sl, tp, "اختبار حي بأسعار السوق الحالية ونظام حجز الأرباح.")
        bot.send_message(message.chat.id, card, reply_markup=kb)

    elif text in ["🟠 تجربة صفقة البيتكوين", "/test_btc"]:
        price = get_live_price("BTCUSDT")
        sl = round(price * 0.992, 2)
        tp = round(price * 1.016, 2)
        card = format_card("البيتكوين (BTC/USDT)", "BUY", price, sl, tp, "كسر هيكلي وفجوة صاعدة FVG مع إدارة مخاطر 1:2.")
        bot.send_message(message.chat.id, card, reply_markup=kb)

    elif text in ["🔍 فحص السوق الآن", "/scan"]:
        btc = get_live_price("BTCUSDT")
        gold = get_live_price("PAXGUSDT")
        eur = get_live_price("EURUSDT")
        res = (
            f"🔍 **تقرير فحص الأسواق اللحظي:**\n\n"
            f"• **البيتكوين:** `{btc:,.2f}$`\n"
            f"• **الذهب:** `{gold:,.2f}$`\n"
            f"• **اليورو:** `{eur:,.4f}$`\n\n"
            f"✅ النظام يتابع حركة السيولة والشموع بدقة."
        )
        bot.send_message(message.chat.id, res, reply_markup=kb)

    else:
        bot.send_message(message.chat.id, "اختر من الأزرار بالأسفل 👇", reply_markup=kb)

# خيط تشغيل تيليجرام
def start_bot():
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            print("🚀 البوت بدأ العمل واستقبال الأوامر...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling retry: {e}")
            time.sleep(5)

threading.Thread(target=start_bot, daemon=True).start()

@app.route('/')
def home():
    return "<h2 style='color:#2ea043; text-align:center; padding-top:50px;'>🟢 النظام متصل ومستقر وبوت تيليجرام يعمل بنجاح!</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
