import os
import requests
import socket
print(socket.gethostbyname("api.lunarcrush.com"))

# === CONFIG ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
LUNARCRUSH_API_KEY = os.environ.get("LUNARCRUSH_API_KEY")  # Optional



# === TELEGRAM ALERT ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.post(url, json=payload)
        print(f"📨 Telegram response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# === LUNARCRUSH FETCH ===
def fetch_top_altrank(limit=5):
    url = "https://api.lunarcrush.com/v4"
    params = {
        "data": "assets",
        "key": os.environ["LUNARCRUSH_API_KEY"],
        "sort": "alt_rank",
        "limit": limit
    }

    try:
        r = requests.get(url, params=params)
        print("🔍 Raw response text:", r.text[:200])  # For debugging
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"❌ Failed to fetch AltRank data: {e}")
        return []



# === FORMAT ALERT ===
def alert_top_altrank_coins():
    coins = fetch_top_altrank(limit=5)
    if not coins:
        send_telegram_alert("⚠️ No AltRank data found.")
        return

    msg = ["🏆 Top Coins by AltRank:\n"]
    for c in coins:
        msg.append(
            f"${c['symbol']} — AltRank: {c['alt_rank']} | "
            f"GalaxyScore: {c.get('galaxy_score', 'N/A')} | "
            f"Price: ${c.get('price', 'N/A'):.4f}"
        )
    send_telegram_alert("\n".join(msg))

# === MAIN ===
if __name__ == "__main__":
    send_telegram_alert("🟢 Fetching top AltRank coins from LunarCrush...")
    alert_top_altrank_coins()
