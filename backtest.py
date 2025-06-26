# backtest.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from risk_analysis import RiskAnalyzer
from config import Config

class Backtester:
    def __init__(self, config):
        self.cfg = config
        self.trades = []
        self.current_balance = config.INITIAL_CAPITAL
        self.in_position = False
        self.buy_price = None
        self.entry_balance = None
        self.market_condition = None

    def run(self):
        sb = datetime(self.cfg.START_BACKTEST_YEAR - self.cfg.ANALYSIS_PERIOD_YEARS, 1, 1) - timedelta(days=60)
        eb = self.cfg.END_BACKTEST_DATE + timedelta(days=7)
        df  = yf.download(self.cfg.TICKER_SYMBOL, start=sb, end=eb, progress=False)
        mdf = yf.download('^GSPC', start=sb, end=eb, progress=False)

        # Normalize
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        if isinstance(mdf.columns, pd.MultiIndex):
            mdf.columns = [c[0] for c in mdf.columns]
        df.index  = df.index.normalize()
        mdf.index = mdf.index.normalize()

        # Haftalık kapanış tarihleri
        first = datetime(self.cfg.START_BACKTEST_YEAR, 1, 1)
        weeks = df['Close'].resample('W').last().dropna().index
        weeks = [d for d in weeks if first <= d <= self.cfg.END_BACKTEST_DATE]

        for ad in weeks:
            # Bir sonraki işlem günü
            td = next(
                (d for d in pd.date_range(ad+timedelta(1), ad+timedelta(7))
                 if d in df.index and d <= self.cfg.END_BACKTEST_DATE),
                None
            )
            if td is None:
                continue

            # 1) Risk analizi ve piyasa durumu
            metrics = RiskAnalyzer.analyze_company_risk_weekly(
                df, mdf, ad, years=self.cfg.ANALYSIS_PERIOD_YEARS
            )
            if metrics is None:
                continue

            self.market_condition = metrics["Piyasa Durumu"]
            if self.market_condition == "Bull":
                profit_tgt = self.cfg.BULL_PROFIT_TARGET
                stop_loss  = self.cfg.BULL_STOP_LOSS
            else:
                profit_tgt = self.cfg.BEAR_PROFIT_TARGET
                stop_loss  = self.cfg.BEAR_STOP_LOSS

            price_open = df.loc[td, 'Open']

            # 2) Pozisyondaysa kapatma kontrolü
            if self.in_position:
                tgt_price = self.buy_price * (1 + profit_tgt)
                sl_price  = self.buy_price * (1 - stop_loss)
                if price_open >= tgt_price or price_open <= sl_price:
                    reason = "Kar Al" if price_open >= tgt_price else "Zarar Kes"
                    self._close(td, price_open, reason)

            # 3) Pozisyonda değilse açma kontrolü
            else:
                if (metrics["Volatilite Oranı"] < self.cfg.MAX_VOLATILITY_RATIO and
                    metrics["Momentum 1w"] > self.cfg.MIN_MOMENTUM_1W and
                    metrics["H3-H2 Hacim"] > self.cfg.MIN_VOLUME_CHANGE_H3H2):
                    self._open(td, price_open)

        # Test sonu kapatma
        if self.in_position:
            lastd = max(d for d in df.index if d <= self.cfg.END_BACKTEST_DATE)
            self._close(lastd, df.loc[lastd, 'Close'], "Backtest Sonu")

        return self._summary()

    def _open(self, day, price):
        adj = price * (1 + self.cfg.SLIPPAGE_RATE)
        com = self.current_balance * self.cfg.COMMISSION_RATE
        self.current_balance -= com

        self.in_position   = True
        self.buy_price     = adj
        self.entry_balance = self.current_balance
        self.trades.append({
            "Tarih": day,
            "İşlem": "AÇ",
            "Raw Fiyat": price,
            "Adj Fiyat": adj,
            "Komisyon": com,
            "Piyasa Durumu": self.market_condition,
            "Bakiye": self.current_balance
        })

    def _close(self, day, price, reason):
        adj = price * (1 - self.cfg.SLIPPAGE_RATE)
        pnl = self.entry_balance * ((adj - self.buy_price) / self.buy_price)
        self.current_balance += pnl
        com_exit = self.current_balance * self.cfg.COMMISSION_RATE
        self.current_balance -= com_exit

        self.trades.append({
            "Tarih": day,
            "İşlem": f"KAPAT ({reason})",
            "Raw Fiyat": price,
            "Adj Fiyat": adj,
            "P/L ($)": pnl,
            "P/L (%)": f"{(adj - self.buy_price)/self.buy_price:.2%}",
            "Komisyon": com_exit,
            "Piyasa Durumu": self.market_condition,
            "Bakiye": self.current_balance
        })
        self.in_position = False

    def _summary(self):
        import pandas as pd
        df_tr = pd.DataFrame(self.trades)
        total_pct = (self.current_balance - self.cfg.INITIAL_CAPITAL) / self.cfg.INITIAL_CAPITAL
        return {
            "ticker": self.cfg.TICKER_SYMBOL,
            "test_period": f"{self.cfg.START_BACKTEST_YEAR}-{self.cfg.END_BACKTEST_DATE.strftime('%Y-%m-%d')}",
            "initial_balance": self.cfg.INITIAL_CAPITAL,
            "final_balance": self.current_balance,
            "total_profit_loss_percent": total_pct,
            "total_trades": len(self.trades),
            "win_rate": None
        }, df_tr
