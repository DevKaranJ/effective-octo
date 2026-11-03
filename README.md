# NSE WhaleFlow + Trendline (TL) Production Suite (v2.0 Pro)

> **100% Manual Trade Execution • Read-Only Market Data Architecture**

A high-performance intraday order-flow terminal and local read-only FastAPI data bridge for Indian equity markets (NSE).

---

## 📦 What's Inside

1. **`nse_whale_intraday_terminal.html`** — Self-contained interactive web terminal featuring:
   - Order-flow footprint & tick delta analysis
   - Cumulative Volume Delta (CVD)
   - 5-Depth Iceberg order detection
   - Session Volume Profile (POC / VAH / VAL)
   - Institutional order block identification
   - Dynamic trendline & liquidity sweep detector
   - Configurable risk parameters (14-bar ATR stop + 0.05% slippage buffer)
   - Manual trade alert dispatcher (Telegram integration)

2. **`server.py`** — Local FastAPI Read-Only Data Bridge:
   - Official `nseindia.com` Session Cookie Manager (`/api/allIndices` + India VIX)
   - Yahoo Finance intraday OHLCV (`.NS`)
   - Read-only adapters for Fyers / Angel One SmartAPI
   - Zero trade execution endpoints for maximum account safety

3. **`requirements.txt`** — Core Python dependencies.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- A modern web browser

### 2. Setup Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Data Bridge
```bash
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Launch Terminal
Open your browser to:
- Direct local bridge: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Or open `nse_whale_intraday_terminal.html` locally and click **🔌 Poll Localhost Bridge** in the *Footprint, Live Bridge & Guards* tab.

---

## 🔒 Safety Architecture
- **Strictly Read-Only**: ZERO automated order placement, modification, or cancellation logic exists in this server.
- **Manual Execution Only**: Any signals, alerts, or insights generated are intended strictly for manual discretionary execution.
