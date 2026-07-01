import requests
import yfinance as yf
from vnstock import stock_historical_data
import datetime
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    @staticmethod
    def get_crypto_price(symbol: str) -> float:
        """
        Fetch current price from Binance.
        Symbol should be like 'BTCUSDT'
        """
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return float(data.get("price", 0))
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return 0.0

    @staticmethod
    def get_world_gold_price() -> float:
        """
        Fetch World Gold Price (GC=F) using yfinance
        """
        try:
            ticker = yf.Ticker("GC=F")
            # Fast get of current price
            fast_info = ticker.fast_info
            return float(fast_info.last_price)
        except Exception as e:
            logger.error(f"Error fetching world gold price: {e}")
            return 0.0

    @staticmethod
    def get_vn_stock_price(symbol: str) -> float:
        """
        Fetch latest VN Stock price using vnstock.
        It uses historical data of the current day.
        """
        try:
            now = datetime.datetime.now()
            start_date = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            df = stock_historical_data(symbol=symbol.upper(), start_date=start_date, end_date=end_date, resolution='1D', type='stock')
            if df is not None and not df.empty:
                return float(df.iloc[-1]['close'])
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching VN stock price for {symbol}: {e}")
            return 0.0

    @staticmethod
    def get_vn_gold_price() -> dict:
        """
        Fetch VN Gold Price (SJC) by parsing XML from sjc.com.vn
        Returns a dict: {'buy': float, 'sell': float}
        """
        url = "https://sjc.com.vn/xml/tygiavang.xml"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            
            # Find the SJC 1L, 10L, 1KG item (usually the first one in Hồ Chí Minh)
            city = root.find('.//city[@name="Hồ Chí Minh"]')
            if city is not None:
                item = city.find('.//item[@type="Vàng SJC 1L - 10L - 1KG"]')
                if item is not None:
                    buy = float(item.get('buy', 0)) * 1000000  # Usually given in millions or hundred thousands, actually XML gives like '81.5000' meaning 81,500,000
                    # Let's check format. It's often "81.5000". We want the raw value.
                    buy_raw = item.get('buy', '0').replace(',', '.')
                    sell_raw = item.get('sell', '0').replace(',', '.')
                    
                    return {
                        'buy': float(buy_raw) * 1000000 if float(buy_raw) < 1000 else float(buy_raw),
                        'sell': float(sell_raw) * 1000000 if float(sell_raw) < 1000 else float(sell_raw)
                    }
            return {'buy': 0.0, 'sell': 0.0}
        except Exception as e:
            logger.error(f"Error fetching VN gold price: {e}")
            return {'buy': 0.0, 'sell': 0.0}

data_fetcher = DataFetcher()
