import numpy as np
import pandas as pd
from database.repository_price import RepoPrice

rpp = RepoPrice()

class Metrics:
    @staticmethod
    def _validate_symbols(symbols: list[str],minimum: int = 2,) -> list[str]:
        symbols = list(symbols)

        if len(symbols) < minimum:
            raise ValueError(f"Give at least {minimum} symbol(s)")

        if len(symbols) != len(set(symbols)):
            raise ValueError("Symbols must not contain duplicates")

        return symbols

    def _get_close_price_matrix(self,symbols: list[str],start_date: str,end_date: str,) -> pd.DataFrame:
        """
        Load all requested close prices with one database query.

        The result has trading dates as the index and one column per symbol.
        Missing dates are retained here and removed by callers when they need
        dates shared by every symbol.
        """
        data = rpp.get_close_prices(symbols, start_date, end_date)

        if data is None or data.empty:
            raise ValueError(f"No price data found for: {symbols}")

        data = data.dropna(subset=["symbol", "trading_date", "close_price"])
        found_symbols = set(data["symbol"].unique())
        missing_symbols = set(symbols) - found_symbols

        if missing_symbols:
            raise ValueError(
                f"No price data found for: {sorted(missing_symbols)}"
            )

        prices = (
            data.pivot(
                index="trading_date",
                columns="symbol",
                values="close_price",
            )
            .sort_index()
            .reindex(columns=symbols)
            .astype(float)
        )

        return prices

    def log_return_list(self,symbols : list[str], start_date: str, end_date:str)-> pd.DataFrame:
        symbols = self._validate_symbols(symbols)
        close_prices = self._get_close_price_matrix(
            symbols,
            start_date,
            end_date,
        ).dropna(how="any")

        if len(close_prices) < 3:
            raise ValueError("Not enough shared trading dates")
        if(close_prices <=0).any().any():
            raise ValueError("Close prices must be positive for log returns")
        log_R = np.log(close_prices/close_prices.shift(1))*100

        return log_R

    def log_return_single(self,symbol: str, start_date:str,end_date:str) -> pd.DataFrame:
        symbol = self._validate_symbols([symbol], minimum=1)[0]
        prices = self._get_close_price_matrix(
            [symbol],
            start_date,
            end_date,
        ).dropna(how="any")

        if len(prices) < 3:
            raise ValueError("Not enough trading dates")
        if (prices <= 0).any().any():
            raise ValueError("Close prices must be positive for log returns")

        log_R = np.log(prices/prices.shift(1))*100
        return log_R
        
    def total_log_return(self, symbols: list[str], start_date:str, end_date:str):
        log_return = self.log_return_list(symbols,start_date,end_date).dropna()
        total_sum =  pd.DataFrame(log_return.sum()).rename(columns={0:"total log return"})
        return total_sum

    def avg_traded_value(self, symbols:list, start_date:str, end_date:str):
        symbols = self._validate_symbols(symbols)

        result = rpp.get_avg_traded_value(
            symbols,
            start_date,
            end_date,
        )

        missing = set(symbols) - set(result["symbol"])

        if missing:
            raise ValueError(f"No price data found for: {sorted(missing)}")

        # Preserve the original symbol order.
        return (
            result.set_index("symbol")
            .loc[symbols]
            .reset_index()
        )

    def return_votality(self,symbols:list[str],start_date:str, end_date:str):
        symbols = self._validate_symbols(symbols)
        returns = self.log_return_list(symbols,start_date,end_date)
        return pd.DataFrame(returns.var()).rename(columns={0:"VLR"})

    def return_std(self,symbols:list[str],start_date:str, end_date:str):
        symbols = self._validate_symbols(symbols)
        returns = self.log_return_list(symbols,start_date,end_date)
        return pd.DataFrame(returns.std()).rename(columns={0:"STDR"})
    
        
    def corr(self,symbols : list[str],start_date:str,end_date:str) -> pd.DataFrame:
        log_R = self.log_return_list(symbols,start_date,end_date)
        return log_R.corr(method ="pearson")

    def autocorrelation(self, returns: np.ndarray, lag_k:int):
        if lag_k < 0:
            raise ValueError("lag_k must be non-negative")

        if lag_k >= len(returns):
            raise ValueError("lag_k must be smaller than len(returns)")
        
        m = returns.mean()
        t = np.sum((returns[lag_k:] - m)*(returns[:-lag_k]-m))
        d = np.sum((returns-m)**2)
        return t/d
