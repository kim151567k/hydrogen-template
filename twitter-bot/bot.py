import argparse
import json
import os
import random
import sys
import time
from typing import Optional, Any

# Optional imports so that --help works without dependencies
try:
    import tweepy  # type: ignore
except Exception:  # pragma: no cover
    tweepy = None  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv() -> None:
        return None

try:
    import backoff  # type: ignore
except Exception:  # pragma: no cover
    class _NoBackoff:
        def on_exception(self, *args: Any, **kwargs: Any):
            def decorator(fn):
                return fn
            return decorator
    backoff = _NoBackoff()  # type: ignore


def load_config_from_env() -> dict:
    load_dotenv()
    config = {
        "api_key": os.getenv("X_API_KEY"),
        "api_secret": os.getenv("X_API_SECRET"),
        "access_token": os.getenv("X_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("X_ACCESS_TOKEN_SECRET"),
    }
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    return config


def build_client(config: dict) -> Any:
    if tweepy is None:
        print(
            "Missing dependency 'tweepy'. Install with: pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(2)
    client = tweepy.Client(
        consumer_key=config["api_key"],
        consumer_secret=config["api_secret"],
        access_token=config["access_token"],
        access_token_secret=config["access_token_secret"],
        wait_on_rate_limit=True,
    )
    return client


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="X (Twitter) like/retweet bot")
    parser.add_argument(
        "--query",
        required=True,
        help="v2 search query, e.g. '#python lang:en -is:retweet -is:reply -is:quote'",
    )
    parser.add_argument("--like", dest="like", action="store_true", default=True)
    parser.add_argument("--no-like", dest="like", action="store_false")
    parser.add_argument("--retweet", dest="retweet", action="store_true", default=False)
    parser.add_argument("--no-retweet", dest="retweet", action="store_false")
    parser.add_argument("--interval-seconds", type=int, default=600)
    parser.add_argument("--per-cycle-limit", type=int, default=10)
    parser.add_argument("--max-total", type=int, default=None)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{ts}] {msg}")


@backoff.on_exception(  # type: ignore[attr-defined]
    getattr(backoff, "expo", lambda *a, **k: (lambda f: f)),  # type: ignore[attr-defined]
    (Exception,),
    max_tries=5,
    factor=2,
)
def like_tweet(client: Any, tweet_id: int, dry_run: bool) -> None:
    if dry_run:
        log(f"DRY-RUN like {tweet_id}")
        return
    if tweepy is None:
        raise RuntimeError("tweepy not installed")
    client.like(tweet_id)


@backoff.on_exception(  # type: ignore[attr-defined]
    getattr(backoff, "expo", lambda *a, **k: (lambda f: f)),  # type: ignore[attr-defined]
    (Exception,),
    max_tries=5,
    factor=2,
)
def retweet_tweet(client: Any, tweet_id: int, dry_run: bool) -> None:
    if dry_run:
        log(f"DRY-RUN retweet {tweet_id}")
        return
    if tweepy is None:
        raise RuntimeError("tweepy not installed")
    client.retweet(tweet_id)


def run_cycle(
    client: Any,
    me_id: int,
    query: str,
    like: bool,
    retweet: bool,
    per_cycle_limit: int,
    dry_run: bool,
) -> int:
    if tweepy is None:
        raise RuntimeError("tweepy not installed")

    acted = 0
    paginator = tweepy.Paginator(
        client.search_recent_tweets,
        query=query,
        max_results=50,
        sort_order="recency",
        tweet_fields=["author_id", "lang", "created_at", "public_metrics"],
    )

    for tweet in paginator.flatten(limit=per_cycle_limit * 3):
        if acted >= per_cycle_limit:
            break
        if str(tweet.author_id) == str(me_id):
            continue
        tweet_id = int(tweet.id)
        try:
            if like:
                like_tweet(client, tweet_id, dry_run)
                log(f"liked {tweet_id}")
                acted += 1
            if retweet:
                time.sleep(random.uniform(1.0, 3.0))
                retweet_tweet(client, tweet_id, dry_run)
                log(f"retweeted {tweet_id}")
                acted += 1
        except Exception as e:
            log(f"Action error on {tweet_id}: {e}")
        time.sleep(random.uniform(2.0, 6.0))

    return acted


def main() -> None:
    args = parse_args()
    config = load_config_from_env()
    client = build_client(config)

    if tweepy is None:
        print("Missing dependency 'tweepy'.", file=sys.stderr)
        sys.exit(2)

    me = client.get_me(user_fields=["id", "username"]).data
    me_id = int(me.id)
    log(f"Authenticated as @{me.username} ({me_id})")

    total_acted = 0

    while True:
        log(f"Searching: {args.query}")
        acted = run_cycle(
            client=client,
            me_id=me_id,
            query=args.query,
            like=args.like,
            retweet=args.retweet,
            per_cycle_limit=args.per_cycle_limit,
            dry_run=args.dry_run,
        )
        total_acted += acted
        log(f"Cycle complete. Acted on {acted} items. Total so far: {total_acted}")

        if args.max_total is not None and total_acted >= args.max_total:
            log("Reached max total. Exiting.")
            break
        if args.once:
            break

        sleep_s = max(1, args.interval_seconds)
        jitter = random.uniform(0, min(60, sleep_s * 0.1))
        sleep_for = sleep_s + jitter
        log(f"Sleeping for {int(sleep_for)}s...")
        time.sleep(sleep_for)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Interrupted. Bye.")
        sys.exit(0)