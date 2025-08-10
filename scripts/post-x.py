#!/usr/bin/env python3
import os
import sys
import logging
import webbrowser
from dotenv import load_dotenv
import tweepy
from tweepy.errors import TweepyException

# — Logging setup —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# — Load environment variables from .env —
load_dotenv()

# — Required env vars —
TWITTER_API_KEY    = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
CLIENT_ID          = os.getenv("TWITTER_CLIENT_ID")
CLIENT_SECRET      = os.getenv("TWITTER_CLIENT_SECRET")
CALLBACK_URL       = os.getenv("TWITTER_CALLBACK_URL")  # e.g. https://<your-ngrok>.app/callback
SCOPES             = os.getenv("TWITTER_OAUTH2_SCOPES", 
                                "tweet.read tweet.write users.read").split()

# Validate env
if not all([TWITTER_API_KEY, TWITTER_API_SECRET, CLIENT_ID,
            CLIENT_SECRET, CALLBACK_URL]):
    logger.error(
        "Please set TWITTER_API_KEY, TWITTER_API_SECRET, "
        "TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET, "
        "and TWITTER_CALLBACK_URL in your .env"
    )
    sys.exit(1)

def get_oauth2_user_token():
    """
    Run OAuth2 Authorization Code flow (PKCE) to get a user token
    with tweet.write scope.
    """
    handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=CALLBACK_URL,
        scope=SCOPES,
        client_secret=CLIENT_SECRET
    )

    # 1) Direct user to authorize URL
    auth_url = handler.get_authorization_url()
    logger.info("Opening browser to: %s", auth_url)
    webbrowser.open(auth_url)

    # 2) User pastes the full callback URL with ?code=…&state=…
    redirect_response = input(
        "Paste the FULL redirect URL here (including ?code=...):\n"
    ).strip()

    # 3) Exchange for tokens
    tokens = handler.fetch_token(authorization_response=redirect_response)
    access_token = tokens.get("access_token")
    if not access_token:
        logger.error("Failed to obtain access token.")
        sys.exit(1)

    logger.info("Obtained OAuth2 user access token.")
    return access_token

def post_tweet(text: str, oauth2_token: str):
    """
    Post a tweet via v2 create_tweet with OAuth2 user-context.
    Must set user_auth=True to avoid app-only fallback.
    """
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=oauth2_token,
        wait_on_rate_limit=True
    )
    try:
        # user_auth=True forces OAuth2 User Context auth :contentReference[oaicite:2]{index=2}
        resp = client.create_tweet(text=text, user_auth=True)
        tweet_id = resp.data.get("id")
        logger.info("✔ Tweet posted successfully! id=%s", tweet_id)
    except TweepyException as e:
        logger.error("✖ Failed to post tweet: %s", e)
        sys.exit(1)

def main():
    # Step 1: Obtain OAuth2 user token
    oauth2_token = get_oauth2_user_token()

    # Step 2: Compose your message
    message = (
        "🚀 Anthropic has officially released Claude Opus 4.1, "
        "achieving 74.5% on SWE-bench and unlocking advanced agentic reasoning! #AI #Anthropic"
    )

    # Step 3: Post it
    post_tweet(message, oauth2_token)

if __name__ == "__main__":
    main()
