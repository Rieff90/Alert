
import json
import os
from datetime import datetime
from utils import get_klines, add_mas, detect_breakout, support_pullback_zone, detect_candle_pattern, detect_chart_pattern
import requests
import pandas as pd
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Load pair list
with open("pairs.json") as f:
    PAIRS = json.load(f)

# Load previous signals
signal_file = "signal_state.json"
if os.path.exists(signal_file):
    with open(signal_file, "r") as f:
        LAST_SIGNAL = json.load(f)
else:
    LAST_SIGNAL = {}

NEW_SIGNALS = {}
alert_lines = []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

for symbol in PAIRS:
    try:
        df = get_klines(symbol)
        df = add_mas(df)
        ma7, ma25, ma99 = df["MA7"].iloc[-1], df["MA25"].iloc[-1], df["MA99"].iloc[-1]
        price = df["close"].iloc[-1]

        breakout_high, breakout_low, prev_high, prev_low = detect_breakout(df)
        support, (pull_low, pull_high) = support_pullback_zone(df)
        candle = detect_candle_pattern(df)
        chart = detect_chart_pattern(df)

        signal_parts = []

        if breakout_high:
            signal_parts.append(f"🚀 Breakout High ${prev_high:.2f}")
        if breakout_low:
            signal_parts.append(f"🔻 Breakout Low ${prev_low:.2f}")
        if price >= pull_low and price <= pull_high:
            signal_parts.append(f"📉 Pullback zone ${pull_low:.2f}–${pull_high:.2f}")
        if ma7 > ma25 > ma99:
            signal_parts.append("🟢 MA Uptrend (MA7>25>99)")
        if candle:
            signal_parts.append(f"🕯️ {candle}")
        if chart:
            signal_parts.append(f"📐 {chart}")

        combined_signal = " | ".join(signal_parts)

        if combined_signal:
            if symbol not in LAST_SIGNAL or LAST_SIGNAL[symbol] != combined_signal:
                line = f"{symbol}: {combined_signal}"
                alert_lines.append(line)
                NEW_SIGNALS[symbol] = combined_signal

    except Exception as e:
        print(f"Error processing {symbol}: {e}")

# Send message if any new signals
if alert_lines:
    header = f"📊 [ALERT - {datetime.now().strftime('%d %b %Y %H:%M')}] 🔔\n"
    message = header + "\n" + "\n".join(alert_lines)
    send_telegram(message)

# Save updated signal state
with open(signal_file, "w") as f:
    json.dump({**LAST_SIGNAL, **NEW_SIGNALS}, f, indent=2)
