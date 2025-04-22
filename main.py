import os
import requests
from flask import Flask

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
LUNARCRUSH_API_KEY = os.environ["LUNARCRUSH_API_KEY"]

app = Flask(__name__)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def fetch_top_altrank(limit=5):
    url = "https://api.lunarcrush.com/v4"
    params = {
        "data": "assets",
        "key": LUNARCRUSH_API_KEY,
        "sort": "alt_rank",
        "limit": limit
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("data", [])

@app.route("/run", methods=["GET"])
def trigger_bot():
    try:
        coins = fetch_top_altrank()
        if not coins:
            send_telegram_alert("⚠️ No AltRank data found.")
            return "No data"

        msg = ["🏆 Top Coins by AltRank:\n"]
        for c in coins:
            msg.append(
                f"${c['symbol']} — AltRank: {c['alt_rank']}, "
                f"GalaxyScore: {c.get('galaxy_score', 'N/A')}, "
                f"Price: ${c.get('price', 0):.4f}, "
                f"Market Cap: ${c.get('market_cap', 0):,.0f}"
            )
        send_telegram_alert("\n".join(msg))
        return "✅ Alert sent"
    except Exception as e:
        send_telegram_alert(f"❌ Error: {e}")
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
