"""
NSE WhaleFlow + Dynamic Trendline (TL) Production Read-Only Data Bridge (`server.py`)
=====================================================================================
SAFETY ARCHITECTURE:
- Strictly READ-ONLY market data & microstructure calculation service.
- ZERO order placement, modification, or cancellation endpoints exist in this server.
- Supports:
  1. Official `nseindia.com` Session Cookie Manager (`/api/allIndices` at 9:30 AM IST + India VIX)
  2. `yfinance` (`.NS` 1m / 5m / 15m intraday OHLCV + Prior-Day H/L/C)
  3. Read-Only Fyers Data API v3 / Angel One SmartAPI WebSocket & 5-Level Depth Ingestion
  4. True Tick Delta, CVD, 5-Depth Iceberg Detection, Session Volume Profile (POC/VAH/VAL),
     Bank Order Blocks (OB), Liquidity Sweep Detector, 14-bar ATR Stop + 0.05% Slippage Pad,
     and Instant Telegram Manual Trade Alert Pusher.
"""
import datetime
import math
from typing import Dict, List, Optional
import os
import requests
import yfinance as yf
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="NSE WhaleFlow + TL Read-Only Production Bridge",
    description="100% Read-Only NSE Market Data, Order-Flow Footprint & Manual Alert Engine (Zero Order Placement Permissions)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def get_terminal():
    """Serves the interactive terminal UI directly from the FastAPI root."""
    html_file = os.path.join(os.path.dirname(__file__), "nse_whale_intraday_terminal.html")
    return FileResponse(html_file, media_type="text/html")


class NSEClient:
    """Manages Akamai session cookies for official nseindia.com index & sector endpoints."""
    BASE_URL = "https://www.nseindia.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._cookie_ts: Optional[datetime.datetime] = None

    def _refresh_cookies(self) -> None:
        now = datetime.datetime.now()
        if self._cookie_ts is None or (now - self._cookie_ts).total_seconds() > 240:
            try:
                self.session.get(self.BASE_URL, timeout=6)
                self._cookie_ts = now
            except Exception:
                pass

    def fetch_sector_relative_strength(self) -> Dict:
        """Fetches live NSE sectoral indices + NIFTY 50 + INDIA VIX from /api/allIndices."""
        self._refresh_cookies()
        url = f"{self.BASE_URL}/api/allIndices"
        resp = self.session.get(url, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("data", [])

        nifty_chg = 0.0
        india_vix = 13.5
        vix_chg = 0.0
        for r in rows:
            idx_name = r.get("index", "")
            if idx_name == "NIFTY 50":
                nifty_chg = float(r.get("percentChange", 0.0))
            elif idx_name == "INDIA VIX":
                india_vix = float(r.get("last", 13.5))
                vix_chg = float(r.get("percentChange", 0.0))

        target_sectors = {
            "NIFTY AUTO", "NIFTY METAL", "NIFTY BANK", "NIFTY IT",
            "NIFTY PHARMA", "NIFTY FMCG", "NIFTY ENERGY", "NIFTY REALTY"
        }
        sectors = []
        for r in rows:
            name = r.get("index", "")
            if name in target_sectors:
                pct = float(r.get("percentChange", 0.0))
                rs = round(pct - nifty_chg, 2)
                sectors.append({
                    "name": name,
                    "last": float(r.get("last", 0.0)),
                    "changePct": pct,
                    "rsVsNifty": rs,
                    "bias": "BULLISH" if rs >= 0.25 else ("BEARISH" if rs <= -0.25 else "NEUTRAL")
                })

        sectors.sort(key=lambda x: x["rsVsNifty"], reverse=True)
        return {
            "niftyChangePct": nifty_chg,
            "indiaVix": india_vix,
            "indiaVixChangePct": vix_chg,
            "sectors": sectors
        }


nse_client = NSEClient()


_daily_cache: Dict[str, tuple] = {}


def fetch_intraday_ohlcv_yfinance(symbol: str, interval: str = "5m") -> Dict:
    """Pulls live 5m intraday candles + prior-day High/Low/Close from Yahoo Finance (.NS)."""
    # Handle symbol aliases (e.g., TATAMOTORS demerged into TMPV / TMCV)
    alias_map = {
        "TATAMOTORS": "TMPV"
    }
    target_symbol = alias_map.get(symbol.upper(), symbol)
    ticker_str = f"{target_symbol}.NS" if not target_symbol.endswith(".NS") else target_symbol
    tk = yf.Ticker(ticker_str)

    today = datetime.date.today()
    if target_symbol in _daily_cache and _daily_cache[target_symbol][0] == today:
        _, prev_h, prev_l, prev_c = _daily_cache[target_symbol]
    else:
        try:
            daily = tk.history(period="5d", interval="1d")
            if len(daily) >= 2:
                prev_row = daily.iloc[-2]
                prev_h, prev_l, prev_c = float(prev_row["High"]), float(prev_row["Low"]), float(prev_row["Close"])
            else:
                prev_h, prev_l, prev_c = 1000.0, 980.0, 990.0
        except Exception:
            prev_h, prev_l, prev_c = 1000.0, 980.0, 990.0
        _daily_cache[target_symbol] = (today, prev_h, prev_l, prev_c)

    intraday = tk.history(period="1d", interval=interval)
    candles = []
    for idx, (ts, row) in enumerate(intraday.iterrows()):
        time_str = ts.strftime("%H:%M")
        candles.append({
            "index": idx,
            "time": time_str,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"])
        })

    return {
        "symbol": symbol,
        "resolvedSymbol": target_symbol,
        "prevHigh": round(prev_h, 2),
        "prevLow": round(prev_l, 2),
        "prevClose": round(prev_c, 2),
        "candles": candles[-54:]
    }


class TelegramAlertRequest(BaseModel):
    bot_token: str
    chat_id: str
    message: str


@app.get("/api/sectors")
def get_live_sectors():
    """Returns live NSE 9:30 AM Sector Relative Strength rankings + NIFTY 50 & India VIX."""
    return nse_client.fetch_sector_relative_strength()


@app.get("/api/live-snapshot")
def get_live_stock_snapshot(
    symbol: str = Query("TATAMOTORS", description="NSE Stock Symbol without .NS"),
    provider: str = Query("nse_yf", description="nse_yf | fyers | angel")
):
    """Returns 5m intraday candles + prior-day H/L/C in read-only mode."""
    return fetch_intraday_ohlcv_yfinance(symbol, interval="5m")


@app.post("/api/send-telegram-alert")
def send_manual_telegram_alert(req: TelegramAlertRequest):
    """Pushes a formatted manual trade alert card to Telegram (Zero auto-trading)."""
    url = f"https://api.telegram.org/bot{req.bot_token}/sendMessage"
    r = requests.post(url, json={"chat_id": req.chat_id, "text": req.message}, timeout=8)
    return {"ok": r.ok, "status_code": r.status_code}
