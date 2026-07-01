import yfinance as yf
from vnstock import stock_historical_data
import datetime
import mplfinance as mpf
import pandas as pd
import requests
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    @staticmethod
    def get_crypto_chart(symbol: str, interval: str = "1d", limit: int = 60) -> BytesIO:
        """
        Generate candlestick chart for Crypto using yfinance
        interval can be: '1h', '1d', '1wk'
        """
        if symbol.endswith("USDT"):
            yf_symbol = symbol[:-4] + "-USD"
        else:
            yf_symbol = symbol + "-USD"
            
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period="3mo", interval=interval)
        if df.empty:
            raise ValueError(f"No data found for {symbol}.")
            
        df = df.tail(limit)
        return ChartGenerator._plot_candlestick(df, f"{symbol.upper()} Crypto ({interval})")

    @staticmethod
    def get_world_gold_chart(interval: str = "1d", limit: int = 60) -> BytesIO:
        """
        Generate line chart for World Gold (GC=F)
        """
        ticker = yf.Ticker("GC=F")
        # '1mo' is 1 month of daily data
        df = ticker.history(period="3mo", interval=interval)
        if df.empty:
            raise ValueError("No data found for Gold.")
        
        df = df.tail(limit)
        return ChartGenerator._plot_line(df, "World Gold (GC=F)")

    @staticmethod
    def get_vn_stock_chart(symbol: str, limit: int = 60) -> BytesIO:
        """
        Generate candlestick chart for VN Stock
        """
        now = datetime.datetime.now()
        start_date = (now - datetime.timedelta(days=limit * 2)).strftime("%Y-%m-%d") # Fetch extra to guarantee enough trading days
        end_date = now.strftime("%Y-%m-%d")
        
        df = stock_historical_data(symbol=symbol.upper(), start_date=start_date, end_date=end_date, resolution='1D', type='stock')
        if df is None or df.empty:
            raise ValueError(f"No data found for stock {symbol}.")
            
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        # Rename columns to match mplfinance expectations
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        # vnstock returns lower case columns
        if 'Open' not in df.columns: # fallback if the new version changed
            df.columns = [c.capitalize() for c in df.columns]

        df = df.tail(limit)
        return ChartGenerator._plot_candlestick(df, f"{symbol.upper()} - VN Stock (Daily)")

    @staticmethod
    def _plot_candlestick(df: pd.DataFrame, title: str) -> BytesIO:
        # Standardize columns
        df.columns = [c.capitalize() for c in df.columns]
        
        buf = BytesIO()
        mpf.plot(
            df, 
            type='candle', 
            volume=True, 
            style='yahoo', 
            title=title, 
            savefig=dict(fname=buf, format='png', bbox_inches='tight', dpi=150)
        )
        buf.seek(0)
        return buf

    @staticmethod
    def _plot_line(df: pd.DataFrame, title: str) -> BytesIO:
        df.columns = [c.capitalize() for c in df.columns]
        
        buf = BytesIO()
        mpf.plot(
            df, 
            type='line', 
            style='yahoo', 
            title=title, 
            savefig=dict(fname=buf, format='png', bbox_inches='tight', dpi=150)
        )
        buf.seek(0)
        return buf

chart_generator = ChartGenerator()
