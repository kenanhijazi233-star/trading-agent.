import uuid
import numpy as np
import pandas as pd
from core.models import Order, OrderSide, ExecutionResult


class SimulatedBroker:
    """
    محاكي تنفيذ صفقات واقعي يحاكي السبريد، الانزلاق السعري (Slippage)، والعمولات.
    """
    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001,   # 0.1% عمولة منصة (مثل بايننس)
        half_spread_pct: float = 0.0002,  # نصف السبريد (0.02%)
        slippage_std_pct: float = 0.0003  # انحراف معياري للانزلاق السعري
    ):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.half_spread_pct = half_spread_pct
        self.slippage_std_pct = slippage_std_pct

        # تتبع المراكز المفتوحة وسجل التنفيذ
        self.positions = {}
        self.execution_history = []

    def execute_order(self, order: Order, current_market_price: float) -> ExecutionResult:
        """
        تنفيذ الأمر وحساب الأسعار الواقعية والعمولات
        """
        # 1. احتساب تأثير السبريد
        # الشراء بسعر أعلى قليلاً (Ask) والبيع بسعر أقل قليلاً (Bid)
        spread_adjustment = current_market_price * self.half_spread_pct
        if order.side == OrderSide.BUY:
            base_price = current_market_price + spread_adjustment
        else:
            base_price = current_market_price - spread_adjustment

        # 2. احتساب الانزلاق السعري العشوائي (Realistic Slippage)
        slippage_factor = abs(np.random.normal(0, self.slippage_std_pct))
        if order.side == OrderSide.BUY:
            fill_price = base_price * (1 + slippage_factor)
        else:
            fill_price = base_price * (1 - slippage_factor)

        actual_slippage = abs(fill_price - current_market_price)

        # 3. احتساب قيمة الصفقة الإجمالية والعمولة
        trade_value = fill_price * order.quantity
        commission = trade_value * self.commission_rate

        # 4. تحديث الرصيد والمركز
        if order.side == OrderSide.BUY:
            self.balance -= (trade_value + commission)
            self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) + order.quantity
        else:  # SELL
            self.balance += (trade_value - commission)
            self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) - order.quantity

        result = ExecutionResult(
            order_id=str(uuid.uuid4())[:8],
            symbol=order.symbol,
            side=order.side,
            executed_quantity=order.quantity,
            executed_price=round(fill_price, 4),
            commission=round(commission, 4),
            slippage=round(actual_slippage, 4),
            timestamp=order.timestamp
        )

        self.execution_history.append(result)
        return result

    def get_portfolio_value(self, current_price: float, symbol: str) -> float:
        """احتساب القيمة الإجمالية للمحفظة (كاش + قيمة العملات المفتوحة)"""
        position_qty = self.positions.get(symbol, 0.0)
        return self.balance + (position_qty * current_price)
