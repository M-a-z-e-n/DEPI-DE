"""
CosmicTracker - Build Combined Dataset
=======================================
Reads every JSON chunk fetched by step1_fetch_historical.py, flattens
NASA's nested NeoWs response structure into one row per asteroid
close-approach, and saves the result as a single CSV file.

Usage:
    python scripts/step2_build_dataset.py
    python scripts/step2_build_dataset.py --output data/processed/my_dataset.csv
"""

import json
import logging
import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "build_dataset.log"
DEFAULT_OUTPUT = PROCESSED_DIR / "neo_dataset.csv"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def find_json_files():
    """Find all chunk files saved by step1, in chronological folder order."""
    return sorted(RAW_DIR.rglob("*.json"))


def flatten_asteroid(date_str, neo):
    """Flatten one NEO object for one close-approach date into a flat dict."""
    try:
        diameter = neo.get("estimated_diameter", {}).get("kilometers", {})
        approach_list = neo.get("close_approach_data", [])
        approach = approach_list[0] if approach_list else {}

        relative_velocity = approach.get("relative_velocity", {})
        miss_distance = approach.get("miss_distance", {})

        return {
            "date": date_str,
            "neo_id": neo.get("id"),
            "neo_reference_id": neo.get("neo_reference_id"),
            "name": neo.get("name"),
            "absolute_magnitude_h": neo.get("absolute_magnitude_h"),
            "estimated_diameter_min_km": diameter.get("estimated_diameter_min"),
            "estimated_diameter_max_km": diameter.get("estimated_diameter_max"),
            "is_potentially_hazardous": neo.get("is_potentially_hazardous_asteroid"),
            "is_sentry_object": neo.get("is_sentry_object"),
            "close_approach_date": approach.get("close_approach_date"),
            "close_approach_date_full": approach.get("close_approach_date_full"),
            "relative_velocity_kph": relative_velocity.get("kilometers_per_hour"),
            "relative_velocity_kps": relative_velocity.get("kilometers_per_second"),
            "miss_distance_km": miss_distance.get("kilometers"),
            "miss_distance_lunar": miss_distance.get("lunar"),
            "miss_distance_au": miss_distance.get("astronomical"),
            "orbiting_body": approach.get("orbiting_body"),
            "nasa_jpl_url": neo.get("nasa_jpl_url"),
        }
    except Exception as e:
        logger.warning(f"Failed to flatten NEO {neo.get('id', '?')} on {date_str}: {e}")
        return None


def process_file(path):
    """Read one JSON chunk file and return a list of flattened rows."""
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Skipping unreadable file {path.name}: {e}")
        return rows

    neo_by_date = data.get("near_earth_objects", {})
    for date_str, neo_list in neo_by_date.items():
        for neo in neo_list:
            row = flatten_asteroid(date_str, neo)
            if row:
                rows.append(row)
    return rows


def print_banner():
    print(f"\n{'=' * 72}")
    print("            CosmicTracker - Build Combined Dataset")
    print(f"{'=' * 72}\n")


# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Combine raw NEO JSON chunks into one CSV dataset")
    parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()
    output_path = Path(args.output)

    print_banner()

    files = find_json_files()
    logger.info(f"Found {len(files)} JSON files under {RAW_DIR}")

    if not files:
        logger.error("No JSON files found. Run step1_fetch_historical.py first.")
        return

    all_rows = []
    empty_files = 0

    progress = tqdm(files, desc="Reading", unit="file", bar_format="{l_bar}{bar:30}{r_bar}")
    for path in progress:
        rows = process_file(path)
        if not rows:
            empty_files += 1
        all_rows.extend(rows)

    logger.info(f"Total rows collected: {len(all_rows):,}")

    if not all_rows:
        logger.error("No data rows extracted. Aborting.")
        return

    df = pd.DataFrame(all_rows)

    # Drop exact duplicates (in case any chunk was ever fetched twice)
    before = len(df)
    df = df.drop_duplicates(subset=["neo_id", "close_approach_date"])
    removed = before - len(df)
    if removed:
        logger.info(f"Removed {removed:,} duplicate rows")

    # Clean up types
    df["close_approach_date"] = pd.to_datetime(df["close_approach_date"], errors="coerce")
    df["is_potentially_hazardous"] = df["is_potentially_hazardous"].fillna(False).astype(bool)

    # Sort chronologically
    df = df.sort_values("close_approach_date").reset_index(drop=True)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    # Summary
    logger.info("=" * 72)
    logger.info("SUMMARY")
    logger.info("=" * 72)
    logger.info(f"Files processed:         {len(files):,}")
    logger.info(f"Files with no data:      {empty_files:,}")
    logger.info(f"Total rows (approaches): {len(df):,}")
    logger.info(f"Unique asteroids:        {df['neo_id'].nunique():,}")
    logger.info(f"Hazardous asteroids:     {int(df['is_potentially_hazardous'].sum()):,}")
    if df["close_approach_date"].notna().any():
        logger.info(
            f"Date range:              "
            f"{df['close_approach_date'].min().date()} -> {df['close_approach_date'].max().date()}"
        )
    logger.info(f"Output saved to:         {output_path}")
    logger.info(f"File size:               {output_path.stat().st_size / (1024 * 1024):.2f} MB")
    logger.info(f"Columns:                 {list(df.columns)}")


if __name__ == "__main__":
    main()