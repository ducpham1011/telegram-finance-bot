from fastapi import FastAPI, Request, HTTPException
import logging
import os
from dotenv import load_dotenv

load_dotenv('config.env')

app = FastAPI(title="Telegram Finance Bot API")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CRON_SECRET = os.environ.get("CRON_SECRET", "default_secret")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Finance Bot API is running"}

import asyncio
from bot import bot_app
from alert_manager import alert_manager
from telegram import Update

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Endpoint for Telegram Webhook"""
    try:
        data = await request.json()
        if bot_app is not None:
            update = Update.de_json(data, bot_app.bot)
            await bot_app.initialize()
            await bot_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/cron/check_alerts")
async def cron_check_alerts(request: Request):
    """Cron endpoint to check prices and send alerts"""
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info("Running alert check cron job...")
    await alert_manager.check_alerts()
    return {"status": "ok", "message": "Alert check complete"}

from digest_manager import digest_manager

@app.get("/api/cron/daily_digest")
async def cron_daily_digest(request: Request):
    """Cron endpoint to send daily digest"""
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info("Running daily digest cron job...")
    await digest_manager.send_daily_digest()
    return {"status": "ok", "message": "Daily digest sent"}

# Required for Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
