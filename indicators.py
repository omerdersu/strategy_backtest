# indicators.py
import pandas as pd
import pandas_ta as ta
from config import Config

class Indicators:
    @staticmethod
    def calculate_mavilim(
        close_series: pd.Series,
        fmal_period: int = Config.MAVILIM_FMAL,
        smal_period: int = Config.MAVILIM_SMAL
    ) -> pd.Series:
        """
        Metastock formülüne göre iç içe WMA kullanarak Mavilim hesaplar.
        """
        if not isinstance(close_series, pd.Series) or close_series.empty:
            return pd.Series(dtype=float)

        tmal  = fmal_period + smal_period
        fomal = smal_period + tmal
        ftmal = tmal + fomal
        simal = fomal + ftmal

        try:
            k2 = ta.wma(close_series, length=fmal_period)
            k3 = ta.wma(k2, length=smal_period) if isinstance(k2, pd.Series) else None
            k4 = ta.wma(k3, length=tmal)      if isinstance(k3, pd.Series) else None
            k5 = ta.wma(k4, length=fomal)     if isinstance(k4, pd.Series) else None
            k6 = ta.wma(k5, length=ftmal)     if isinstance(k5, pd.Series) else None
            k7 = ta.wma(k6, length=simal)     if isinstance(k6, pd.Series) else None
        except Exception:
            return pd.Series(dtype=float)

        return (k7.dropna() if isinstance(k7, pd.Series) else pd.Series(dtype=float))
