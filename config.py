# config.py
from datetime import datetime

class Config:
    TICKER_SYMBOL        = "FN"
    START_BACKTEST_YEAR  = 2020
    END_BACKTEST_DATE    = datetime(2025, 6, 25)
    ANALYSIS_PERIOD_YEARS= 5
    INITIAL_CAPITAL      = 100000.0

    # Slippage ve komisyon
    SLIPPAGE_RATE   = 0.001
    COMMISSION_RATE = 0.0025

    # MAVILIM indikatörü periyotları
    MAVILIM_FMAL = 3
    MAVILIM_SMAL = 5

    # Alış sinyalleri için eşikler
    MAX_VOLATILITY_RATIO   = 1.0
    MIN_MOMENTUM_1W        = 0.0
    MIN_VOLUME_CHANGE_H3H2 = 0.0

    # ===== BOĞA / AYI piyasa hedefleri =====
    BEAR_PROFIT_TARGET = 0.05   # Ayı piyasası: %10
    BEAR_STOP_LOSS     = 0.07   # Ayı piyasası: %4
    BULL_PROFIT_TARGET = 0.40   # Boğa piyasası: %50
    BULL_STOP_LOSS     = 0.1   # Boğa piyasası: %10
