from database.connection import getConnection, getEngine
from sqlalchemy import text, bindparam
from psycopg2.extras import execute_values
import pandas as pd

class RepoPrice:
    def insert_price(self,stock_id, trading_date, open_price, high, low, close_price,volume):
        conn = None
        cur = None
        try:
            conn = getConnection()
            cur  = conn.cursor()
            sql = """ INSERT INTO daily_prices(stock_id,trading_date,open_price,high,low,close_price,volume) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (stock_id, trading_date) DO NOTHING
                """
            cur.execute(sql,(stock_id, trading_date, open_price, high, low, close_price,volume))
            conn.commit()
        except Exception as e: 
            if conn is not None:
                conn.rollback()
            print(e)
        finally:
            if conn:
                conn.close()
            if cur:
                cur.close()

    def get_price_all(self,symbol):
        conn = None
        try:
            conn = getConnection()
            sql ="""SELECT
                    dp.trading_date,
                    dp.open_price,
                    dp.high,
                    dp.low,
                    dp.close_price,
                    dp.volume
                    FROM daily_prices dp
                    JOIN stocks s ON dp.stock_id = s.id
                    WHERE s.symbol = :symbol
                    ORDER BY dp.trading_date
                     """      
            df = pd.read_sql(text(sql),getEngine(),params={"symbol":symbol}) 
            return df
        except Exception as e:
            print(e)
            return None
        finally:
            if conn:
                conn.close()

    def get_price_btw(self,symbol,start_date: str, end_date:str): #year-month-date (2999-02-02)
        conn = None
        try:
            conn = getConnection()
            sql = """SELECT
                    dp.trading_date,
                    dp.open_price,
                    dp.high,
                    dp.low,
                    dp.close_price,
                    dp.volume
                    FROM daily_prices dp
                    JOIN stocks s ON dp.stock_id = s.id
                    WHERE s.symbol = :symbol
                        AND dp.trading_date BETWEEN :start_date AND :end_date
                    ORDER BY dp.trading_date
                     """
            df = pd.read_sql(text(sql),getEngine(), params={"symbol":symbol,"start_date":start_date,"end_date":end_date})
            return df
        except Exception as e:
            print(e)
            return None
        finally:
            if conn:
                conn.close()

    def get_price_limit(self, symbol, limit):
        conn = None
        try:
            conn = getConnection()
            sql ="""SELECT
                    dp.trading_date,
                    dp.open_price,
                    dp.high,
                    dp.low,
                    dp.close_price,
                    dp.volume
                    FROM daily_prices dp
                    JOIN stocks s ON dp.stock_id = s.id
                    WHERE s.symbol = :symbol
                    ORDER BY dp.trading_date ASC
                    LIMIT :limit
                     """      
            df = pd.read_sql(text(sql),getEngine(),params={"symbol":symbol,"limit":limit}) 
            return df
        except Exception as e:
            print(e)
            return None
        finally:
            if conn:
                conn.close()

    def insert_many_price(self,stock_id,df):
        conn = None
        cur = None
        try:
            conn = getConnection()
            cur = conn.cursor()
            sql =""" INSERT INTO daily_prices
            (
                stock_id,
                trading_date,
                open_price,
                high,
                low,
                close_price,
                volume
            )
            VALUES %s
            ON CONFLICT (stock_id, trading_date)
            DO NOTHING"""
            records = (
                (
                    stock_id,
                    row.time,
                    row.open,
                    row.high,
                    row.low,
                    row.close,
                    row.volume
                )
                for row in df.itertuples(index=False)
            )
            execute_values(cur, sql, records)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(e)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def get_avg_traded_value(self, symbols, start_date, end_date):
        sql = text("""
            SELECT
                s.symbol,
                AVG(dp.close_price * dp.volume) AS avg_trade
            FROM daily_prices dp
            JOIN stocks s ON dp.stock_id = s.id
            WHERE s.symbol IN :symbols
              AND dp.trading_date BETWEEN :start_date AND :end_date
            GROUP BY s.symbol
            ORDER BY s.symbol
        """).bindparams(
            bindparam("symbols", expanding=True)
        )

        return pd.read_sql(
            sql,
            getEngine(),
            params={
                "symbols": list(symbols),
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def get_close_prices(self, symbols, start_date, end_date):
        """Fetch close prices for all symbols with one database query."""
        sql = text("""
            SELECT
                s.symbol,
                dp.trading_date,
                dp.close_price
            FROM daily_prices dp
            JOIN stocks s ON dp.stock_id = s.id
            WHERE s.symbol IN :symbols
              AND dp.trading_date BETWEEN :start_date AND :end_date
            ORDER BY dp.trading_date, s.symbol
        """).bindparams(
            bindparam("symbols", expanding=True)
        )

        price_df =  pd.read_sql(
            sql,
            getEngine(),
            params={
                "symbols": list(symbols),
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        price_df["trading_date"] = pd.to_datetime(price_df["trading_date"])

        price_df = price_df.pivot(
            index="trading_date",
            columns="symbol",
            values="close_price",
                )

        price_df.columns.name = None

        return price_df
        

    def get_latest_date(self):
            """Fetch latest_date query."""
            sql = text("""
                SELECT MAX(trading_date) AS latest_date
                FROM daily_prices
            """)
    
            return pd.read_sql(
                sql,
                getEngine(),
            )