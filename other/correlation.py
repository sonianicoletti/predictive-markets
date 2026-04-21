import csv
from datetime import datetime

INPUT_FILE = "news_iran_with_stance.csv"

def parse_time(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except:
        return None

JUMPS = [
    {
        "name": "Dec 29 → Dec 30",
        "start": "2025-12-29T01:00:00+00:00",
        "end": "2025-12-30T13:00:00+00:00",
        "direction": "up"
    },
    {
        "name": "Jan 8 → Jan 11",
        "start": "2026-01-08T01:00:00+00:00",
        "end": "2026-01-11T01:00:00+00:00",
        "direction": "up"
    },
    {
        "name": "Feb 17 → Feb 19",
        "start": "2026-02-17T01:00:00+00:00",
        "end": "2026-02-19T01:00:00+00:00",
        "direction": "up"
    },
    {
        "name": "Feb 27 → Mar 1",
        "start": "2026-02-27T01:00:00+00:00",
        "end": "2026-03-01T01:00:00+00:00",
        "direction": "up"
    },
    {
        "name": "Mar 9 → Mar 10 (DROP)",
        "start": "2026-03-09T01:00:00+00:00",
        "end": "2026-03-10T13:00:00+00:00",
        "direction": "down"
    }
]


def load_articles():
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    articles = []

    for row in rows:
        ts = parse_time(row.get("Exact Publish Time", ""))

        if ts is None:
            continue

        try:
            confidence = int(row.get("stance_confidence", 0))
        except:
            confidence = 0

        articles.append({
            "title": row.get("Title"),
            "time": ts,
            "stance": row.get("stance", "").lower(),
            "confidence": confidence,
            "source": row.get("Source"),
        })

    return articles


def analyze():
    articles = load_articles()

    for jump in JUMPS:
        start = parse_time(jump["start"])
        end = parse_time(jump["end"])
        direction = jump["direction"]

        print("\n" + "=" * 60)
        print(f"JUMP: {jump['name']}")
        print(f"Time window: {start} → {end}")
        print(f"Direction: {direction.upper()}")

        # Filter articles in timeframe
        in_window = [
            a for a in articles
            if start <= a["time"] <= end
        ]

        print(f"\nTotal articles in timeframe: {len(in_window)}")

        # Apply confidence filter
        strong_articles = [a for a in in_window if a["confidence"] >= 50]

        if not strong_articles:
            print("No articles with confidence >= 50 in this timeframe.")
            continue

        # Determine expected stance
        expected_stance = "yes" if direction == "up" else "no"

        print(f"\nArticles with confidence >= 50: {len(strong_articles)}")
        print(f"Expected stance: {expected_stance.upper()}")

        matches = []

        for a in strong_articles:
            is_match = (a["stance"] == expected_stance)

            if is_match:
                matches.append(a)

            print("\n---")
            print("Title:", a["title"])
            print("Source:", a["source"])
            print("Time:", a["time"])
            print("Stance:", a["stance"])
            print("Confidence:", a["confidence"])
            print("Matches jump direction:", is_match)

        print("\nSummary:")
        print(f"Matching articles: {len(matches)} / {len(strong_articles)}")


if __name__ == "__main__":
    analyze()