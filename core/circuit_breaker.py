import pandas as pd
from typing import Tuple


class CircuitBreaker:
    """
    قاطع الأمان التلقائي لحماية الحساب من الكوارث وحالات التذبذب العنيف.
    """
    def __init__(
        self,
        max_daily_drawdown_pct: float = 0.03,  # حد أقصى للتراجع اليومي 3%
        max_consecutive_losses: int = 3,       # أقصى عدد صفقات خاسرة متتالية
        volatility_threshold_multiplier: float = 2.5  # مضاعف ATR لاعتبار السوق في صدمة
    ):
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.volatility_threshold_multiplier = volatility_threshold_multiplier

        self.consecutive_losses = 0
        self.daily_starting_balance = None
        self.current_day = None
        self.is_tripped = False
        self.trip_reason = ""

    def update_daily_reference(self, current_timestamp: pd.Timestamp, balance: float):
        """تحديث رصيد بداية اليوم لمراقبة الـ Drawdown اليومي"""
        bar_date = current_timestamp.date()
        if self.current_day != bar_date:
            self.current_day = bar_date
            self.daily_starting_balance = balance
            # إعادة ضبط القاطع إذا كان مفصولاً بسبب هبوط اليوم السابق
            if self.is_tripped and "Daily drawdown" in self.trip_reason:
                self.is_tripped = False
                self.trip_reason = ""

    def register_trade_result(self, pnl: float):
        """تسجيل نتيجة الصفقة لمراقبة الخسائر المتتالية"""
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.is_tripped = True
                self.trip_reason = f"Hit max consecutive losses ({self.consecutive_losses})"
        else:
            self.consecutive_losses = 0

    def can_trade(self, current_balance: float, current_atr: float, baseline_atr: float) -> Tuple[bool, str]:
        """
        التحقق مما إذا كان مسموحاً للوكيل بفتح صفقات جديدة
        """
        # 1. إذا كان القاطع مفصولاً بالفعل
        if self.is_tripped:
            return False, f"Trading halted: {self.trip_reason}"

        # 2. فحص التراجع اليومي (Daily Drawdown)
        if self.daily_starting_balance and self.daily_starting_balance > 0:
            daily_loss = (self.daily_starting_balance - current_balance) / self.daily_starting_balance
            if daily_loss >= self.max_daily_drawdown_pct:
                self.is_tripped = True
                self.trip_reason = f"Daily drawdown reached {daily_loss * 100:.2f}%"
                return False, f"Trading halted: {self.trip_reason}"

        # 3. فحص صدمات التذبذب المفاجئ (Volatility Shock)
        if baseline_atr > 0 and (current_atr / baseline_atr) >= self.volatility_threshold_multiplier:
            return False, "Trading temporarily blocked: High volatility spike detected"

        return True, "All safety constraints passed"
