import json
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FREENEWS_API_KEY", "")
LANGUAGE = os.getenv("NEWS_LANG", "en")

# Each category is shown on its own screen(s). Every query is one API request;
# a category's queries are merged (e.g. Canada + US) and the newest stories kept.
CATEGORIES = [
    # Without a topic the API returns everything newest-first, which is mostly sports; "world" reads like headlines.
    {"key": "top", "label": "Top Stories", "queries": [
        {"topic": "world", "country": "ca"},
        {"topic": "world", "country": "us"},
    ]},
    {"key": "politics", "label": "Politics", "queries": [
        {"topic": "politics", "country": "ca"},
        {"topic": "politics", "country": "us"},
    ]},
    {"key": "business", "label": "Business", "queries": [
        {"topic": "business", "country": "ca"},
        {"topic": "business", "country": "us"},
    ]},
    {"key": "health", "label": "Health", "queries": [
        {"topic": "health", "country": "ca"},
        {"topic": "health", "country": "us"},
    ]},
    {"key": "technology", "label": "Technology", "queries": [{"topic": "technology", "country": "us"}]},
]
PER_CATEGORY = 6

# freenewsapi.io free tier: 5,000 requests/day, 2 requests/second.
# 9 requests every 15 min = 864/day.
NEWS_INTERVAL_SECONDS = 15 * 60
REQUEST_SPACING_SECONDS = 0.6

NEWS_URL = "https://api.freenewsapi.io/v1/news"
# Persisted so service restarts and reboots reuse the last fetch instead of spending quota.
CACHE_FILE = Path(__file__).parent / ".news_cache.json"


def _load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache))


def _fetch(query):
    response = httpx.get(
        NEWS_URL,
        params={"language": LANGUAGE, **query},
        headers={"x-api-key": API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    return [
        {
            "title": _clean_title(article["title"], article.get("publisher") or ""),
            "source": article.get("publisher") or "",
            "published_at": article["published_at"],
        }
        for article in response.json().get("data", [])
        if article.get("title")
    ]


def _clean_title(title, publisher):
    # Some feeds append the outlet ("Headline - Sports Illustrated"); the source is already shown below.
    if publisher and " - " in title:
        head, _, tail = title.partition(" - ")
        if publisher.lower() in tail.lower() or tail.lower() in publisher.lower():
            return head
    return title


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


def _select(results):
    # Categories are filled in order, so a story already under Top Stories isn't repeated later.
    seen, categories = [], []
    for category in CATEGORIES:
        pool = [
            article
            for i in range(len(category["queries"]))
            for article in results.get(f"{category['key']}:{i}", [])
        ]
        picked = []
        for article in sorted(pool, key=lambda a: a["published_at"], reverse=True):
            if len(picked) == PER_CATEGORY:
                break
            if _is_duplicate(article["title"], seen):
                continue
            seen.append(_words(article["title"]))
            picked.append(article)
        if picked:
            categories.append({"key": category["key"], "label": category["label"], "articles": picked})
    return categories


def get_news():
    if not API_KEY:
        return {"categories": [], "fetched_at": None, "error": "FREENEWS_API_KEY is not set"}

    cache = _load_cache()
    stale = "results" not in cache or time.time() - cache.get("fetched_at", 0) >= NEWS_INTERVAL_SECONDS
    if stale:
        # Record the attempt before calling, so failing requests are retried
        # on the normal schedule rather than every loop.
        cache["fetched_at"] = time.time()
        cache.setdefault("results", {})
        _save_cache(cache)
        errors = []
        first = True
        for category in CATEGORIES:
            for i, query in enumerate(category["queries"]):
                if not first:
                    time.sleep(REQUEST_SPACING_SECONDS)
                first = False
                try:
                    cache["results"][f"{category['key']}:{i}"] = _fetch(query)
                except httpx.HTTPStatusError as exc:
                    errors.append(f"{category['label']}: HTTP {exc.response.status_code}")
                except httpx.HTTPError as exc:
                    errors.append(f"{category['label']}: {type(exc).__name__}")
        # On failure a query keeps its previous articles.
        cache["error"] = f"Some news unavailable ({'; '.join(errors)})" if errors else None
        _save_cache(cache)

    return {
        "categories": _select(cache["results"]),
        "fetched_at": cache["fetched_at"],
        "error": cache.get("error"),
    }
