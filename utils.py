
import requests
import pandas as pd
import numpy as np

# === Ambil data Klines dari Binance ===
def get_klines(symbol, interval="1d", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df = df.astype({
        "open": float, "high": float, "low": float, "close": float, "volume": float
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["timestamp", "open", "high", "low", "close", "volume"]]

# === Moving Averages ===
def add_mas(df):
    df["MA7"] = df["close"].rolling(window=7).mean()
    df["MA25"] = df["close"].rolling(window=25).mean()
    df["MA99"] = df["close"].rolling(window=99).mean()
    return df

# === Breakout Detection ===
def detect_breakout(df, window=20):
    prev_high = df["high"].iloc[-window:-1].max()
    prev_low = df["low"].iloc[-window:-1].min()
    breakout_high = df["close"].iloc[-1] > prev_high
    breakout_low = df["close"].iloc[-1] < prev_low
    return breakout_high, breakout_low, prev_high, prev_low

# === Support/Pullback Zone ===
def support_pullback_zone(df, window=20):
    lows = df["low"].rolling(window).min()
    supports = lows[lows == lows]
    support = supports.iloc[-1]
    pullback_zone = (support * 0.985, support * 1.015)
    return support, pullback_zone

# === Candlestick Patterns ===
def detect_candle_pattern(df):
    o, h, l, c = df.iloc[-2][["open", "high", "low", "close"]]
    if c > o and (c - o) > 2 * (o - l):
        return "Bullish Engulfing"
    elif o > c and (o - c) > 2 * (h - o):
        return "Bearish Engulfing"
    elif abs(c - o) < 0.002 * o:
        return "Doji"
    elif c > o and (h - c) <= 0.1 * (c - o) and (o - l) >= 2 * (h - c):
        return "Hammer"
    elif o > c and (o - l) <= 0.1 * (o - c) and (h - c) >= 2 * (o - l):
        return "Shooting Star"
    return None

# === Chart Pattern (Double Bottom - simple version) ===
def detect_chart_pattern(df):
    closes = df["close"].values[-10:]
    if closes[-1] > closes[-2] > closes[-3] and min(closes[-6:-3]) == closes[-4]:
        return "Double Bottom"
    return None

# === EMA200 ===
def add_ema200(df):
    df["EMA200"] = df["close"].ewm(span=200, adjust=False).mean()
    return df

# === RSI ===
def add_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# === Bollinger Bands ===
def add_bollinger_bands(df, window=20):
    ma = df["close"].rolling(window).mean()
    std = df["close"].rolling(window).std()
    df["BB_upper"] = ma + 2 * std
    df["BB_lower"] = ma - 2 * std
    df["BB_basis"] = ma
    return df

# === MACD ===
def add_macd(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df

# === ADX ===
def add_adx(df, period=14):
    df["TR"] = df[["high", "low", "close"]].max(axis=1) - df[["high", "low", "close"]].min(axis=1)
    df["+DM"] = np.where((df["high"].diff() > df["low"].diff()) & (df["high"].diff() > 0), df["high"].diff(), 0)
    df["-DM"] = np.where((df["low"].diff() > df["high"].diff()) & (df["low"].diff() > 0), df["low"].diff(), 0)
    tr14 = df["TR"].rolling(window=period).sum()
    plus_dm14 = df["+DM"].rolling(window=period).sum()
    minus_dm14 = df["-DM"].rolling(window=period).sum()
    plus_di14 = 100 * (plus_dm14 / tr14)
    minus_di14 = 100 * (minus_dm14 / tr14)
    dx = 100 * abs(plus_di14 - minus_di14) / (plus_di14 + minus_di14)
    df["ADX"] = dx.rolling(window=period).mean()
    return df

# === Volume Moving Average ===
def add_volume_ma(df, period=20):
    df["vol_ma"] = df["volume"].rolling(window=period).mean()
    return df
