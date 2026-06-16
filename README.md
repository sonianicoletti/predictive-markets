# Predictive markets
 
This repository contains exploratory experiments for a research project conducted during my RIL at the Social Systems group (MPI-SWS). It investigates how news articles influence beliefs in prediction markets, using large language models as a measurement tool.

The core idea is to use LLMs not as forecasters, but as instruments: by comparing a model's probability estimate for a market event before and after reading an article, we can quantify how much and in what direction a piece of news shifts beliefs. This *belief-update signal* is the foundation for characterising news sources along dimensions like informativeness, credibility, and timeliness.
 
Markets and crowd predictions are sourced from [Polymarket](https://polymarket.com).
 
---
 
## Experiments
 
### 1. Stance and beliefs (`prob_markets.ipynb`)
Tests whether articles with different stances shift LLM probability estimates in the expected direction. Uses 5 Polymarket questions and hand-picked articles from the New York Times, BBC, and Fox News. Also evaluates whether the LLM can correctly classify article stances against human-labelled ground truth.
 
### 2. News APIs comparison (`news_apis_comparison.ipynb`)
Compares five news retrieval APIs (GNews API, NewsAPI.org, NewsCatcher (CatchAll), NewsData.io, and the GNews Python package) across 10 Polymarket questions, all on free tiers. Evaluates article volume, source quality, and full-text availability. Includes source overlap analysis via Venn diagrams.
 
### 3. Political markets (`political_markets_retrieval.ipynb`, `political_markets_relevance.ipynb`, `political_markets_trends.ipynb`)
An end-to-end pipeline test on 3 political markets. Covers LLM-generated search query generation, article retrieval via the GNews package, relevance scoring (with and without publication date), and temporal trend analysis of article volume and relevance over time.
 
---
 
## Setup
 
```bash
pip install -r requirements.txt
```
 
Key dependencies: `gnews`, `googlenewsdecoder`, `groq`, `newspaper3k`, `readability-lxml`, `pandas`, `matplotlib`, `python-dotenv`.
 
API keys are loaded from a `.env` file. You will need at least one Groq API key to run the LLM calls:
 
```
GROQ_API_KEY_1=your_key_here
```
 
If running the News APIs comparison, you will also need keys for the other services (`GNEWS_API_KEY`, `NEWSAPI_ORG_KEY`, `NEWSCATCHER_API_KEY`, `NEWSDATA_API_KEY`), all of which have free tiers.
 
---
 
## Notes
 
- Article full text is not provided by GNews directly. URLs are decoded using `googlenewsdecoder` and full text is scraped via `newspaper3k` with readability and BeautifulSoup fallbacks.
- LLM calls use Llama 3.3 70B via the Groq API. The code supports multiple API keys with automatic rotation on rate limit errors.
- Parquet data files (from Polymarket) are not included in this repository due to size.
 
