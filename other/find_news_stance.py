import csv
import time
import os
from dotenv import load_dotenv
from groq import Groq

INPUT_FILE = "news_iran.csv"
OUTPUT_FILE = "news_results_with_stance.csv"

QUERY = "Will the Iranian regime fall by June 30?"

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"

def classify_article(title, text):
    prompt = f"""
You are analyzing a news article.

Question: "{QUERY}"

Article title: {title}

Article text:
{text[:4000]}

Task:
1. Does this article support the claim that the answer to the question is YES?
2. Answer strictly with:
   stance: yes OR no
   confidence: number from 0 to 100

Rules:
- "yes" = article suggests the regime WILL fall
- "no" = article suggests it will NOT fall OR is neutral/unclear

Return format (STRICT):
stance: <yes/no>
confidence: <0-100>
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        stance = "no"
        confidence = 0

        for line in content.split("\n"):
            if "stance:" in line.lower():
                stance = line.split(":")[1].strip().lower()
            if "confidence:" in line.lower():
                try:
                    confidence = int(line.split(":")[1].strip())
                except:
                    confidence = 0

        return stance, confidence

    except Exception as e:
        print("Error:", e)
        return "no", 0


def process_csv():
    with open(INPUT_FILE, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    updated_rows = []

    for i, row in enumerate(rows, 1):
        print(f"Processing article {i}/{len(rows)}")

        title = row.get("Title", "")
        text = row.get("Full Text", "")

        if not text:
            stance, confidence = "no", 0
        else:
            stance, confidence = classify_article(title, text)
            time.sleep(0.5)  # Groq is fast; small delay is enough

        row["stance"] = stance
        row["stance_confidence"] = confidence

        updated_rows.append(row)

    fieldnames = list(updated_rows[0].keys())

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"\nSaved updated file to {OUTPUT_FILE}")


if __name__ == "__main__":
    process_csv()