import time
from datetime import datetime, timedelta
from ETL.Extract import Extract_by_date, Extract_by_limit
from database.repository_stock import RepoStock
from database.repository_price import RepoPrice
from ETL.Transform import Transform_price

stock_repo = RepoStock()
price_repo = RepoPrice()


class Pipeline:
    MAX_RETRIES = 3
    MIN_INTERVAL = 6   # giây giữa mỗi lần gọi -> tối đa 10 request/phút (an toàn hơn nhiều so với 20)

    def __init__(self):
        self._last_call_time = 0

    def load(self, stocks, config):
        failed_symbols = []

        for data in stocks:
            symbol = data["symbol"]

            if not stock_repo.exist_stock(symbol=symbol):
                stock_repo.insert_stock(symbol, data["company_name"], data["exchange"])
                print(f'{symbol} is inserted into database')

            stock_id = stock_repo.get_stockID(symbol)

            df = self._extract(symbol, config)

            if df is None:
                print(f'{symbol}: bỏ qua sau {self.MAX_RETRIES} lần thử thất bại')
                failed_symbols.append(symbol)
                continue
                
            print(f'{symbol}: raw df có {len(df)} dòng')

            df = Transform_price(df)
            price_repo.insert_many_price(stock_id, df)
            print(f'{symbol}: đã lấy và lưu {len(df)} nến')

        if failed_symbols:
            print(f'\nCác mã lấy thất bại: {failed_symbols}')

        print(f'\nHoàn tất pipeline: {len(stocks) - len(failed_symbols)}/{len(stocks)} mã thành công')

    def _wait_for_slot(self):
        """Đảm bảo luôn chờ đủ MIN_INTERVAL giây kể từ lần gọi trước"""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.MIN_INTERVAL:
            time.sleep(self.MIN_INTERVAL - elapsed)
        self._last_call_time = time.time()

    def _extract(self, symbol, config):
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._wait_for_slot()

                if config["mode"] == "limit":
                    return Extract_by_limit(symbol, config["interval"], config["limit"])
                elif config["mode"] == "date":
                    return Extract_by_date(symbol, config["interval"], config["start_date"], config["end_date"])
                else:
                    raise ValueError("Invalid mode")

            except SystemExit:
                # Trường hợp vnstock tự sys.exit() khi rate-limit
                print(f'{symbol}: bị chặn cứng bởi rate-limit (SystemExit), chờ 60s...')
                time.sleep(60)

            except Exception as e:
                wait = 15 * attempt
                print(f'{symbol}: lỗi lần {attempt} ({e}) → chờ {wait}s rồi thử lại')
                time.sleep(wait)
        return None
    def _extract_update(self,symbol,config):
        sup = datetime.now().strftime("%Y-%m-%d")
        inf = price_repo.get_latest_date()['latest_date'] + timedelta(days=1)
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._wait_for_slot()
    
                if config["mode"] == "limit":
                    return Extract_by_limit(symbol, config["interval"], config["limit"])
                elif config["mode"] == "date":
                    return Extract_by_date(symbol, config["interval"],inf, sup)
                else:
                    raise ValueError("Invalid mode")
    
            except SystemExit:
                        # Trường hợp vnstock tự sys.exit() khi rate-limit
                print(f'{symbol}: bị chặn cứng bởi rate-limit (SystemExit), chờ 60s...')
                time.sleep(60)
    
            except Exception as e:
                wait = 15 * attempt
                print(f'{symbol}: lỗi lần {attempt} ({e}) → chờ {wait}s rồi thử lại')
                time.sleep(wait)
            return None
        
    def update(self,stocks,config):
        failed_symbols = []
        for data in stocks:
            symbol = data["symbol"]
    
            if not stock_repo.exist_stock(symbol=symbol):
                stock_repo.insert_stock(symbol, data["company_name"], data["exchange"])
                print(f'{symbol} is inserted into database')
        
            stock_id = stock_repo.get_stockID(symbol)
            df = self._extract_update(symbol, config)
        
            if df is None:
                print(f'{symbol}: bỏ qua sau {self.MAX_RETRIES} lần thử thất bại')
                failed_symbols.append(symbol)
                continue
        
            print(f'{symbol}: raw df có {len(df)} dòng')
        
            df = Transform_price(df)
            price_repo.insert_many_price(stock_id, df)
            print(f'{symbol}: đã lấy và lưu {len(df)} nến')
        
            if failed_symbols:
                print(f'\nCác mã lấy thất bại: {failed_symbols}')
        
        print(f'\nHoàn tất pipeline: {len(stocks) - len(failed_symbols)}/{len(stocks)} mã thành công')
