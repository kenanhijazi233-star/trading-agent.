from core.models import Signal, SignalType, RiskAssessment


class RiskManager:
    """
    محرك إدارة المخاطر المستقل.
    يحدد حجم اللوت ونقاط الوقف والهدف بناءً على ATR ورأس المال.
    """
    def __init__(self, risk_per_trade_pct: float = 0.01, atr_multiplier: float = 2.0, reward_risk_ratio: float = 1.5):
        self.risk_per_trade_pct = risk_per_trade_pct  # أقصى نسبة خسارة مسموحة للصفقة (1%)
        self.atr_multiplier = atr_multiplier          # مضاعف ATR لتحديد بُعد وقف الخسارة
        self.reward_risk_ratio = reward_risk_ratio    # نسبة العائد للمخاطرة (1.5 ضعف وقف الخسارة)

    def assess_signal(self, signal: Signal, current_price: float, current_atr: float, portfolio_balance: float) -> RiskAssessment:
        # 1. رفض إشارات الانتظار
        if signal.signal_type == SignalType.HOLD or signal.strength <= 0:
            return RiskAssessment(approved=False, reason="No active trade signal (HOLD)")

        # 2. التأكد من سلامة مدخلات السعر و ATR
        if current_price <= 0 or current_atr <= 0:
            return RiskAssessment(approved=False, reason="Invalid price or ATR data")

        # 3. حساب مسافة وقف الخسارة بناءً على تذبذب السوق (Volatility-adjusted Stop Loss)
        stop_distance = current_atr * self.atr_multiplier
        if stop_distance >= current_price:
            return RiskAssessment(approved=False, reason="Stop distance exceeds current price")

        # 4. حساب رأس المال المعرض للمخاطرة في هذه الصفقة
        risk_capital = portfolio_balance * self.risk_per_trade_pct
        
        # 5. حساب حجم المركز المطلوب (Position Sizing)
        # الحجم = المبلغ المعرض للمخاطرة مقسوماً على مسافة الوقف
        target_quantity = risk_capital / stop_distance

        # تعديل الحجم وفقاً لقوة الإشارة الصادرة عن الاستراتيجية
        target_quantity = target_quantity * signal.strength

        # التأكد من أن القيمة الإجمالية لا تتجاوز الرصيد الكلي
        position_value = target_quantity * current_price
        if position_value > portfolio_balance:
            target_quantity = portfolio_balance / current_price

        # 6. تحديد أسعار وقف الخسارة وأخذ الربح بحسب الاتجاه
        if signal.signal_type == SignalType.BUY:
            stop_loss = current_price - stop_distance
            take_profit = current_price + (stop_distance * self.reward_risk_ratio)
        else:  # SELL
            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * self.reward_risk_ratio)

        return RiskAssessment(
            approved=True,
            reason=f"Approved with ATR-based risk management (Strength: {signal.strength:.2f})",
            target_quantity=round(target_quantity, 6),
            stop_loss_price=round(stop_loss, 2),
            take_profit_price=round(take_profit, 2)
        )
