# main.py
from config import Config
from backtest import Backtester

if __name__ == "__main__":
    bt = Backtester(Config)
    overall_results, trades_df = bt.run()
    cols = ['Tarih', 'İşlem', 'Bakiye'] + [c for c in trades_df.columns if c not in ('Tarih', 'İşlem', 'Bakiye')]
    trades_df = trades_df[cols]
    if overall_results:
        print("\n--- KÜMÜLATİF BACKTEST ÖZETİ ---")
        print(f"Hisse Senedi: {overall_results['ticker']}")
        print(f"Test Dönemi: {overall_results['test_period']}")
        print(f"Başlangıç Bakiyesi: {overall_results['initial_balance']:,.2f} $")
        print(f"Final Bakiye: {overall_results['final_balance']:,.2f} $")
        print(f"Toplam Kar/Zarar: {overall_results['total_profit_loss_percent']:.2%}")
        print(f"Toplam İşlem Sayısı: {overall_results['total_trades']}")
        if overall_results['win_rate'] is not None:
            print(f"Kazanma Oranı: {overall_results['win_rate']:.2f}%")
        print("\n--- İşlem Detayları ---")
        print(trades_df.to_string(index=False))