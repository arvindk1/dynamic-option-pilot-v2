# backend/api/routes/_twitter_client.py
import os, tweepy

def get_client() -> tweepy.Client:
    # use your working OAuth1 tokens for now
    return tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=True,
    )
