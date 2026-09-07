import sys
from pathlib import Path
import pandas as pd

# Add STOCKLAB root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.repository_price import RepoPrice
from analytics.Metrics import Metrics
from Portfolio.Portfolio import Portfolio

rpp = RepoPrice()
ms = Metrics()


class Overlapping_Strategy:

    def __init__(self, total_capital: float, start_date: str, end_date: str, K=3):
        self.total_capital = total_capital
        self.K = K
        capital_per_portfolio = total_capital / K
        
        self.portfolios = [Portfolio(capital_per_portfolio) for _ in range(K)]
        self.start_date = start_date
        self.end_date = end_date
        self.portfolio_values = []

    def formation_J(self, symbols: list[str], start_date: str, J=6):
        # ĐÃ SỬA THỜI GIAN: Tính đủ J tháng, lùi 1 ngày để lấy ngày cuối tháng
        start_dt = pd.to_datetime(start_date)
        end_dt = start_dt + pd.DateOffset(months=J) - pd.DateOffset(days=1)
        end_date_str = end_dt.strftime("%Y-%m-%d")
        
        threshold_safe = 50_000_000
        list_liquidity = ms.avg_traded_value(symbols, start_date, end_date_str)
        
        if list_liquidity is None or list_liquidity.empty:
            return []

        liquid_stocks = list_liquidity[list_liquidity["avg_trade"] >= threshold_safe]["symbol"].tolist()
        log_return = ms.total_log_return(liquid_stocks, start_date, end_date_str)
        
        if log_return is None or log_return.empty:
            return []

        n = max(1, int(len(log_return) * 0.1))
        top_10 = log_return.sort_values(by="total log return", ascending=False).head(n)
        
        return top_10.index.tolist()

    def get_first_trading_day(self, month_start, symbols):
        month_start = pd.to_datetime(month_start)
        month_end = month_start + pd.offsets.MonthEnd(0)
        
        # ĐÃ SỬA: Quét danh sách mã để tìm ngày giao dịch (Tránh rủi ro huỷ niêm yết)
        for sym in symbols:
            price_df = rpp.get_price_btw(
                sym,
                start_date=month_start.strftime("%Y-%m-%d"),
                end_date=month_end.strftime("%Y-%m-%d")
            )
            if price_df is not None and not price_df.empty:
                return pd.to_datetime(price_df["trading_date"].iloc[0])
        return None

    def run(self, symbols: list[str], start_date: str, end_date: str):
        formation_end = pd.to_datetime(start_date) + pd.DateOffset(months=5)
        month_starts = pd.date_range(
            start=formation_end + pd.DateOffset(months=1),
            end=end_date,
            freq="MS"
        )

        for i, month_start in enumerate(month_starts):
            # Truyền toàn bộ list symbols vào thay vì chỉ symbols[0]
            current_date = self.get_first_trading_day(month_start, symbols)
            
            if current_date is None:
                print(f"\n{month_start.strftime('%Y-%m')} -> Không tìm thấy ngày giao dịch cho bất kỳ mã nào.")
                continue
                
            current_date_str = current_date.strftime("%Y-%m-%d")
            lookback_start = (current_date - pd.DateOffset(months=6)).strftime("%Y-%m-%d")
            
            best_stocks = self.formation_J(symbols, lookback_start, J=6)
            
            portfolio_index = i % self.K
            portfolio = self.portfolios[portfolio_index]
            
            print(f"\n{current_date_str} -> Portfolio {portfolio_index + 1}")
            print(f"Best stocks: {best_stocks}")

            # Chốt lời sau K tháng
            if i >= self.K:
                for symbol, quantity in list(portfolio.total_owned_stocks.items()):
                    portfolio.sell(symbol, quantity, current_date_str)

            if not best_stocks:
                continue

            capital_per_stock = portfolio.balance / len(best_stocks)

            # Mua cổ phiếu
            for symbol in best_stocks:
                price_df = rpp.get_price_btw(symbol, current_date_str, current_date_str)
                
                # ĐÃ SỬA: Check None để chống sập chương trình
                if price_df is None or price_df.empty:
                    continue
                    
                price = float(price_df["close_price"].iloc[0])
                quantity = (capital_per_stock / price) // 100 * 100
                
                if quantity > 0:
                    portfolio.buy(symbol, quantity, current_date_str)

            # Tính toán động linh hoạt theo K
            values = [pf.get_portfolio_value(current_date_str) for pf in self.portfolios]
            total_value = sum(values)
            profit = total_value - self.total_capital
            return_pct = profit / self.total_capital
            
            row = {"date": current_date_str}
            for j, val in enumerate(values):
                row[f"P{j+1}"] = val
                
            row.update({
                "total_value": total_value,
                "profit": profit,
                "return": return_pct
            })
            self.portfolio_values.append(row)
            
            portfolio_str = " | ".join([f"P{j+1}: {val:,.2f}" for j, val in enumerate(values)])
            print(f"{current_date_str} | {portfolio_str} | Total: {total_value:,.2f} | Profit: {profit:,.2f} | Return: {return_pct:.2%}")

        for portfolio in self.portfolios:
            for symbol, quantity in list(portfolio.total_owned_stocks.items()):
                # Nên dùng current_date_str của tháng cuối cùng thay vì end_date cứng để chống sập ngày nghỉ
                portfolio.sell(symbol, quantity, end_date)

        result = pd.DataFrame(self.portfolio_values)
        return result