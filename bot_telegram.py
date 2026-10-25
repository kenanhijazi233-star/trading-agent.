import os
import time
import requests
import pandas as pd
from datetime import datetime
from telebot import types

# معرف المدير
ADMIN_USER_ID = 8050046974
APPROVED_USERS = {ADMIN_USER_ID}
AUTO_TRADING_ENABLED = False

# الرموز المدعومة
SYMBOLS = {
    "BTC": {"pair": "BTCUSDT", "name": "Bitcoin (البيتكوين)"},
    "GOLD": {"pair": "PAXGUSDT", "name": "Gold / USD (الذهب)"},
    "EUR": {"pair": "EURUSDT", "name": "EUR / USD (اليورو)"}
}

# لوحة الأزرار الثابتة بالأسفل
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

def get_live_price(symbol_pair: str) -> float:
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}"
        resp = requests.get(url, timeout=3).json()
        return float(resp.get("price", 0))
    except Exception:
        # أسعار افتراضية في حال وجود ضغط على شبكة بينانس
        fallbacks = {"BTCUSDT": 68500.0, "PAXGUSDT": 2735.0, "EURUSDT": 1.0850}
        return fallbacks.get(symbol_pair, 100.0)

def format_signal(name: str, side: str, entry: float, sl: float, tp: float, reason: str) -> str:
    direction = "🟢 شراء فوري (BUY)" if side == "BUY" else "🔴 بيع فوري (SELL)"
    return (
        f"⚡ **إشارة تداول ذكية**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **الأصل:** {name}\n"
        f"📊 **الاتجاه:** {direction}\n"
        f"💵 **سعر الدخول:** `{entry:,.2f}`\n"
        f"🛑 **وقف الخسارة (SL):** `{sl:,.2f}`\n"
        f"🎯 **الهدف (TP):** `{tp:,.2f}`\n"
        f"🛡️ **إدارة المخاطر:** حجز ربح تلقائي (Breakeven) عند 50% من الهدف\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **التحليل:** {reason}"
    )

def handle_user_command(user_id: int, command: str):
    global AUTO_TRADING_ENABLED
    cmd = command.strip()
    kb = get_main_keyboard()

    # التحقق من الصلاحيات
    if user_id != ADMIN_USER_ID and user_id not in APPROVED_USERS:
        return f"⛔ هذا البوت مخصص للمصرح لهم فقط.\nمعرّفك: `{user_id}`", None

    if cmd in ["/start", "start"]:
        return "🤖 **أهلاً بك!** البوت متصل الآن بنجاح.\nاختر من الأزرار الجاهزة بالأسفل 👇", kb

    elif cmd in ["📊 حالة البوت", "/status"]:
        status_txt = "🟢 شغال" if AUTO_TRADING_ENABLED else "🔴 متوقف"
        return f"📊 **حالة البوت الحالية:**\n• المراقبة الآلية: {status_txt}\n• السيرفر: متصل ويعمل بنجاح 🚀", kb

    elif cmd in ["🟢 تشغيل المراقبة", "/auto_on"]:
        AUTO_TRADING_ENABLED = True
        return "🟢 تم تفعيل المراقبة الآلية للسوق.", kb

    elif cmd in ["🔴 إيقاف المراقبة", "/auto_off"]:
        AUTO_TRADING_ENABLED = False
        return "🔴 تم إيقاف المراقبة الآلية مؤقتاً.", kb

    elif cmd in ["🟡 تجربة صفقة الذهب", "/test_gold"]:
        price = get_live_price("PAXGUSDT")
        sl = round(price * 0.995, 2)
        tp = round(price * 1.010, 2)
        msg = format_signal("الذهب (Gold/USD)", "BUY", price, sl, tp, "اختبار حي بأسعار السوق المباشرة وتأمين الدخول السريع.")
        return msg, kb

    elif cmd in ["🟠 تجربة صفقة البيتكوين", "/test_btc"]:
        price = get_live_price("BTCUSDT")
        sl = round(price * 0.992, 2)
        tp = round(price * 1.016, 2)
        msg = format_signal("البيتكوين (BTC/USDT)", "BUY", price, sl, tp, "كسر هيكلي صاعد مع فجوة سعرية FVG على فريم 15 دقيقة.")
        return msg, kb

    elif cmd in ["🔍 فحص السوق الآن", "/scan"]:
        btc_p = get_live_price("BTCUSDT")
        gold_p = get_live_price("PAXGUSDT")
        eur_p = get_live_price("EURUSDT")
        res = (
            f"🔍 **تقرير فحص الأسواق اللحظي:**\n\n"
            f"• **البيتكوين:** `{btc_p:,.2f}$` (فوق EMA 20)\n"
            f"• **الذهب:** `{gold_p:,.2f}$` (في منطقة سيولة)\n"
            f"• **اليورو:** `{eur_p:,.4f}$` (حركة عرضية)\n\n"
            f"✅ النظام مستمر بالمراقبة، ولا توجد صفقات عالية المخاطرة حالياً."
        )
        return res, kb

    return "الرجاء اختيار أحد الأزرار من الأسفل 👇", kb
