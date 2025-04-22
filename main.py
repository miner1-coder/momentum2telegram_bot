import os
import requests, re, time
from datetime import datetime
from replit import db

# === CONFIG ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TWITTER_API_KEY = os.environ["TWITTER_API_KEY"]
TWITTER_SEARCH_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
HEADERS = {"x-api-key": TWITTER_API_KEY}
SLEEP_INTERVAL_MINUTES = 15

# === ALERTING ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# === TEXT PARSING ===
def extract_cashtags(tweet_text):
    return re.findall(r"\$[A-Z]{2,10}", tweet_text.upper())

# === PAGINATED TWEET FETCH WITH DEBUG ===
def get_trending_tweets(max_pages=5):
    all_tweets = []
    cursor = None

    for page in range(max_pages):
        params = {"query": "$BTC"}
        if cursor:
            params["cursor"] = cursor

        print(f"🔄 Fetching page {page + 1}...")
        try:
            r = requests.get(TWITTER_SEARCH_URL, headers=HEADERS, params=params)
            data = r.json()
            print("📦 RAW RESPONSE:")
            print(data)
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")
            break

        tweets = data.get("data") or data.get("statuses") or data.get("tweets") or []
        print(f"📥 Page returned {len(tweets)} tweets")
        all_tweets.extend(tweets)

        cursor = data.get("cursor")
        if not cursor:
            break
        time.sleep(1)  # prevent rate limit

    coin_data = {}
    for tweet in all_tweets:
        text = tweet.get("text") or tweet.get("full_text") or ""
        likes = tweet.get("favorite_count", 0)
        retweets = tweet.get("retweet_count", 0)
        engagement = likes + retweets

        print(f"📝 Tweet: {text}")
        cashtags = extract_cashtags(text)
        if cashtags:
            print(f"🔖 Found cashtags: {cashtags}")

        for tag in cashtags:
            coin = tag[1:]  # remove $
            if coin not in coin_data:
                coin_data[coin] = {"mentions": 0, "engagement": 0}
            coin_data[coin]["mentions"] += 1
            coin_data[coin]["engagement"] += engagement

    print(f"✅ Coins parsed: {list(coin_data.keys())}")
    return coin_data

# === MOMENTUM DETECTION ===
def compare_with_previous(current_data):
    alerts = []
    for coin, data in current_data.items():
        previous = db.get(coin, {"mentions": 0, "engagement": 0})
        prev_mentions = previous["mentions"]
        prev_engagement = previous["engagement"]

        growth_mentions = ((data["mentions"] - prev_mentions) / prev_mentions * 100) if prev_mentions else 0
        growth_engagement = ((data["engagement"] - prev_engagement) / prev_engagement * 100) if prev_engagement else 0

        db[coin] = data  # store current for next run

        if growth_mentions > 100 and growth_engagement > 200:
            alert = f"🚨 ${coin} is surging!\nMentions ↑ {growth_mentions:.1f}%\nEngagement ↑ {growth_engagement:.1f}%"
            alerts.append(alert)

    return alerts

def send_top_3_summary(current_data):
    if not current_data:
        return

    sorted_coins = sorted(
        current_data.items(),
        key=lambda item: (item[1]["mentions"], item[1]["engagement"]),
        reverse=True
    )

    top_coins = sorted_coins[:3]
    lines = ["🏆 Top Coins This Run:"]
    for i, (coin, data) in enumerate(top_coins, start=1):
        lines.append(f"{i}. ${coin} — {data['mentions']} mentions, {data['engagement']} engagement")

    message = "\n".join(lines)
    send_telegram_alert(message)


# === MAIN RUNNER ===
def main():
    print(f"📡 Fetching Twitter activity...")
    trending = get_trending_tweets()
    print(f"🔍 Parsed {len(trending)} coins")

    alerts = compare_with_previous(trending)
    for alert in alerts:
        send_telegram_alert(alert)
        print(alert)

    send_top_3_summary(trending)

    print("✅ Cycle complete")

# === LOOP ===
if __name__ == "__main__":
    while True:
        print(f"\n⏱️ Run at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        try:
            main()
        except Exception as e:
            print(f"⚠️ ERROR: {e}")
            send_telegram_alert(f"⚠️ Momentum bot error: {e}")
        print(f"💤 Sleeping {SLEEP_INTERVAL_MINUTES} min...\n" + "-" * 40)
        time.sleep(SLEEP_INTERVAL_MINUTES * 60)
