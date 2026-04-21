#!/usr/bin/env python3
import random
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
import matplotlib.pyplot as plt

ph_file = pq.ParquetFile("data/prices_history.parquet")

num_row_groups = ph_file.num_row_groups
rg = random.randint(0, num_row_groups - 1)

batch = ph_file.read_row_group(rg).to_pandas()
row = batch.sample(1).iloc[0]

clob_id = row["market_clob"]
print(f"Clob ID: {clob_id}")

filtered_tables = []

for batch in ph_file.iter_batches(batch_size=20000):
    table = pa.Table.from_batches([batch])
    mask = pc.equal(table["market_clob"], clob_id)
    filtered = table.filter(mask)

    if filtered.num_rows > 0:
        filtered_tables.append(filtered)

if not filtered_tables:
    raise ValueError("No price history found")

ph_df = pa.concat_tables(filtered_tables).to_pandas()

markets_file = pq.ParquetFile("data/markets.parquet")
market_row = None

for batch in markets_file.iter_batches(batch_size=50000):
    df = batch.to_pandas()
    match = df[df["clobTokenIds"].str.contains(clob_id, na=False)]
    if len(match) > 0:
        market_row = match.iloc[0]
        break

if market_row is None:
    raise ValueError(f"No market found for clob ID: {clob_id}")

print(f"Market: {market_row['question']}")

events = market_row["events"]
event_title = events[0].get("title", "Unknown event") if events else "Unknown event"

print(f"Event: {event_title}")

ts = []
prices = []

for hist in ph_df["history"]:
    if hist is None or len(hist) == 0:
        continue

    n = min(10, len(hist))
    idxs = [int(i * (len(hist) - 1) / (n - 1)) if n > 1 else 0 for i in range(n)]

    for i in idxs:
        ts.append(hist[i]["t"])
        prices.append(hist[i]["p"])

df_plot = pd.DataFrame({"t": ts, "p": prices})
df_plot["datetime"] = pd.to_datetime(df_plot["t"], unit="s")
df_plot = df_plot.sort_values("datetime")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_plot["datetime"], df_plot["p"])
ax.set_title(f"{event_title}\n{market_row['question']}", fontsize=11)
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("price_history.png", dpi=150)

print("Saved → price_history.png")