# NSE WhaleFlow + Trendline (TL) Production Suite (v2.0 Pro)

## 100% Manual Trade Execution • Read-Only Market Data Architecture
This production suite contains:
1. `nse_whale_intraday_terminal.html` — The self-contained interactive terminal with all **12 Institutional Upgrades** built in.
2. `server.py` — The local FastAPI Read-Only Data Bridge (`nseindia.com` `/api/allIndices` + `yfinance` `.NS` intraday OHLCV + Fyers/Angel One read-only adapter + Telegram Manual Alert pusher).
3. `requirements.txt` — Python dependencies.

## Quick Start (Local Live NSE Data Mode)
```bash
pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
Then open `nse_whale_intraday_terminal.html` in your browser, go to the **Footprint, Live Bridge & Guards** tab, and click **🔌 Poll Localhost Bridge**.
