import pyarrow.parquet as pq
import pyarrow as pa

files = ["events", "markets", "prices_history"]

for name in files:
    f = pq.ParquetFile(f"data/polymarket/{name}.parquet")
    schema = f.schema_arrow

    print("=" * 60)
    print(f"FILE: {name}.parquet")
    print(f"Entries: {f.metadata.num_rows}")
    print("Fields:")
    for field in schema:
        print(f"  {field.name}: {field.type}")
    print()

    if name == "events":
        counts = {}

        for batch in f.iter_batches(batch_size=100000):
            df = batch.to_pandas()

            if "category" not in df.columns:
                continue

            vc = df["category"].value_counts(dropna=True)

            for k, v in vc.items():
                counts[k] = counts.get(k, 0) + int(v)

        print("*** Event categories ***")
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {k}: {v}")

        print()