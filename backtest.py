
# backtest.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from risk_analysis import RiskAnalyzer

class Backtester:
    def __init__(self, config):
        self.cfg = config
        self.trades = []
        self.current_balance = config.INITIAL_CAPITAL
        self.in_position = False
        self.buy_date = None
        self.buy_price = None
        self.entry_balance = None

    def run(self):
        # Tüm veri setini tek sefer indir
        start_buffer = datetime(self.cfg.START_BACKTEST_YEAR - self.cfg.ANALYSIS_PERIOD_YEARS, 1, 1) - timedelta(days=60)
        end_buffer   = self.cfg.END_BACKTEST_DATE + timedelta(days=7)
        company_df = yf.download(self.cfg.TICKER_SYMBOL, start=start_buffer, end=end_buffer, progress=False)
        market_df  = yf.download('^GSPC', start=start_buffer, end=end_buffer, progress=False)

        if company_df.empty or market_df.empty:
            raise RuntimeError("Veri alınamadı!")

        # MultiIndex varsa normalize et
        if isinstance(company_df.columns, pd.MultiIndex):
            company_df.columns = [c[0] for c in company_df.columns]
        if isinstance(market_df.columns, pd.MultiIndex):
            market_df.columns = [c[0] for c in market_df.columns]

        company_df.index = company_df.index.normalize()
        market_df.index  = market_df.index.normalize()

        # Haftalık periyotlar
        first_date = datetime(self.cfg.START_BACKTEST_YEAR, 1, 1)
        weekly = company_df['Close'].resample('W').last().dropna().index
        weekly = [d for d in weekly if first_date <= d <= self.cfg.END_BACKTEST_DATE]

        # Backtest döngüsü
        for analysis_date in weekly:
            # Bir sonraki iş günü al
            trade_day = next(
                (d for d in pd.date_range(analysis_date + timedelta(1), analysis_date + timedelta(7))
                 if d in company_df.index and d <= self.cfg.END_BACKTEST_DATE),
                None
            )
            if not trade_day:
                continue

            raw_price = company_df.loc[trade_day, 'Open']

            if self.in_position:
                # Kar al / stop loss kontrolleri
                target = self.buy_price * (1 + self.cfg.PROFIT_TARGET_PERCENT)
                stop   = self.buy_price * (1 - self.cfg.STOP_LOSS_PERCENT)
                if raw_price >= target or raw_price <= stop:
                    reason = "Kar Al" if raw_price >= target else "Zarar Durdur"
                    self._close(trade_day, raw_price, reason)
            else:
                # Alış sinyallerini config üzerinden kontrol et
                metrics = RiskAnalyzer.analyze_company_risk_weekly(
                    company_df, market_df, analysis_date, years=self.cfg.ANALYSIS_PERIOD_YEARS
                )
                if (metrics and
                    metrics["Volatilite Oranı"] < self.cfg.MAX_VOLATILITY_RATIO and
                    metrics["Momentum 1w"] > self.cfg.MIN_MOMENTUM_1W and
                    metrics["H3-H2 Hacim"] > self.cfg.MIN_VOLUME_CHANGE_H3H2):
                    self._open(trade_day, raw_price)

        # Kapanış pozisyonu varsa kapat
        if self.in_position:
            last_day = max(d for d in company_df.index if d <= self.cfg.END_BACKTEST_DATE)
            close_price = company_df.loc[last_day, 'Close']
            self._close(last_day, close_price, "Backtest Sonu")

        return self._summary()

    def _open(self, day, price):
        # Slippage ve komisyon uygula
        adj_price = price * (1 + self.cfg.SLIPPAGE_RATE)
        commission = self.current_balance * self.cfg.COMMISSION_RATE
        self.current_balance -= commission

        self.in_position   = True
        self.buy_date      = day
        self.buy_price     = adj_price
        self.entry_balance = self.current_balance
        self.trades.append({
            "Tarih": day,
            "İşlem": "AÇ",
            "Fiyat (Raw)": price,
            "Fiyat (Adj)": adj_price,
            "Komisyon": commission,
            "Bakiye": self.current_balance
        })

    def _close(self, day, price, reason):
        # Slippage ve komisyon çıkışı
        adj_close = price * (1 - self.cfg.SLIPPAGE_RATE)
        gross_pl   = self.entry_balance * ((adj_close - self.buy_price) / self.buy_price)
        self.current_balance += gross_pl
        commission_exit = (self.entry_balance + gross_pl) * self.cfg.COMMISSION_RATE
        self.current_balance -= commission_exit

        pl_pct = (adj_close - self.buy_price) / self.buy_price
        self.trades.append({
            "Tarih": day,
            "İşlem": f"KAPAT ({reason})",
            "Fiyat (Raw)": price,
            "Fiyat (Adj)": adj_close,
            "P/L (%)": f"{pl_pct:.2%}",
            "Brüt P/L": gross_pl,
            "Komisyon": commission_exit,
            "Bakiye": self.current_balance
        })
        self.in_position = False

    def _summary(self):
        df_trades    = pd.DataFrame(self.trades)
        total_pl_pct = (self.current_balance - self.cfg.INITIAL_CAPITAL) / self.cfg.INITIAL_CAPITAL
        total_trades = len(self.trades)
        win_rate     = None

        return {
            "ticker": self.cfg.TICKER_SYMBOL,
            "test_period": f"{self.cfg.START_BACKTEST_YEAR}-{self.cfg.END_BACKTEST_DATE.strftime('%Y-%m-%d')}",
            "initial_balance": self.cfg.INITIAL_CAPITAL,
            "final_balance": self.current_balance,
            "total_profit_loss_percent": total_pl_pct,
            "total_trades": total_trades,
            "win_rate": win_rate
        }, df_trades