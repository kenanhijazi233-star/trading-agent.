import pandas as pd
from core.models import Signal, SignalType


class SignalEngine:
    """
    محرك توليد الإشارات بناءً على اتجاه السوق والزخم.
    يفصل بالكامل منطق الإشارة عن تحديد حجم الصفقة.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol

    def generate_signal(self, current_bar: pd.Series) -> Signal:
        """
        تقييم شمعة مغلقة واحدة (t-1) لتوليد إشارة
        """
        timestamp = current_bar['timestamp'] if 'timestamp' in current_bar else pd.Timestamp.now()
        regime = current_bar.get('regime', 'CHOPPY')
        rsi = current_bar.get('rsi', 50.0)
        close = current_bar.get('close', 0.0)
        ema_fast = current_bar.get('ema_fast', 0.0)
        ema_slow = current_bar.get('ema_slow', 0.0)

        signal_type = SignalType.HOLD
        strength = 0.0

        # استراتيجية تتبع الاتجاه مع فلترة السوق المتذبذب
        if regime == 'TRENDING_UP':
            # الاتجاه صاعد والزخم لم يصل بعد إلى ذروة الشراء المفرطة
            if ema_fast > ema_slow and rsi < 70:
                signal_type = SignalType.BUY
                # قوة الإشارة تتناسب عكسياً مع قرب RSI من 70
                strength = min(1.0, max(0.2, (70 - rsi) / 40))

        elif regime == 'TRENDING_DOWN':
            # الاتجاه هابط والزخم لم يصل بعد إلى ذروة البيع المفرطة
            if ema_fast < ema_slow and rsi > 30:
                signal_type = SignalType.SELL
                # قوة الإشارة تتناسب مع قرب السقوط
                strength = min(1.0, max(0.2, (rsi - 30) / 40))

        # إذا كانت حالة السوق متذبذبة (CHOPPY)، نتجنب الدخول نهائياً
        else:
            signal_type = SignalType.HOLD
            strength = 0.0

        return Signal(
            timestamp=timestamp,
            symbol=self.symbol,
            signal_type=signal_type,
            strength=strength,
            regime=regime
        )
