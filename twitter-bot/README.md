# X (Twitter) Like & Retweet Bot

Automates liking and retweeting recent posts that match a search query using the official X (Twitter) API.

Important: You need a developer account with user-context access and proper API keys/tokens. Ensure your usage complies with X's Automation Rules and Developer Policy.

## Features
- Searches recent posts using a configurable query (v2 search)
- Likes and/or retweets matching posts
- Skips your own posts
- Safe defaults (excludes retweets/replies/quotes by default)
- Rate-limit aware
- Dry-run mode

## Prerequisites
- Python 3.9+
- An X developer account and an app with user-context access
- OAuth 1.0a user tokens (API key/secret + Access token/secret)

## Setup

1) Create a virtual environment (optional but recommended):

```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```
pip install -r requirements.txt
```

3) Create a `.env` file based on `.env.example` and fill in your credentials:

```
cp .env.example .env
# edit .env with your keys/tokens
```

Environment variables required:
- `X_API_KEY` — Consumer API Key
- `X_API_SECRET` — Consumer API Secret
- `X_ACCESS_TOKEN` — Access Token (user)
- `X_ACCESS_TOKEN_SECRET` — Access Token Secret (user)

## Usage

Basic example (run once):

```
python bot.py --query "#python lang:en -is:retweet -is:reply -is:quote" --like --retweet --once
```

Run continuously every 10 minutes, acting on up to 10 tweets per cycle:

```
python bot.py --query "from:someuser -is:retweet -is:reply" --like --retweet --interval-seconds 600 --per-cycle-limit 10
```

Dry-run (log actions without performing them):

```
python bot.py --query "#datascience lang:en -is:retweet -is:reply -is:quote" --like --retweet --dry-run --once
```

CLI flags:
- `--query` Required. X API v2 search query
- `--like / --no-like` Enable or disable liking (default on)
- `--retweet / --no-retweet` Enable or disable retweeting (default off)
- `--interval-seconds` Delay between cycles when not using `--once` (default 600)
- `--per-cycle-limit` Max actions per cycle (default 10)
- `--max-total` Optional global max actions then exit
- `--once` Run a single cycle and exit
- `--dry-run` Log only, do not call the API

## Notes
- Access to like/retweet endpoints may require Elevated or paid access on X. If your app lacks permission, the API will return 403 errors.
- Respect rate limits and platform rules. Avoid spammy behavior.
- You are responsible for compliance with all applicable policies.