import pandas as pd
import numpy as np


class MarketDataLoader:
    """
    مسؤول عن معالجة البيانات وحساب المؤشرات الفنية
    وفلترة حالة السوق (Market Regime) دون تسريب مستقبلي.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def prepare_features(self) -> pd.DataFrame:
        # التأكد من الترتيب الزمني للشموع
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df.sort_values('timestamp', inplace=True)
            self.df.reset_index(drop=True, inplace=True)

        # 1. المتوسطات المتحركة الأسية (Trend Indicators)
        self.df['ema_fast'] = self.df['close'].ewm(span=12, adjust=False).mean()
        self.df['ema_slow'] = self.df['close'].ewm(span=26, adjust=False).mean()

        # 2. مؤشر القوة النسبية (RSI - 14)
        delta = self.df['close'].diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # 3. مؤشر متوسط المدى الحقيقي (ATR - 14) لقياس التذبذب والمخاطرة
        high_low = self.df['high'] - self.df['low']
        high_close = (self.df['high'] - self.df['close'].shift(1)).abs()
        low_close = (self.df['low'] - self.df['close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr'] = tr.rolling(window=14).mean()

        # 4. تحديد حالة السوق (Regime Detection)
        # نسبة تباعد المتوسطات عن السعر لتقييم قوة الاتجاه
        self.df['trend_spread'] = (self.df['ema_fast'] - self.df['ema_slow']) / self.df['close']
        
        # تصنيف حالة السوق
        conditions = [
            (self.df['trend_spread'] > 0.005) & (self.df['close'] > self.df['ema_fast']),
            (self.df['trend_spread'] < -0.005) & (self.df['close'] < self.df['ema_fast']),
        ]
        choices = ['TRENDING_UP', 'TRENDING_DOWN']
        self.df['regime'] = np.select(conditions, choices, default='CHOPPY')

        # حذف الصفوف الأولى التي تحتوي قيم فارغة (NaN) بسبب حسابات النوافذ
        self.df.dropna(inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        
        return self.df
      
