#!/usr/bin/env python3
"""
Fetch NYT articles about "Iran" between Dec 18 2025 and Apr 10 2026.
Retrieves title, date published, lead paragraph, and full article text (scraped).

Requirements:
    pip install requests python-dotenv newspaper3k lxml_html_clean

Usage:
    python fetch_nyt_iran.py
"""

import json
import os
import time

import requests
from dotenv import load_dotenv
from newspaper import Article

API_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
QUERY = "Iran"
BEGIN_DATE = "20251218"
END_DATE = "20260410"
OUTPUT_FILE = "nyt_iran_articles.json"
API_DELAY = 0.5      # between paginated API calls
SCRAPE_DELAY = 1.0   # between article scrapes

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_full_text(url: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        response.raise_for_status()
        article = Article(url)
        article.set_html(response.text)
        article.parse()
        return article.text.strip()
    except Exception as exc:
        print(f"  [WARNING] Could not scrape {url}: {exc}")
        return ""


def fetch_articles(api_key: str) -> list[dict]:
    articles = []
    page = 0

    while True:
        params = {
            "q":          QUERY,
            "begin_date": BEGIN_DATE,
            "end_date":   END_DATE,
            "page":       page,
            "api-key":    api_key,
        }

        print(f"Fetching page {page}...")

        try:
            response = requests.get(API_URL, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[ERROR] {exc}")
            break

        data = response.json()
        resp = data.get("response", {})
        docs = resp.get("docs", [])
        meta = resp.get("meta", {})
        hits = meta.get("hits", 0)

        if page == 0:
            print(f"Raw meta: {meta}")  # print so you can see the actual structure
            print(f"Total matches: {hits}\n")

        if not docs:
            print("No more docs returned.")
            break

        for doc in docs:
            articles.append({
                "title":     doc.get("headline", {}).get("main", "").strip(),
                "published": doc.get("pub_date", "").strip(),
                "url":       doc.get("web_url", "").strip(),
                "lead":      doc.get("lead_paragraph") or doc.get("abstract") or "",
                "text":      "",
            })

        print(f"  Got {len(docs)} docs on page {page} (total so far: {len(articles)})")
        page += 1

        # NYT caps at 100 pages (1000 results)
        if page >= 100:
            break
        if hits and len(articles) >= hits:
            break

        time.sleep(API_DELAY)

    return articles


def main() -> None:
    load_dotenv()
    api_key = os.getenv("NYT_API_KEY")
    if not api_key:
        raise ValueError("NYT_API_KEY not found in .env file")

    articles = fetch_articles(api_key)
    print(f"\nFetched {len(articles)} articles from API.")
    print("Scraping full text from article URLs...\n")

    for i, article in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] {article['title'][:80]}")
        article["text"] = scrape_full_text(article["url"])
        words = len(article["text"].split())
        print(f"  → {words} words")
        time.sleep(SCRAPE_DELAY)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(articles, fh, ensure_ascii=False, indent=2)

    print(f"\nSaved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()