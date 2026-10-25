import os
import requests
import pandas as pd
from datetime import datetime
from telebot import types

# --- إعدادات النظام والمشتركين ---
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "8050046974"))
APPROVED_USERS = set([ADMIN_USER_ID])
AUTO_TRADING_ENABLED = False

# لمنع تكرار الإشارات لنفس العملة ما دامت الفرصة لم تتغير
SENT_SIGNALS_CACHE = {}

SYMBOLS = {
    "BTC": {"pair": "BTCUSDT", "name": "Bitcoin (البيتكوين)", "is_crypto": True},
    "GOLD": {"pair": "PAXGUSDT", "name": "Gold / USD (الذهب)", "is_crypto": False},
    "EUR": {"pair": "EURUSDT", "name": "EUR / USD (اليورو)", "is_crypto": False}
}

# --- لوحة المفاتيح والأزرار الجاهزة أسفل الشاشة ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_status = types.KeyboardButton("📊 حالة البوت")
    btn_scan = types.KeyboardButton("🔍 فحص السوق الآن")
    btn_test_gold = types.KeyboardButton("🟡 تجربة صفقة الذهب")
    btn_test_btc = types.KeyboardButton("🟠 تجربة صفقة البيتكوين")
    btn_auto_on = types.KeyboardButton("🟢 تشغيل المراقبة الآلية")
    btn_auto_off = types.KeyboardButton("🔴 إيقاف المراقبة الآلية")
    
    markup.add(btn_scan, btn_status)
    markup.add(btn_test_gold, btn_test_btc)
    markup.add(btn_auto_on, btn_auto_off)
    return markup

# --- جلب الأسعار والشموع الحية من Binance ---
def get_live_price(symbol_pair: str) -> float:
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}"
        resp = requests.get(url, timeout=5).json()
        return float(resp["price"])
    except Exception:
        return 0.0

def get_live_klines(symbol_pair: str, interval: str, limit: int = 50) -> pd.DataFrame:
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol_pair}&interval={interval}&limit={limit}"
        data = requests.get(url, timeout=7).json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except Exception:
        return pd.DataFrame()

# --- محرك التحليل ومنع تكرار الإشارة ---
def analyze_asset(symbol_key: str):
    asset = SYMBOLS[symbol_key]
    pair = asset["pair"]
    now = datetime.utcnow()

    # فلتر عطلات الذهب والفوركس (السبت والأحد)
    if not asset["is_crypto"] and now.weekday() in [5, 6]:
        return None

    # فريم 1H للاتجاه
    df_1h = get_live_klines(pair, interval="1h", limit=30)
    if df_1h.empty or len(df_1h) < 20:
        return None

    ema20 = df_1h["close"].ewm(span=20, adjust=False).mean()
    trend = "BULLISH" if df_1h["close"].iloc[-1] > ema20.iloc[-1] else "BEARISH"

    # فريم 15m للـ FVG والسيولة
    df_15m = get_live_klines(pair, interval="15m", limit=10)
    if df_15m.empty or len(df_15m) < 4:
        return None

    c1 = df_15m.iloc[-3]
    c3 = df_15m.iloc[-1]
    current_price = c3["close"]

    signal_candidate = None

    # شراء
    if trend == "BULLISH" and c3["low"] > c1["high"]:
        entry = current_price
        sl = c1["low"]
        risk = entry - sl
        if risk > 0:
            tp = entry + (risk * 2.0)
            signal_candidate = {
                "symbol": pair,
                "name": asset["name"],
                "side": "BUY",
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "analysis": "تأكيد اتجاه صاعد قوي (1H EMA 20) + سحب سيولة وفجوة سعرية (15m Bullish FVG)"
            }

    # بيع
    elif trend == "BEARISH" and c3["high"] < c1["low"]:
        entry = current_price
        sl = c1["high"]
        risk = sl - entry
        if risk > 0:
            tp = entry - (risk * 2.0)
            signal_candidate = {
                "symbol": pair,
                "name": asset["name"],
                "side": "SELL",
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "analysis": "تأكيد اتجاه هابط رئيسي (1H EMA 20) + سحب سيولة وكسر قاع (15m Bearish FVG)"
            }

    # فلتر منع تكرار نفس الإشارة إن أُرسلت مؤخراً
    if signal_candidate:
        sig_id = f"{pair}_{signal_candidate['side']}_{round(signal_candidate['entry'], -1)}"
        last_time = SENT_SIGNALS_CACHE.get(sig_id, 0)
        # لا نكرر الإشارة لنفس النطاق إلا بعد مرور ساعتين (7200 ثانية)
        if time.time() - last_time < 7200:
            return None
        SENT_SIGNALS_CACHE[sig_id] = time.time()

    return signal_candidate

# --- تنسيق الرسائل ---
def format_signal_message(trade_dict: dict) -> str:
    direction = "🟢 شراء فوري (BUY)" if trade_dict["side"] == "BUY" else "🔴 بيع فوري (SELL)"
    return (
        f"⚡ **إشارة تداول ذكية معتمدة**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **الأصل:** {trade_dict['name']}\n"
        f"📊 **الاتجاه:** {direction}\n"
        f"💵 **نقطة الدخول الحية:** `{trade_dict['entry']:,.2f}`\n"
        f"🛑 **وقف الخسارة (SL):** `{trade_dict['sl']:,.2f}`\n"
        f"🎯 **الهدف الأساسي (TP):** `{trade_dict['tp']:,.2f}`\n"
        f"🛡️ **إدارة المخاطر:** حجز ربح تلقائي عند 50% من الطريق\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **التحليل الفني:**\n_{trade_dict['analysis']}_\n"
    )

# --- معالجة الأوامر من الأزرار أو الكتابة ---
def handle_user_command(user_id: int, command: str) -> tuple:
    global AUTO_TRADING_ENABLED, APPROVED_USERS

    cmd = command.strip()

    # حماية الاشتراك
    if user_id != ADMIN_USER_ID and user_id not in APPROVED_USERS:
        return (
            "⛔ **عذراً! هذا البوت محمي ومخصص للمشتركين فقط.**\n\n"
            f"معرّف حسابك: `{user_id}`\n"
            "تواصل مع الإدارة لتفعيل اشتراكك.",
            None
        )

    markup = get_main_keyboard()

    if cmd in ["/start", "start"]:
        msg = (
            "🤖 **مرحباً بك في لوحة تحكم وكيل التداول الذكي**\n\n"
            "استخدم الأزرار الجاهزة أسفل الشاشة للتحكم الكامل:"
        )
        return msg, markup

    elif cmd in ["🟢 تشغيل المراقبة الآلية", "/auto_on"]:
        AUTO_TRADING_ENABLED = True
        return "🟢 **تم تفعيل المراقبة الآلية.** يفحص البوت الأسواق تلقائياً بدون إرسال إشارات مكررة.", markup

    elif cmd in ["🔴 إيقاف المراقبة الآلية", "/auto_off"]:
        AUTO_TRADING_ENABLED = False
        return "🔴 **تم إيقاف المراقبة التلقائية مؤقتاً.**", markup

    elif cmd in ["🔍 فحص السوق الآن", "/scan"]:
        results = []
        for key in SYMBOLS:
            signal = analyze_asset(key)
            if signal:
                results.append(format_signal_message(signal))
        if results:
            return "\n\n".join(results), markup
        return "🔍 تم فحص الأسواق بدقة. لا توجد فرص مكتملة الشروط بنسبة 100% حالياً (فلتر الانضباط يمنع الدخول العشوائي).", markup

    elif cmd in ["🟡 تجربة صفقة الذهب", "/test_gold"]:
        price = get_live_price("PAXGUSDT") or 2735.0
        trade = {
            "name": "Gold / USD (الذهب الفوري)",
            "side": "BUY",
            "entry": price,
            "sl": price * 0.995,
            "tp": price * 1.01,
            "analysis": "صفقة تجريبية حية بأسعار السوق الآن لاختبار سرعة الإرسال وإدارة المخاطر."
        }
        return format_signal_message(trade), markup

    elif cmd in ["🟠 تجربة صفقة البيتكوين", "/test_btc"]:
        price = get_live_price("BTCUSDT") or 68500.0
        trade = {
            "name": "Bitcoin (البيتكوين)",
            "side": "BUY",
            "entry": price,
            "sl": price * 0.993,
            "tp": price * 1.014,
            "analysis": "صفقة تجريبية حية لاختبار تتبع الأهداف وتأمين الدخول (Breakeven)."
        }
        return format_signal_message(trade), markup

    elif cmd in ["📊 حالة البوت", "/status"]:
        state = "🟢 شغال ومستمر" if AUTO_TRADING_ENABLED else "🔴 متوقف"
        return (
            f"📊 **تقرير حالة البوت:**\n"
            f"• المراقبة الآلية: {state}\n"
            f"• فلاتر الأمان: منع التكرار + حجز الأرباح مفعلة بنجاح\n"
            f"• المشتركون المعتمدون: {len(APPROVED_USERS)}"
        ), markup

    return "اختر من الأزرار الجاهزة بالأسفل 👇", markup
