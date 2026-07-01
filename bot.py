from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import logging
from dotenv import load_dotenv
from chart_generator import chart_generator
from db_manager import db_manager

load_dotenv('config.env')
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Chào mừng bạn đến với <b>Finance Tracker Bot</b> 📈\n\n"
        "Tôi có thể giúp bạn:\n"
        "- Đặt cảnh báo giá Crypto, Chứng khoán VN, Vàng.\n"
        "- Xem biểu đồ trực quan.\n"
        "- Nhận bản tin tổng hợp hàng ngày.\n\n"
        "Nhấn /help để xem danh sách lệnh."
    )
    await update.message.reply_html(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>Danh sách lệnh:</b>\n"
        "/chart [mã] - <i>Xem biểu đồ (VD: /chart BTC, /chart FPT, /chart GOLD)</i>\n"
        "/alert [mã] [&gt; hoặc &lt;] [giá] - <i>Đặt cảnh báo (VD: /alert BTC &gt; 90000)</i>\n"
        "/alerts - <i>Xem danh sách cảnh báo</i>\n"
        "/del_alert [id] - <i>Xóa cảnh báo</i>\n"
        "/sub_digest - <i>Đăng ký nhận bản tin ngày</i>\n"
        "/unsub_digest - <i>Hủy nhận bản tin ngày</i>"
    )
    await update.message.reply_html(help_text)

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Vui lòng cung cấp mã. VD: /chart BTC hoặc /chart FPT hoặc /chart GOLD")
        return
        
    symbol = context.args[0].upper()
    await update.message.reply_text(f"Đang tạo biểu đồ cho {symbol}, vui lòng đợi...")
    
    try:
        # Simple heuristic to determine type
        if symbol == "GOLD":
            buf = chart_generator.get_world_gold_chart()
        elif len(symbol) == 3 and not symbol.endswith("USDT"): # likely VN Stock, normally 3 chars
            # But wait, BTC is 3 chars. 
            # Let's assume if it's 3 chars and not in a known crypto list, it might be stock.
            # For simplicity, if user types BTC, we append USDT.
            if symbol in ["BTC", "ETH", "BNB", "SOL"]:
                buf = chart_generator.get_crypto_chart(symbol + "USDT")
            else:
                buf = chart_generator.get_vn_stock_chart(symbol)
        else: # Crypto pair like BTCUSDT
            buf = chart_generator.get_crypto_chart(symbol)
            
        await update.message.reply_photo(photo=buf)
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        await update.message.reply_text(f"Không thể tạo biểu đồ cho {symbol}. Lỗi: {str(e)}")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Sai cú pháp. VD: /alert BTC > 90000")
        return
        
    symbol = context.args[0].upper()
    condition = context.args[1]
    try:
        target_price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Giá mục tiêu phải là số.")
        return
        
    if condition not in [">", "<"]:
        await update.message.reply_text("Điều kiện phải là '>' hoặc '<'")
        return
        
    chat_id = update.effective_chat.id
    alerts_col = db_manager.get_collection("alerts")
    
    if alerts_col is not None:
        alert_doc = {
            "chat_id": chat_id,
            "symbol": symbol,
            "condition": condition,
            "target_price": target_price,
            "is_triggered": False
        }
        res = alerts_col.insert_one(alert_doc)
        await update.message.reply_text(f"Đã đặt cảnh báo: {symbol} {condition} {target_price}. ID: {str(res.inserted_id)[-4:]}")
    else:
        await update.message.reply_text("Lỗi kết nối database.")

async def list_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    alerts_col = db_manager.get_collection("alerts")
    
    if alerts_col is not None:
        alerts = list(alerts_col.find({"chat_id": chat_id, "is_triggered": False}))
        if not alerts:
            await update.message.reply_text("Bạn không có cảnh báo nào đang hoạt động.")
            return
            
        msg = "<b>Các cảnh báo của bạn:</b>\n"
        for a in alerts:
            msg += f"- ID: <code>{str(a['_id'])[-4:]}</code> | {a['symbol']} {a['condition']} {a['target_price']}\n"
        await update.message.reply_html(msg)
    else:
        await update.message.reply_text("Lỗi kết nối database.")

async def sub_digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs_col = db_manager.get_collection("subscribers")
    if subs_col is not None:
        subs_col.update_one({"chat_id": chat_id}, {"$set": {"subscribed": True}}, upsert=True)
        await update.message.reply_text("✅ Đã đăng ký nhận bản tin hàng ngày thành công!")
    else:
        await update.message.reply_text("Lỗi kết nối database.")

async def unsub_digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs_col = db_manager.get_collection("subscribers")
    if subs_col is not None:
        subs_col.update_one({"chat_id": chat_id}, {"$set": {"subscribed": False}}, upsert=True)
        await update.message.reply_text("✅ Đã hủy đăng ký bản tin hàng ngày.")
    else:
        await update.message.reply_text("Lỗi kết nối database.")

def create_bot_app():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is missing!")
        return None
        
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("alerts", list_alerts_command))
    app.add_handler(CommandHandler("sub_digest", sub_digest_command))
    app.add_handler(CommandHandler("unsub_digest", unsub_digest_command))
    return app

bot_app = create_bot_app()
