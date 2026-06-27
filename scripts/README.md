### Historical Backfill (one-time)

```bash
# Fetch 6 years of weekly chunks (~313 API calls)
python scripts/step1_fetch_historical.py --years 6

# Flatten all JSON chunks into one CSV
python scripts/step2_build_dataset.py
```
