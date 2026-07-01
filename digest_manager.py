import logging
from telegram import Bot
import os
from db_manager import db_manager
from data_fetcher import data_fetcher

logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

class DigestManager:
    @staticmethod
    async def send_daily_digest():
        """
        Generate and send daily digest to all subscribed users
        """
        subs_col = db_manager.get_collection("subscribers")
        if subs_col is None:
            logger.error("DB not connected. Cannot send digest.")
            return

        subscribers = list(subs_col.find({"subscribed": True}))
        if not subscribers:
            return

        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Fetch data for digest
        btc_price = data_fetcher.get_crypto_price("BTCUSDT")
        world_gold = data_fetcher.get_world_gold_price()
        vn_gold = data_fetcher.get_vn_gold_price()
        vnindex = data_fetcher.get_vn_stock_price("VNINDEX") # VNINDEX is often supported by vnstock
        
        msg = "🌅 <b>BẢN TIN TÀI CHÍNH HÀNG NGÀY</b> 🌅\n\n"
        msg += f"🔸 <b>Bitcoin (BTC):</b> {btc_price:,.2f} USDT\n"
        msg += f"🔸 <b>Vàng Thế giới:</b> {world_gold:,.2f} USD/oz\n"
        if vn_gold['buy'] > 0:
            msg += f"🔸 <b>Vàng SJC (M/B):</b> {vn_gold['buy']/1000000:.2f} / {vn_gold['sell']/1000000:.2f} Triệu VND\n"
        
        if vnindex > 0:
            msg += f"🔸 <b>VN-Index:</b> {vnindex:,.2f} điểm\n"
            
        msg += "\n<i>Chúc bạn một ngày đầu tư thành công!</i> 🚀"
        
        for sub in subscribers:
            try:
                await bot.send_message(chat_id=sub['chat_id'], text=msg, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to send digest to {sub['chat_id']}: {e}")

digest_manager = DigestManager()
