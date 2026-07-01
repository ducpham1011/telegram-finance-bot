import logging
from telegram import Bot
import os
from db_manager import db_manager
from data_fetcher import data_fetcher
import asyncio

logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

class AlertManager:
    @staticmethod
    async def check_alerts():
        """
        Check all active alerts in DB and send message if triggered
        """
        alerts_col = db_manager.get_collection("alerts")
        if alerts_col is None:
            logger.error("DB not connected. Cannot check alerts.")
            return

        active_alerts = list(alerts_col.find({"is_triggered": False}))
        if not active_alerts:
            return

        bot = Bot(token=TELEGRAM_TOKEN)
        
        # We cache prices in memory during one run so we don't spam APIs
        price_cache = {}
        
        for alert in active_alerts:
            symbol = alert['symbol']
            target = alert['target_price']
            condition = alert['condition']
            
            # Fetch price
            if symbol not in price_cache:
                if symbol == "GOLD":
                    price_cache[symbol] = data_fetcher.get_world_gold_price()
                elif symbol.endswith("USDT") or symbol in ["BTC", "ETH"]:
                    fetch_sym = symbol if symbol.endswith("USDT") else symbol + "USDT"
                    price_cache[symbol] = data_fetcher.get_crypto_price(fetch_sym)
                else:
                    price_cache[symbol] = data_fetcher.get_vn_stock_price(symbol)
                    
            current_price = price_cache[symbol]
            
            if current_price == 0.0:
                continue # Failed to fetch price
                
            triggered = False
            if condition == ">" and current_price > target:
                triggered = True
            elif condition == "<" and current_price < target:
                triggered = True
                
            if triggered:
                msg = f"🚨 <b>CẢNH BÁO GIÁ</b> 🚨\n\n{symbol} đã đạt điều kiện {condition} {target}!\nGiá hiện tại: <b>{current_price}</b>"
                try:
                    await bot.send_message(chat_id=alert['chat_id'], text=msg, parse_mode='HTML')
                    # Mark as triggered
                    alerts_col.update_one({"_id": alert["_id"]}, {"$set": {"is_triggered": True}})
                except Exception as e:
                    logger.error(f"Failed to send alert to {alert['chat_id']}: {e}")

alert_manager = AlertManager()
