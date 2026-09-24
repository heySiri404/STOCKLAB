from datetime import date
from math import isfinite
from numbers import Real
import numpy as np
import pandas as pd

from database.repository_price import RepoPrice
rpp = RepoPrice()

class Portfolio:
    def __init__(self, capital: float):
        if isinstance(capital, bool) or not isinstance(capital, Real):
            raise TypeError("capital must be a number")

        if not isfinite(float(capital)) or capital < 0:
            raise ValueError(
                "capital must be a finite, non-negative number"
            )
        self.initial_capital = capital
        self.balance = capital
        self.total_owned_stocks: dict[str, float] = {}
        self.trade_history: list[dict] = []
        self.total_short_stocks: dict[str, float] = {}

    def buy(self, symbols:list[str], quantities: list[int], trading_date:str):
            bought_stocks = 0
            for symbol,quantity in zip(symbols,quantities):
                if quantity <= 0:
                    raise ValueError("quantity must be positive")
                
                price_df = rpp.get_price_btw(symbol,start_date=trading_date,end_date=trading_date)
                if price_df is None and price_df['close_price'].empty:
                    print(f"Skipped {symbol}: No price data on {trading_date}.")
                    continue
                price = price_df['close_price'].iloc[0]
                cur_cost = price*quantity

                if cur_cost > self.balance:
                    print(f"Balance is not enough to buy :{symbol}")
                    continue

                else: 
                    bought_stocks +=1
                    print(f"successfully bought {symbol}, current number stocks bought :{bought_stocks}")
                    old_quantity = self.total_owned_stocks.get(symbol, 0)
                    new_quantity = old_quantity + quantity
                    self.balance -= cur_cost
                    self.total_owned_stocks[symbol] = new_quantity
                    self.trade_history.append({
                            "symbol": symbol,
                            "quantity": quantity,
                            "asset_type": "stock",
                            "side": "BUY",
                            "trading_date": trading_date,
                            "price": price,
                            "cost": cur_cost
                        })
    
    def sell(self, symbol:str, quantity: float, trading_date:str):
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        close_price = rpp.get_price_btw(symbol,start_date=trading_date,end_date=trading_date)["close_price"].iloc[0]
        old_quantity = self.total_owned_stocks.get(symbol, 0)

        if quantity > old_quantity:
          print("Stock is not enough")
          return None
        else:
              cur_income = close_price*quantity
              self.balance += cur_income
              self.total_owned_stocks[symbol] -= quantity

              self.trade_history.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "asset_type": "stock",
                    "side": "SELL",
                    "trading_date": trading_date,
                    "price": close_price,
                    "income": cur_income

              })

        if self.total_owned_stocks[symbol] == 0:
            del self.total_owned_stocks[symbol]

    def get_portfolio_value(self, trading_date: str):
        total_value = 0
        stocks_owned = []
        quantity_owned = []
        for symbol,quantity in self.total_owned_stocks.items():
            stocks_owned.append(symbol)
            quantity_owned.append(quantity)

        prices = rpp.get_close_prices(symbols=stocks_owned,start_date=trading_date,end_date=trading_date)
        for i in range(len(self.total_owned_stocks)):
            total_value += prices[stocks_owned[i]].iloc[0] * quantity_owned[i]

        return self.balance + total_value

    def get_pnl(self, trading_date: str):
        current_value = self.get_portfolio_value(trading_date)
        return current_value - self.initial_capital

    def log_return(self,start_date,end_date):
        n_returns = []
        trading_days = pd.date_range(start=start_date, end=end_date, freq='B')
        for date in trading_days:
            str_date = date.strftime('%Y-%m-%d')
            n_returns.append(self.get_portfolio_value(str_date))
        
        n_returns = np.array(n_returns)

        l_returns = np.log(n_returns[1:]/n_returns[:-1])*100
        return l_returns
        
    def short(self, symbol: str, quantity: float, trading_date: str):
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        open_price = rpp.get_price_btw(
            symbol,
            start_date=trading_date,
            end_date=trading_date
        )["close_price"].iloc[0]

        income = open_price * quantity

        old_quantity = self.total_short_stocks.get(symbol, 0)
        new_quantity = old_quantity + quantity

        # Bán khống → nhận tiền
        self.balance += income

        self.total_short_stocks[symbol] = new_quantity

        self.trade_history.append({
            "symbol": symbol,
            "quantity": quantity,
            "asset_type": "stock",
            "side": "SHORT",
            "trading_date": trading_date,
            "price": open_price,
            "income": income
        })
    def cover(self, symbol: str, quantity: float, trading_date: str):
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        old_quantity = self.total_short_stocks.get(symbol, 0)

        if quantity > old_quantity:
            print("Short position is not enough")
            return None

        close_price = rpp.get_price_btw(
            symbol,
            start_date=trading_date,
            end_date=trading_date
        )["close_price"].iloc[0]

        cost = close_price * quantity

        # Mua lại để đóng short
        self.balance -= cost

        self.total_short_stocks[symbol] -= quantity

        self.trade_history.append({
            "symbol": symbol,
            "quantity": quantity,
            "asset_type": "stock",
            "side": "COVER",
            "trading_date": trading_date,
            "price": close_price,
            "cost": cost
        })

        if self.total_short_stocks[symbol] == 0:
            del self.total_short_stocks[symbol]