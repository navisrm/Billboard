import json
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GNEWS_API_KEY", "")
LANGUAGE = os.getenv("NEWS_LANG", "en")

# One GNews search request per topic. `in=title` keeps matches on-topic.
TOPICS = [
    {
        "key": "ca_gov",
        "label": "Canada",
        "country": "ca",
        "q": '"federal government" OR "prime minister" OR "Government of Canada" OR "federal funding" OR Parliament',
    },
    {
        "key": "us_gov",
        "label": "US",
        "country": "us",
        "q": '"White House" OR "executive order" OR "Trump administration" OR "signs bill" OR "federal agency"',
    },
    {
        "key": "health",
        "label": "FDA / Vaccines",
        "country": None,
        "q": '"FDA approves" OR "FDA approval" OR "FDA clears" OR "Health Canada" OR vaccine',
    },
    {
        "key": "deals",
        "label": "Deals",
        "country": None,
        "q": '"to acquire" OR "agrees to buy" OR "agreed to buy" OR "merger agreement" OR "takeover bid" OR "billion deal"',
    },
]
PER_TOPIC = 5

# GNews free tier: 100 requests/day, max 10 articles per request, 1 request/second.
# 4 topics every 90 min = 64 requests/day, leaving headroom for manual testing.
NEWS_INTERVAL_SECONDS = 90 * 60
MAX_ARTICLES = 10
REQUEST_SPACING_SECONDS = 1.2

NEWS_URL = "https://gnews.io/api/v4/search"
# Persisted so service restarts and reboots reuse the last fetch instead of spending quota.
CACHE_FILE = Path(__file__).parent / ".news_cache.json"


def _load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache))


def _fetch_topic(topic):
    params = {
        "q": topic["q"],
        "in": "title",
        "lang": LANGUAGE,
        "max": MAX_ARTICLES,
        "sortby": "publishedAt",
        "apikey": API_KEY,
    }
    if topic["country"]:
        params["country"] = topic["country"]
    response = httpx.get(NEWS_URL, params=params, timeout=10)
    response.raise_for_status()
    return [
        {
            "title": article["title"],
            "source": article["source"]["name"],
            "published_at": article["publishedAt"],
            "topic": topic["label"],
            "topic_key": topic["key"],
        }
        for article in response.json().get("articles", [])
    ]


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "its", "of", "off", "on", "or", "s", "says", "the", "to", "with", "after", "over", "new",
}


def _words(title):
    return set(re.findall(r"[a-z0-9]+", title.lower())) - STOPWORDS


def _is_duplicate(title, seen):
    # Same story from different outlets: most of the shorter headline's key words appear in the other.
    words = _words(title)
    for other in seen:
        shared = len(words & other)
        if shared >= 3 and shared / max(1, min(len(words), len(other))) > 0.5:
            return True
    return False


def _select_articles(topics):
    seen, selected = [], []
    for topic in TOPICS:
        picked = 0
        for article in topics.get(topic["key"], []):
            if picked == PER_TOPIC:
                break
            if _is_duplicate(article["title"], seen):
                continue
            seen.append(_words(article["title"]))
            selected.append(article)
            picked += 1
    return sorted(selected, key=lambda a: a["published_at"], reverse=True)


def get_news():
    if not API_KEY:
        return {"articles": [], "fetched_at": None, "error": "GNEWS_API_KEY is not set"}

    cache = _load_cache()
    stale = "topics" not in cache or time.time() - cache.get("fetched_at", 0) >= NEWS_INTERVAL_SECONDS
    if stale:
        # Record the attempt before calling, so failing requests are retried
        # on the normal schedule rather than every loop and can't burn the daily quota.
        cache["fetched_at"] = time.time()
        cache.setdefault("topics", {})
        _save_cache(cache)
        errors = []
        for i, topic in enumerate(TOPICS):
            if i:
                time.sleep(REQUEST_SPACING_SECONDS)
            try:
                cache["topics"][topic["key"]] = _fetch_topic(topic)
            except httpx.HTTPStatusError as exc:
                # Not str(exc): it includes the request URL, which carries the API key.
                errors.append(f"{topic['label']}: GNews returned {exc.response.status_code}")
            except httpx.HTTPError as exc:
                errors.append(f"{topic['label']}: {type(exc).__name__}")
        # On failure a topic keeps its previous articles.
        cache["error"] = f"News unavailable ({'; '.join(errors)})" if errors else None
        _save_cache(cache)

    return {
        "articles": _select_articles(cache["topics"]),
        "fetched_at": cache["fetched_at"],
        "error": cache.get("error"),
    }
