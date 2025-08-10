#!/usr/bin/env python3
"""
Post to X (Twitter) using either:
  - OAuth 1.0a user auth (legacy tokens), OR
  - OAuth 2.0 (PKCE) user auth with a local callback server.

Auto-picks the mode based on env vars, or set AUTH_MODE=oauth1 / oauth2.

Dependencies:
  pip install tweepy python-dotenv

Usage:
  python post_x.py
"""

import os
import sys
import json
import time
import queue
import logging
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
import tweepy
from tweepy.errors import TweepyException

# ────────────────────── Logging ──────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("post_x")

# ────────────────────── Message to post ──────────────────────
MESSAGE = (
    "🚀 It’s here — OpenAI GPT-5\n"
    "Smarter. Faster. More adaptable.\n"
    "From lightning-quick answers to deep, multi-step reasoning — all in one model.\n"
    "Copilot & Apple Intelligence are already on board.\n\n"
    "The AI game just leveled up.\n"
    "#GPT5 #AI #OpenAI "
)

# ────────────────────── Env ──────────────────────
load_dotenv()

AUTH_MODE = (os.getenv("AUTH_MODE") or "").strip().lower()  # "oauth1" or "oauth2" (optional)

# OAuth1 (legacy tokens)
O1_API_KEY = os.getenv("TWITTER_API_KEY")
O1_API_SECRET = os.getenv("TWITTER_API_SECRET")
O1_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
O1_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OAuth2 (PKCE)
O2_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
O2_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")  # optional if your app is public client
O2_CALLBACK_URL_RAW = os.getenv("TWITTER_CALLBACK_URL")
O2_SCOPES = (os.getenv("TWITTER_OAUTH2_SCOPES")
             or "tweet.read tweet.write users.read offline.access").split()

LOCAL_HOST = os.getenv("LOCAL_CALLBACK_HOST", "127.0.0.1")
LOCAL_PORT = int(os.getenv("LOCAL_CALLBACK_PORT", "8765"))
LOCAL_PATH = os.getenv("LOCAL_CALLBACK_PATH", "/callback")  # must match portal if you use local callback

# ────────────────────── Helpers ──────────────────────
def _log_x_error(e: Exception):
    resp = getattr(e, "response", None)
    if resp is not None:
        try:
            log.error("X API response: %s", json.dumps(resp.json(), indent=2))
        except Exception:
            log.error("X API status=%s text=%s", getattr(resp, "status_code", "?"), getattr(resp, "text", ""))

def _require(cond: bool, msg: str):
    if not cond:
        log.error(msg)
        sys.exit(1)

def _sanitize_callback(url: str) -> str:
    if not url:
        return ""
    if "TWITTER_CALLBACK_URL=" in url:
        url = url.split("TWITTER_CALLBACK_URL=", 1)[1].strip()
        log.warning("Sanitized TWITTER_CALLBACK_URL from malformed value.")
    p = urlparse(url)
    _require(p.scheme in ("http", "https") and p.netloc, f"Invalid TWITTER_CALLBACK_URL: {url!r}")
    return url

# ────────────────────── Mode detection ──────────────────────
def detect_mode() -> str:
    if AUTH_MODE in ("oauth1", "oauth2"):
        return AUTH_MODE
    have_oauth1 = all([O1_API_KEY, O1_API_SECRET, O1_ACCESS_TOKEN, O1_ACCESS_SECRET])
    have_oauth2 = all([O2_CLIENT_ID, O2_CALLBACK_URL_RAW])
    if have_oauth1:
        return "oauth1"
    if have_oauth2:
        return "oauth2"
    return ""

# ────────────────────── OAuth1 flow ──────────────────────
def run_oauth1_flow(message: str):
    log.info("Auth mode: OAuth 1.0a (legacy tokens)")

    # Verify creds via v1.1 for sanity
    try:
        auth = tweepy.OAuth1UserHandler(
            O1_API_KEY, O1_API_SECRET, O1_ACCESS_TOKEN, O1_ACCESS_SECRET
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)
        user = api.verify_credentials()
        _require(user is not None, "OAuth1 verify_credentials failed.")
        log.info("OAuth1 OK: @%s", user.screen_name)
    except TweepyException:
        log.exception("OAuth1 verification failed")
        sys.exit(1)

    # Post via v2 create_tweet using OAuth1 user context
    try:
        client = tweepy.Client(
            consumer_key=O1_API_KEY,
            consumer_secret=O1_API_SECRET,
            access_token=O1_ACCESS_TOKEN,
            access_token_secret=O1_ACCESS_SECRET,
            wait_on_rate_limit=True,
        )
        me = client.get_me(user_auth=True)
        _require(me and me.data, "Failed to get user context (OAuth1).")
        log.info("Authenticated as @%s (id=%s)", me.data.username, me.data.id)

        resp = client.create_tweet(text=message, user_auth=True)
        tweet_id = (resp.data or {}).get("id")
        log.info("Tweet posted! id=%s", tweet_id)
    except TweepyException as e:
        log.error("Failed to post (OAuth1 path): %s", e)
        _log_x_error(e)
        sys.exit(1)

# ────────────────────── Local callback server (OAuth2) ──────────────────────
class _CallbackHandler(BaseHTTPRequestHandler):
    _queue: "queue.Queue[str]" = None  # set by starter
    def do_GET(self):
        try:
            full_url = f"http://{self.headers.get('Host')}{self.path}"
            # Return a friendly page
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorization complete.</h2>"
                             b"<p>You can close this window and return to the app.</p></body></html>")
            # Push the full URL to the queue
            if self._queue:
                self._queue.put(full_url)
        except Exception:
            pass

def _start_local_server(host: str, port: int, q: "queue.Queue[str]") -> HTTPServer:
    _CallbackHandler._queue = q
    httpd = HTTPServer((host, port), _CallbackHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

# ────────────────────── OAuth2 flow ──────────────────────
def run_oauth2_flow(message: str):
    log.info("Auth mode: OAuth 2.0 (PKCE)")

    callback_url = _sanitize_callback(O2_CALLBACK_URL_RAW)
    use_local = False

    # If callback points to our local server, start it; otherwise we'll do normal browser + paste
    parsed = urlparse(callback_url)
    if parsed.hostname in ("127.0.0.1", "localhost") and parsed.path == LOCAL_PATH:
        use_local = True
        _require(str(parsed.port or LOCAL_PORT) == str(LOCAL_PORT),
                 f"Callback port mismatch. Expected {LOCAL_PORT}, got {parsed.port or '(none)'}")

    # Build handler
    handler = tweepy.OAuth2UserHandler(
        client_id=O2_CLIENT_ID,
        redirect_uri=callback_url,
        scope=O2_SCOPES,
        client_secret=O2_CLIENT_SECRET  # keep if your app is Confidential client
    )

    # Start local server if applicable
    httpd = None
    q: "queue.Queue[str]" = queue.Queue()
    if use_local:
        httpd = _start_local_server(LOCAL_HOST, LOCAL_PORT, q)
        log.info("Local callback server running at http://%s:%s%s", LOCAL_HOST, LOCAL_PORT, LOCAL_PATH)

    # Open consent
    auth_url = handler.get_authorization_url()
    log.info("Opening browser for consent: %s", auth_url)
    webbrowser.open(auth_url)

    # Get the redirected URL
    if use_local:
        try:
            redirect_response = q.get(timeout=180)  # 3 minutes
            log.info("Captured redirect.")
        except queue.Empty:
            log.error("Timed out waiting for redirect to local callback.")
            sys.exit(1)
    else:
        redirect_response = input("Paste the FULL redirect URL here (must contain ?code=...):\n").strip()

    # Must contain ?code=
    qs = parse_qs(urlparse(redirect_response).query)
    _require("code" in qs, "No 'code' query param found in redirect URL.")

    # Exchange code for tokens
    try:
        tokens = handler.fetch_token(authorization_response=redirect_response)
    except TweepyException as e:
        log.error("Failed to exchange code for tokens: %s", e)
        _log_x_error(e)
        sys.exit(1)

    scopes_str = tokens.get("scope")
    log.info("Token scopes granted: %s", scopes_str)
    if scopes_str and "tweet.write" not in scopes_str:
        log.warning("Token missing tweet.write; posting will fail.")

    access_token = tokens.get("access_token")
    _require(bool(access_token), "No access_token returned.")

    # Build OAuth2 user client (IMPORTANT: pass ONLY the access_token)
    client = tweepy.Client(access_token=access_token, wait_on_rate_limit=True)

    # Verify user context (OAuth2 → user_auth=False)
    try:
        me = client.get_me(user_auth=False)
        _require(me and me.data, "User context check failed (OAuth2).")
        log.info("Authenticated as @%s (id=%s)", me.data.username, me.data.id)
    except TweepyException as e:
        log.error("User context check failed (OAuth2): %s", e)
        _log_x_error(e)
        sys.exit(1)

    # Post
    try:
        resp = client.create_tweet(text=message, user_auth=False)
        tweet_id = (resp.data or {}).get("id")
        log.info("Tweet posted! id=%s", tweet_id)
    except TweepyException as e:
        log.error("Failed to post tweet (OAuth2): %s", e)
        _log_x_error(e)
        sys.exit(1)
    finally:
        if httpd:
            try:
                httpd.shutdown()
            except Exception:
                pass

# ────────────────────── Main ──────────────────────
def main():
    mode = detect_mode()
    if not mode:
        log.error(
            "No auth mode could be determined.\n"
            "- For OAuth1: set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET\n"
            "- For OAuth2: set TWITTER_CLIENT_ID, TWITTER_CALLBACK_URL (and optional TWITTER_CLIENT_SECRET)\n"
            "Optionally set AUTH_MODE=oauth1|oauth2 to force a mode."
        )
        sys.exit(1)

    if mode == "oauth1":
        run_oauth1_flow(MESSAGE)
    else:
        # If you want to use the built-in local server, set:
        #   TWITTER_CALLBACK_URL=http://127.0.0.1:8765/callback
        # and add that exact URL in X Developer Portal → User authentication settings.
        run_oauth2_flow(MESSAGE)

if __name__ == "__main__":
    main()
