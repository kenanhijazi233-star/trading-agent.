from dataclasses import dataclass
from enum import Enum
from typing import Optional
import pandas as pd


class SignalType(Enum):
    """نوع الإشارة الصادرة من محرك الاستراتيجية"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderType(Enum):
    """نوع الأمر المرسل للمحاكي أو المنصة"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Signal:
    """
    الإشارة: ناتج محرك الاستراتيجية فقط (الاتجاه والقوة وحالة السوق)
    دون تحديد حجم اللوت أو أوامر الوقف
    """
    timestamp: pd.Timestamp
    symbol: str
    signal_type: SignalType
    strength: float           # قوة الإشارة من 0.0 إلى 1.0
    regime: str               # وصف حالة السوق (مثل TRENDING_UP أو CHOPPY)


@dataclass
class RiskAssessment:
    """ناتج محرك المخاطر بعد تدقيق الإشارة"""
    approved: bool
    reason: str               # سبب القبول أو الرفض بالتفصيل
    target_quantity: float = 0.0
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


@dataclass
class Order:
    """الأمر الجاهز للتنفيذ"""
    timestamp: pd.Timestamp
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class ExecutionResult:
    """نتيجة تنفيذ الأمر من المنصة أو المحاكي"""
    order_id: str
    symbol: str
    side: OrderSide
    executed_quantity: float
    executed_price: float
    commission: float
    slippage: float
    timestamp: pd.Timestamp
