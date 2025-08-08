# check_twitter_tokens.py

import os
import sys
import tweepy
from tweepy.errors import TweepyException
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()  

def check_oauth1():
    print("→ Testing OAuth 1.0a (API Key/Secret + Access Token/Secret)…")
    try:
        auth = tweepy.OAuth1UserHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)
        user = api.verify_credentials()
        if user and user.id:
            print(f"✔ OAuth1 Success: authenticated as @{user.screen_name}")
        else:
            print("✖ OAuth1 Failed: verify_credentials returned no user")
    except TweepyException as e:
        print(f"✖ OAuth1 Exception: {e}")
        return False
    return True

def check_bearer():
    print("\n→ Testing OAuth 2.0 Bearer Token…")
    try:
        client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))
        resp = client.get_user(username="TwitterDev")
        if resp.data and resp.data.id:
            print(f"✔ Bearer Success: able to lookup @TwitterDev (id={resp.data.id})")
        else:
            print("✖ Bearer Failed: get_user returned no data")
    except TweepyException as e:
        print(f"✖ Bearer Exception: {e}")
        return False
    return True

if __name__ == "__main__":
    missing = [var for var in [
        "TWITTER_API_KEY", "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET",
        "TWITTER_BEARER_TOKEN"
    ] if not os.getenv(var)]
    if missing:
        print("Please set these env vars first (from .env or export):", ", ".join(missing))
        sys.exit(1)

    ok1 = check_oauth1()
    ok2 = check_bearer()

    if not ok1:
        print("\n>> OAuth 1.0a is failing. Likely culprit: API_KEY/SECRET or ACCESS_TOKEN/SECRET.")
    if not ok2:
        print("\n>> Bearer Token test failed. Likely culprit: BEARER_TOKEN.")
    if ok1 and ok2:
        print("\n🎉 All tokens appear to be valid.")
