
# risk_analysis.py
import pandas as pd
import numpy as np
from indicators import Indicators
from config import Config

class RiskAnalyzer:
    @staticmethod
    def analyze_company_risk_weekly(
        company_df: pd.DataFrame,
        market_df: pd.DataFrame,
        analysis_date,
        years: int = 3
    ) -> dict:
        """
        Şirket ve piyasa verilerini kullanarak haftalık risk metriklerini hesaplar ve
        piyasa durumunu (Bull/Bear) belirler.
        """
        # Zaman penceresini belirle (years yıl + 30 gün)
        start_date = analysis_date - pd.Timedelta(days=years * 365 + 30)
        comp = company_df.loc[start_date:analysis_date].copy()
        mkt  = market_df.loc[start_date:analysis_date].copy()
        if comp.empty or mkt.empty:
            return None

        # Haftalık getiri
        weekly_ret = comp['Close'].resample('W').last().pct_change().dropna()

        # Günlük getirileri hesapla
        comp['Daily_Return'] = comp['Close'].pct_change()
        mkt['Daily_Return']  = mkt['Close'].pct_change()
        comp = comp.dropna(subset=['Daily_Return', 'Volume'])
        mkt  = mkt.dropna(subset=['Daily_Return'])

        # Ortak günlük tarihler
        common_daily = comp.index.intersection(mkt.index)
        if common_daily.empty:
            return None
        comp_daily = comp.loc[common_daily, 'Daily_Return']
        mkt_daily  = mkt.loc[common_daily, 'Daily_Return']

        # Haftalık ortak tarihler
        mkt_weekly  = mkt['Close'].resample('W').last().pct_change().dropna()
        common_week = weekly_ret.index.intersection(mkt_weekly.index)
        if len(common_week) < 2:
            return None
        weekly_ret = weekly_ret.loc[common_week]

        # Risk metrikleri
        exp_ret       = weekly_ret.mean()
        vol_week      = weekly_ret.std()
        last_week_vol = comp_daily.tail(5).std() * np.sqrt(5) if len(comp_daily) >= 5 else np.nan

        # Momentum
        close_ser = comp['Close']
        m1 = (close_ser.iloc[-1] - close_ser.iloc[-5]) / close_ser.iloc[-5] if len(close_ser) >= 5 else np.nan
        m4 = (close_ser.iloc[-1] - close_ser.iloc[-20]) / close_ser.iloc[-20] if len(close_ser) >= 20 else np.nan

        # Hacim değişimleri
        vol_series = comp.loc[common_daily, 'Volume']
        weekly_avg_volumes = vol_series.resample('W').mean().dropna()
        cw4_3 = cw3_2 = cw2_1 = np.nan
        if len(weekly_avg_volumes) >= 4:
            last4 = weekly_avg_volumes.iloc[-4:]
            if last4.iloc[-2] != 0:
                cw4_3 = (last4.iloc[-1] - last4.iloc[-2]) / last4.iloc[-2]
            if last4.iloc[-3] != 0:
                cw3_2 = (last4.iloc[-2] - last4.iloc[-3]) / last4.iloc[-3]
            if last4.iloc[-4] != 0:
                cw2_1 = (last4.iloc[-3] - last4.iloc[-4]) / last4.iloc[-4]

        # Beta hesaplama
        cov = comp_daily.cov(mkt_daily)
        var = mkt_daily.var()
        beta = cov / var if var and not np.isnan(cov) else np.nan

        # Piyasa durumunu belirle (Bull/Bear) mavilim ile
        # analysis_date kapanış fiyatı
        current_close = comp['Close'].iloc[-1]
        mav_series = Indicators.calculate_mavilim(
            company_df['Close'],
            Config.MAVILIM_FMAL,
            Config.MAVILIM_SMAL
        )
        try:
            mav_val = mav_series.loc[analysis_date]
        except KeyError:
            mav_val = mav_series[:analysis_date].iloc[-1] if not mav_series.empty else np.nan
        market_condition = 'Bull' if not np.isnan(mav_val) and current_close >= mav_val else 'Bear'

        return {
            "Şirket": None,
            "Beklenen Getiri": exp_ret,
            "Volatilite": vol_week,
            "Son 1 Haftalık Vol": last_week_vol,
            "Volatilite Oranı": (last_week_vol / vol_week) if vol_week else np.nan,
            "Momentum 1w": m1,
            "Momentum 4w": m4,
            "H4-H3 Hacim": cw4_3,
            "H3-H2 Hacim": cw3_2,
            "H2-H1 Hacim": cw2_1,
            "Beta": beta,
            "Piyasa Durumu": market_condition
        }