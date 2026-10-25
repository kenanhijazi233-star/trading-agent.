import pandas as pd
import numpy as np

from core.models import Order, OrderSide, OrderType, SignalType
from core.data_handler import MarketDataLoader
from core.signals import SignalEngine
from core.risk_manager import RiskManager
from core.circuit_breaker import CircuitBreaker
from execution.simulated import SimulatedBroker


def run_agent_simulation():
    print("==========================================")
    print("🚀 بدء محاكاة وكيل التداول الذكي...")
    print("==========================================\n")

    # 1. إنشاء بيانات تجريبية تحاكي سوق حقيقي لزوج BTC/USDT (200 شمعة)
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=200, freq="1h")
    initial_price = 65000.0
    returns = np.random.normal(0.0005, 0.012, size=200)
    prices = initial_price * np.cumprod(1 + returns)

    raw_data = {
        'timestamp': dates,
        'open': prices * (1 - np.random.uniform(0, 0.003, size=200)),
        'high': prices * (1 + np.random.uniform(0.002, 0.008, size=200)),
        'low': prices * (1 - np.random.uniform(0.002, 0.008, size=200)),
        'close': prices,
        'volume': np.random.uniform(10, 100, size=200)
    }
    df = pd.DataFrame(raw_data)

    # 2. معالجة البيانات والمؤشرات وفلترة حالة السوق (Market Regime)
    loader = MarketDataLoader(df)
    processed_df = loader.prepare_features()
    baseline_atr = processed_df['atr'].mean()

    # 3. تهيئة الوحدات المستقلة
    symbol = "BTC/USDT"
    signal_engine = SignalEngine(symbol=symbol)
    risk_manager = RiskManager(risk_per_trade_pct=0.01, atr_multiplier=2.0)
    circuit_breaker = CircuitBreaker(max_daily_drawdown_pct=0.03, max_consecutive_losses=3)
    broker = SimulatedBroker(initial_balance=10000.0)

    # 4. حلقة الأحداث الزمنية شمعة بشمعة (Event-Driven Simulation Loop)
    print(f"💰 رأس المال الأولي: ${broker.initial_balance:,.2f}")
    print(f"📊 عدد الشموع المكتملة الخاضعة للتحليل: {len(processed_df)}\n")
    print("--- سجل التدقيق والقرارات (Audit Telemetry) ---")

    for idx, bar in processed_df.iterrows():
        current_time = bar['timestamp']
        current_price = bar['close']
        current_atr = bar['atr']

        # تحديث مرجع الرصيد اليومي لقاطع الأمان
        current_portfolio_value = broker.get_portfolio_value(current_price, symbol)
        circuit_breaker.update_daily_reference(current_time, current_portfolio_value)

        # التحقق من قواطع الأمان أولاً
        can_trade, halt_reason = circuit_breaker.can_trade(
            current_balance=current_portfolio_value,
            current_atr=current_atr,
            baseline_atr=baseline_atr
        )

        if not can_trade:
            continue

        # توليد الإشارة من الشمعة المغلقة الحالية
        signal = signal_engine.generate_signal(bar)

        if signal.signal_type != SignalType.HOLD:
            # تقييم المخاطر وتحديد حجم المركز ووقف الخسارة
            assessment = risk_manager.assess_signal(
                signal=signal,
                current_price=current_price,
                current_atr=current_atr,
                portfolio_balance=current_portfolio_value
            )

            if assessment.approved and assessment.target_quantity > 0:
                side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
                
                # إنشاء أمر التداول
                order = Order(
                    timestamp=current_time,
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=assessment.target_quantity,
                    stop_loss=assessment.stop_loss_price,
                    take_profit=assessment.take_profit_price
                )

                # تنفيذ الصفقة واقعياً مع السبريد والعمولة والانزلاق
                result = broker.execute_order(order, current_market_price=current_price)
                print(f"[{current_time}] نفّذ أمر {side.value} | كمية: {result.executed_quantity:.4f} | "
                      f"سعر التنفيذ: ${result.executed_price:,.2f} | عمولة: ${result.commission:.2f} | انزلاق: ${result.slippage:.2f}")

    # 5. التقرير النهائي للأداء
    final_price = processed_df.iloc[-1]['close']
    final_portfolio_value = broker.get_portfolio_value(final_price, symbol)
    net_pnl = final_portfolio_value - broker.initial_balance
    roi = (net_pnl / broker.initial_balance) * 100

    print("\n==========================================")
    print("📈 النتيجة النهائية للمحاكاة:")
    print(f"• الرصيد النهائي للمحفظة: ${final_portfolio_value:,.2f}")
    print(f"• صافي الربح / الخسارة: ${net_pnl:,.2f} ({roi:+.2f}%)")
    print(f"• إجمالي الصفقات المنفذة: {len(broker.execution_history)}")
    print("==========================================")


if __name__ == "__main__":
    run_agent_simulation()
