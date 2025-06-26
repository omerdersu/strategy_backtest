import pandas as pd
import numpy as np

class RiskAnalyzer:
    @staticmethod
    def analyze_company_risk_weekly(
        company_df: pd.DataFrame,
        market_df: pd.DataFrame,
        analysis_date,
        years: int = 3
    ) -> dict:
        # Başlangıç tarihini belirle ve slice üzerinden copy alın
        start_date = analysis_date - pd.Timedelta(days=years * 365 + 30)
        comp = company_df.loc[start_date:analysis_date].copy()
        mkt  = market_df.loc[start_date:analysis_date].copy()
        if comp.empty or mkt.empty:
            return None

        # Haftalık getiri
        weekly_close = comp['Close'].resample('W').last().pct_change().dropna()

        # Günlük getiri
        comp['Daily_Return'] = comp['Close'].pct_change()
        mkt['Daily_Return']  = mkt['Close'].pct_change()
        comp = comp.dropna(subset=['Daily_Return','Volume'])
        mkt  = mkt.dropna(subset=['Daily_Return'])

        # Ortak tarihler
        common_daily = comp.index.intersection(mkt.index)
        comp_daily   = comp.loc[common_daily, 'Daily_Return']
        mkt_daily    = mkt.loc[common_daily, 'Daily_Return']

        # Haftalık ortak
        mkt_weekly = mkt['Close'].resample('W').last().pct_change().dropna()
        common_week = weekly_close.index.intersection(mkt_weekly.index)
        if len(common_week) < 2:
            return None
        weekly_ret = weekly_close.loc[common_week]

        # Metrikler
        exp_ret       = weekly_ret.mean()
        vol_week      = weekly_ret.std()
        last_week_vol = comp_daily.tail(5).std() * np.sqrt(5) if len(comp_daily) >= 5 else np.nan

        # Momentum
        close_ser = comp['Close']
        m1 = (close_ser.iloc[-1] - close_ser.iloc[-5]) / close_ser.iloc[-5] if len(close_ser) >= 5 else np.nan
        m4 = (close_ser.iloc[-1] - close_ser.iloc[-20]) / close_ser.iloc[-20] if len(close_ser) >= 20 else np.nan

        # Hacim değişimleri
        weekly_vol = comp['Volume'].resample('W').mean().dropna()
        h_changes  = [np.nan, np.nan, np.nan]
        if len(weekly_vol) >= 4:
            last4 = weekly_vol.iloc[-4:]
            for i in range(3):
                if last4.iloc[i] != 0:
                    h_changes[i] = (last4.iloc[i+1] - last4.iloc[i]) / last4.iloc[i]

        # Beta
        cov  = comp_daily.cov(mkt_daily)
        var  = mkt_daily.var()
        beta = cov/var if var and not np.isnan(cov) else np.nan

        return {
            "Şirket": None,
            "Beklenen Getiri": exp_ret,
            "Volatilite": vol_week,
            "Son 1 Haftalık Vol": last_week_vol,
            "Volatilite Oranı": (last_week_vol/vol_week) if vol_week else np.nan,
            "Momentum 1w": m1,
            "Momentum 4w": m4,
            "H4-H3 Hacim": h_changes[2],
            "H3-H2 Hacim": h_changes[1],
            "H2-H1 Hacim": h_changes[0],
            "Beta": beta
        }