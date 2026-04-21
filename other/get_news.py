import requests
from newspaper import Article
from datetime import datetime
import os
from dotenv import load_dotenv
import csv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

QUERY = "Will the Iranian regime fall by June 30?"
OUTPUT_FILE = "news_iran.csv"

NUMBER_OF_ARTICLES = 100


def fetch_news():
    url = "https://serpapi.com/search"
    all_results = []
    
    for start in range(0, NUMBER_OF_ARTICLES, 10):
        params = {
            "engine": "google",
            "tbm": "nws",
            "q": QUERY,
            "api_key": SERPAPI_API_KEY,
            "num": 10,  # Max per page for news
            "start": start  # Pagination offset
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        page_results = data.get("news_results", [])
        if not page_results:  # No more results
            break
            
        all_results.extend(page_results)
        
        # Optional: Add delay to respect rate limits
        # time.sleep(1)
    
    return all_results[:NUMBER_OF_ARTICLES]


def extract_full_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        return article.text, article.publish_date
    except Exception:
        return None, None


def save_to_csv(results):
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Header
        writer.writerow([
            "Title",
            "Source",
            "Google Timestamp",
            "Exact Publish Time",
            "URL",
            "Full Text"
        ])

        # Rows
        for r in results:
            writer.writerow([
                r["title"],
                r["source"],
                r["google_timestamp"],
                r["exact_publish_time"],
                r["url"],
                r["full_text"]
            ])


def main():
    articles = fetch_news()
    results = []

    for item in articles:
        link = item.get("link")

        full_text, publish_date = extract_full_article(link)

        result = {
            "title": item.get("title"),
            "source": item.get("source"),
            "google_timestamp": item.get("date"),
            "url": link,
            "full_text": full_text,
            "exact_publish_time": (
                publish_date.isoformat() if publish_date else None
            )
        }

        results.append(result)

    save_to_csv(results)
    print(f"Saved {len(results)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()