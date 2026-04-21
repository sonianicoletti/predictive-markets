import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
import time
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4.1"

#OLLAMA_URL = "http://localhost:11434/api/generate"
#MODEL = "llama3.1:8b"

def ask_llm(title=None, text=None, no_article=False):
    if no_article:
        prompt = f"""
With what probability do you think this event is going to happen:

Event: Will the Iranian regime fall by June 30?

Only reply with an integer number from 0 to 100.
Do not include any explanation. Only output the number.
""".strip()
    else:
        prompt = f"""
With what probability do you think this event is going to happen after reading this article:

{title}
{text}

Event: Will the Iranian regime fall by June 30?

Only reply with an integer number from 0 to 100.
Do not include any explanation. Only output the number.
""".strip()

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(OPENAI_URL, json=payload, headers=headers)
        r.raise_for_status()
        response = r.json()["choices"][0]["message"]["content"].strip()
        
        # extract first integer found (robustness)
        num = "".join(ch for ch in response if ch.isdigit())
        return int(num) if num else None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def get_unbiased_baseline(num_calls=10):
    print(f"\n{'='*60}")
    print(f"Getting unbiased baseline probability from {num_calls} separate LLM calls...")
    print(f"(No article provided - just asking about the event directly)")
    print(f"{'='*60}")
    
    probabilities = []
    
    for i in range(num_calls):
        print(f"  Baseline call {i+1}/{num_calls}...", end="", flush=True)
        prob = ask_llm(no_article=True)
        if prob is not None:
            probabilities.append(prob)
            print(f" got: {prob}%")
        else:
            print(f" failed")
        
        if i < num_calls - 1:
            time.sleep(0.5)
    
    if probabilities:
        avg_prob = sum(probabilities) / len(probabilities)
        print(f"\n✓ Unbiased baseline average: {avg_prob:.1f}% (based on {len(probabilities)} successful calls)")
        return avg_prob
    else:
        print(f"\n✗ Failed to get any valid baseline probabilities")
        return None


def run_three_conditions(row, unbiased_baseline=None):
    # Original article
    print("  Asking about ORIGINAL article...", end="", flush=True)
    orig = ask_llm(row["Title"], row["Full Text"])
    print(f" got: {orig}%" if orig is not None else " failed")
    
    time.sleep(0.3)
    
    # Left wing version
    print("  Asking about LEFT-WING version...", end="", flush=True)
    left = ask_llm(row["Left_Wing_Title"], row["Left_Wing_Full_Text"])
    print(f" got: {left}%" if left else " failed")
    
    time.sleep(0.3)
    
    # Right wing version
    print("  Asking about RIGHT-WING version...", end="", flush=True)
    right = ask_llm(row["Right_Wing_Title"], row["Right_Wing_Full_Text"])
    print(f" got: {right}%" if right else " failed")
    
    return orig, left, right


def create_average_plot(orig_vals, left_vals, right_vals, baseline_val):
    # Calculate averages (ignoring None/NaN)
    orig_avg = np.nanmean(orig_vals)
    left_avg = np.nanmean(left_vals)
    right_avg = np.nanmean(right_vals)
    
    # Calculate standard deviations
    orig_std = np.nanstd(orig_vals)
    left_std = np.nanstd(left_vals)
    right_std = np.nanstd(right_vals)
    
    # Prepare data for plotting
    categories = ['Original Articles', 'Left-Wing Rewrites', 'Right-Wing Rewrites']
    averages = [orig_avg, left_avg, right_avg]
    std_devs = [orig_std, left_std, right_std]
    colors = ['skyblue', 'lightgreen', 'salmon']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Create bar plot with error bars
    x = np.arange(len(categories))
    bars = ax.bar(x, averages, yerr=std_devs, capsize=8, 
                  color=colors, edgecolor='black', alpha=0.8,
                  error_kw={'linewidth': 2, 'ecolor': 'darkred'})
    
    # Add baseline as horizontal line
    ax.axhline(y=baseline_val, color='red', linestyle='--', linewidth=2.5, 
               label=f'Unbiased Baseline: {baseline_val:.1f}%', alpha=0.8)
    
    # Add labels and title
    ax.set_ylabel('Average Probability (%)', fontsize=13, fontweight='bold')
    ax.set_title('Average Probability of Iranian Regime Falling by June 30\n(Across All 10 Articles)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Set x-axis ticks
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_yticks(range(0, 101, 10))
    
    # Add grid
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for i, (bar, avg, std) in enumerate(zip(bars, averages, std_devs)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{avg:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax.text(bar.get_x() + bar.get_width()/2., height - (std/2),
                f'±{std:.1f}', ha='center', va='top', fontsize=8, color='darkred', alpha=0.7)
    
    # Add legend
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
    
    # Add note about statistical significance
    dev_from_baseline_orig = orig_avg - baseline_val
    dev_from_baseline_left = left_avg - baseline_val
    dev_from_baseline_right = right_avg - baseline_val
    
    note_text = f"""Deviation from baseline:
    Original: {dev_from_baseline_orig:+.1f} percentage points
    Left-wing: {dev_from_baseline_left:+.1f} percentage points
    Right-wing: {dev_from_baseline_right:+.1f} percentage points"""
    
    ax.text(0.02, 0.98, note_text, transform=ax.transAxes, 
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            family='monospace')
    
    plt.tight_layout()
    plt.savefig("average_probabilities.png", dpi=300, bbox_inches='tight')
    print("✓ Saved average plot to 'average_probabilities.png'")
    plt.show()
    
    return fig, ax


def main():
    df = pd.read_csv("news_iran_2.csv")
    df = df.head(10).copy()
    
    # Step 1: Get unbiased baseline probability (10 calls, no article)
    unbiased_baseline = get_unbiased_baseline(num_calls=10)
    
    # Add baseline column to dataframe (same value for all rows)
    df["Unbiased_Baseline_Prob"] = unbiased_baseline if unbiased_baseline is not None else np.nan
    
    # Step 2: Process each article
    print(f"\n{'='*60}")
    print(f"Processing {len(df)} articles...")
    print(f"{'='*60}")
    
    for i, row in df.iterrows():
        print(f"\nArticle {i+1}/{len(df)}: {row['Title'][:60]}...")
        
        orig, left, right = run_three_conditions(row, unbiased_baseline)
        
        df.loc[i, "Prob_Original"] = orig
        df.loc[i, "Prob_Left"] = left
        df.loc[i, "Prob_Right"] = right
        
        # Small delay between articles
        if i < len(df) - 1:
            time.sleep(0.5)
    
    # Save updated CSV
    df.to_csv("iran_news_2_with_probs_and_baseline.csv", index=False)
    print(f"\n✓ Saved to 'iran_news_2_with_probs_and_baseline.csv'")
    
    # ---- plotting ----
    print(f"\n{'='*60}")
    print("Generating plots...")
    print(f"{'='*60}")
    
    # Prepare data for plotting
    labels = [f"Article {i+1}" for i in range(len(df))]
    orig_vals = df["Prob_Original"].tolist()
    left_vals = df["Prob_Left"].tolist()
    right_vals = df["Prob_Right"].tolist()
    baseline_val = unbiased_baseline if unbiased_baseline is not None else 0
    
    # Create three subplots: individual, deviations, and averages
    fig = plt.figure(figsize=(18, 6))
    
    # Subplot 1: Individual article probabilities with baseline
    ax1 = plt.subplot(1, 3, 1)
    x = range(len(df))
    width = 0.2
    
    bars1 = ax1.bar([i - 1.5*width for i in x], orig_vals, width=width, 
                    label="Original Article", color='skyblue', edgecolor='black')
    bars2 = ax1.bar([i - 0.5*width for i in x], left_vals, width=width, 
                    label="Left-Wing Rewrite", color='lightgreen', edgecolor='black')
    bars3 = ax1.bar([i + 0.5*width for i in x], right_vals, width=width, 
                    label="Right-Wing Rewrite", color='salmon', edgecolor='black')
    
    ax1.axhline(y=baseline_val, color='red', linestyle='--', linewidth=2, 
                label=f'Baseline: {baseline_val:.1f}%', alpha=0.8)
    
    ax1.set_xlabel("Article", fontsize=11, fontweight='bold')
    ax1.set_ylabel("Probability (%)", fontsize=11, fontweight='bold')
    ax1.set_title("Individual Article Probabilities", fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax1.set_ylim(0, 105)
    ax1.set_yticks(range(0, 101, 10))
    ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax1.legend(loc='upper right', fontsize=8)
    
    # Subplot 2: Deviation from baseline
    ax2 = plt.subplot(1, 3, 2)
    orig_dev = [val - baseline_val if val is not None else np.nan for val in orig_vals]
    left_dev = [val - baseline_val if val is not None else np.nan for val in left_vals]
    right_dev = [val - baseline_val if val is not None else np.nan for val in right_vals]
    
    bars1_dev = ax2.bar([i - width for i in x], orig_dev, width=width, 
                        label="Original", color='skyblue', edgecolor='black')
    bars2_dev = ax2.bar(x, left_dev, width=width, 
                        label="Left-Wing", color='lightgreen', edgecolor='black')
    bars3_dev = ax2.bar([i + width for i in x], right_dev, width=width, 
                        label="Right-Wing", color='salmon', edgecolor='black')
    
    ax2.axhline(y=0, color='red', linestyle='-', linewidth=1.5, alpha=0.5)
    ax2.set_xlabel("Article", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Deviation from Baseline (pp)", fontsize=11, fontweight='bold')
    ax2.set_title("Deviation from Baseline", fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax2.legend(loc='upper right', fontsize=8)
    
    # Subplot 3: Average probabilities across all articles
    ax3 = plt.subplot(1, 3, 3)
    categories = ['Original', 'Left-Wing', 'Right-Wing']
    averages = [np.nanmean(orig_vals), np.nanmean(left_vals), np.nanmean(right_vals)]
    std_devs = [np.nanstd(orig_vals), np.nanstd(left_vals), np.nanstd(right_vals)]
    colors = ['skyblue', 'lightgreen', 'salmon']
    
    x_cat = np.arange(len(categories))
    bars_avg = ax3.bar(x_cat, averages, yerr=std_devs, capsize=8, 
                       color=colors, edgecolor='black', alpha=0.8,
                       error_kw={'linewidth': 2, 'ecolor': 'darkred'})
    
    ax3.axhline(y=baseline_val, color='red', linestyle='--', linewidth=2.5, 
                label=f'Baseline: {baseline_val:.1f}%', alpha=0.8)
    
    ax3.set_ylabel('Average Probability (%)', fontsize=11, fontweight='bold')
    ax3.set_title('Averages Across All 10 Articles', fontsize=12, fontweight='bold')
    ax3.set_xticks(x_cat)
    ax3.set_xticklabels(categories, fontsize=10, fontweight='bold')
    ax3.set_ylim(0, 105)
    ax3.set_yticks(range(0, 101, 10))
    ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax3.legend(loc='upper right', fontsize=9)
    
    # Add value labels on average bars
    for i, (bar, avg, std) in enumerate(zip(bars_avg, averages, std_devs)):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{avg:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax3.text(bar.get_x() + bar.get_width()/2., height - (std/2),
                f'±{std:.1f}', ha='center', va='top', fontsize=8, color='darkred')
    
    plt.suptitle("Probability of Iranian Regime Falling by June 30\nAnalysis of 10 News Articles and Their Political Rewrites", 
                 fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig("iran_predictions_complete.png", dpi=300, bbox_inches='tight')
    print("✓ Saved complete plot to 'iran_predictions_complete.png'")
    plt.show()
    
    # Also create a standalone average plot
    create_average_plot(orig_vals, left_vals, right_vals, baseline_val)
    
    # Print summary statistics
    print(f"\n{'='*60}")
    print("SUMMARY STATISTICS")
    print(f"{'='*60}")
    print(f"Unbiased Baseline (10 calls, no article): {baseline_val:.1f}%")
    print(f"\nAverages across 10 articles:")
    print(f"  Original articles:  {np.nanmean(orig_vals):.1f}% (±{np.nanstd(orig_vals):.1f})")
    print(f"  Left-wing rewrites: {np.nanmean(left_vals):.1f}% (±{np.nanstd(left_vals):.1f})")
    print(f"  Right-wing rewrites:{np.nanmean(right_vals):.1f}% (±{np.nanstd(right_vals):.1f})")
    print(f"\nBias relative to baseline:")
    print(f"  Original:  {np.nanmean(orig_dev):+.1f} percentage points")
    print(f"  Left-wing: {np.nanmean(left_dev):+.1f} percentage points")
    print(f"  Right-wing:{np.nanmean(right_dev):+.1f} percentage points")
    
    # Statistical test info
    print(f"\nEffect of political framing:")
    if np.nanmean(left_vals) > np.nanmean(orig_vals):
        print(f"  Left-wing framing INCREASES perceived probability by {np.nanmean(left_vals) - np.nanmean(orig_vals):+.1f}pp")
    else:
        print(f"  Left-wing framing DECREASES perceived probability by {np.nanmean(left_vals) - np.nanmean(orig_vals):+.1f}pp")
    
    if np.nanmean(right_vals) > np.nanmean(orig_vals):
        print(f"  Right-wing framing INCREASES perceived probability by {np.nanmean(right_vals) - np.nanmean(orig_vals):+.1f}pp")
    else:
        print(f"  Right-wing framing DECREASES perceived probability by {np.nanmean(right_vals) - np.nanmean(orig_vals):+.1f}pp")


if __name__ == "__main__":
    main()