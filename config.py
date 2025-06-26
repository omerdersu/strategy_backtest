from datetime import datetime

class Config:
    # Backtest için genel ayarlar
    TICKER_SYMBOL = "AMZN"
    START_BACKTEST_YEAR = 2020
    END_BACKTEST_DATE = datetime(2025, 6, 25)
    ANALYSIS_PERIOD_YEARS = 5
    INITIAL_CAPITAL = 100000.0
    PROFIT_TARGET_PERCENT = 0.30
    STOP_LOSS_PERCENT = 0.05
    SLIPPAGE_RATE = 0.001
    COMMISSION_RATE = 0.0025
    # Alış sinyalleri için eşikler
    MAX_VOLATILITY_RATIO = 1.3  # Maksimum volatilite oranı
    MIN_MOMENTUM_1W = 0.0  # Minimum 1 haftalık momentum
    MIN_VOLUME_CHANGE_H3H2 = 0.05  # Minimum H3-H2 hacim değişimi