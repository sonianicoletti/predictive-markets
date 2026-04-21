import csv
import requests
import json

# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def ask_llm(prompt):
    """Send prompt to Ollama and return response text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        return response.json()["response"].strip()
    else:
        print(f"Error: {response.status_code}")
        return ""

def rewrite_article(title, full_text, political_side):
    """
    Ask LLM to rewrite article with same facts but different political tone.
    political_side: "left-wing" or "right-wing"
    Returns: (new_title, new_full_text)
    """
    prompt = f"""You are a political rewriting assistant.

Original article title: {title}
Original article text: {full_text}

Rewrite the article from a **{political_side}** perspective.
Keep all the same facts, but change the tone, word choice, and phrasing to reflect a {political_side} political viewpoint.
Do not invent new facts or remove key facts.

You MUST return your response in the following EXACT format:

NEW TITLE: [insert your rewritten title here]

NEW FULL TEXT: [insert your rewritten full text here]

Do not add any other commentary outside this format."""

    response = ask_llm(prompt)
    
    # Parse the response to extract title and full text
    new_title = ""
    new_full_text = ""
    
    if "NEW TITLE:" in response and "NEW FULL TEXT:" in response:
        # Extract title
        title_part = response.split("NEW TITLE:")[1].split("NEW FULL TEXT:")[0].strip()
        new_title = title_part
        
        # Extract full text
        text_part = response.split("NEW FULL TEXT:")[1].strip()
        new_full_text = text_part
    else:
        # Fallback if LLM doesn't follow format exactly
        print(f"  Warning: LLM didn't follow expected format for {political_side}")
        new_title = f"[{political_side}] {title}"
        new_full_text = response[:500]  # Truncate if needed
    
    return new_title, new_full_text

def main():
    input_file = "news_iran.csv"
    output_file = "news_iran_2.csv"
    
    # Read original CSV
    with open(input_file, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + [
            "Left_Wing_Title", "Left_Wing_Full_Text",
            "Right_Wing_Title", "Right_Wing_Full_Text"
        ]
        all_rows = list(reader)
    
    # Take only first 10 articles
    rows_to_process = all_rows[:10]
    print(f"Processing first {len(rows_to_process)} articles out of {len(all_rows)} total")
    
    # Process each article
    for idx, row in enumerate(rows_to_process):
        title = row["Title"]
        full_text = row["Full Text"]
        print(f"\nProcessing article {idx+1}/{len(rows_to_process)}: {title[:60]}...")
        
        print("  Generating left-wing version...")
        left_title, left_text = rewrite_article(title, full_text, "left-wing")
        
        print("  Generating right-wing version...")
        right_title, right_text = rewrite_article(title, full_text, "right-wing")
        
        # Add the new fields to the row
        row["Left_Wing_Title"] = left_title
        row["Left_Wing_Full_Text"] = left_text
        row["Right_Wing_Title"] = right_title
        row["Right_Wing_Full_Text"] = right_text
    
    # Write output CSV with all original rows (including unprocessed ones)
    # For unprocessed rows (11+), the new fields will be empty
    for row in all_rows[10:]:
        row["Left_Wing_Title"] = ""
        row["Left_Wing_Full_Text"] = ""
        row["Right_Wing_Title"] = ""
        row["Right_Wing_Full_Text"] = ""
    
    with open(output_file, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nDone! Saved to {output_file}")
    print(f"  - Processed {len(rows_to_process)} articles")
    print(f"  - Left unmodified {len(all_rows) - len(rows_to_process)} articles")

if __name__ == "__main__":
    main()