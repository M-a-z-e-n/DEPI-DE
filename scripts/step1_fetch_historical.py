"""
CosmicTracker - Historical Data Fetcher (6 Years)
==================================================
Fetches Near-Earth Object (NEO) data from NASA NeoWs API for the last 6 years.
Splits the date range into 7-day chunks and organizes JSON files by year/month.

Features:
- 6 years of historical data (~313 chunks)
- Resume logic (restart-safe)
- Retry logic with exponential backoff
- Rate limiting (safe for 1000/hour limit)
- Progress bar with ETA
- Organized folder structure: data/raw/YYYY/MM/
- Detailed logging to logs/fetch.log
- Summary statistics at the end

Usage:
    python scripts/step1_fetch_historical.py

    # Or customize years:
    python scripts/step1_fetch_historical.py --years 6
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from tqdm import tqdm
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "fetch.log"

# Default: 6 years
DEFAULT_YEARS = 6

# API limits
CHUNK_SIZE_DAYS = 7
SLEEP_BETWEEN_REQUESTS = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF = 5


# ============================================================================
# LOGGING SETUP
# ============================================================================
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
def generate_date_chunks(start_date, end_date, chunk_size=7):
    """Split date range into 7-day chunks (NASA API limit)."""
    chunks = []
    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=chunk_size - 1), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def get_output_path(start, end):
    """
    Build organized path:
    data/raw/YYYY/MM/YYYY-MM-DD_to_YYYY-MM-DD.json
    """
    folder = OUTPUT_DIR / str(start.year) / f"{start.month:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{start.isoformat()}_to_{end.isoformat()}.json"
    return folder / filename


def fetch_chunk(start, end, retries=0):
    """Fetch one 7-day chunk with retry logic."""
    params = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "api_key": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)

        if response.status_code == 429:
            wait = RETRY_BACKOFF * (2 ** retries)
            logger.warning(f"Rate limited. Waiting {wait}s before retry...")
            time.sleep(wait)
            if retries < MAX_RETRIES:
                return fetch_chunk(start, end, retries + 1)
            raise Exception("Max retries exceeded for rate limit")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        if retries < MAX_RETRIES:
            wait = RETRY_BACKOFF * (2 ** retries)
            logger.warning(f"Request failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
            return fetch_chunk(start, end, retries + 1)
        raise


def count_asteroids(data):
    """Count total asteroids in the response."""
    if not data or "near_earth_objects" not in data:
        return 0
    return sum(len(v) for v in data["near_earth_objects"].values())


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds % 60)}s"
    hours = minutes / 60
    return f"{int(hours)}h {int(minutes % 60)}m"


def print_banner(years):
    """Print a nice banner."""
    banner = f"""
{'=' * 72}
                  CosmicTracker - NASA NeoWs Data Fetcher
{'=' * 72}
  Period:    Last {years} years
  Source:    https://api.nasa.gov/neo/rest/v1/feed
  Output:    data/raw/YYYY/MM/
  API Key:   {'CONFIGURED' if API_KEY != 'DEMO_KEY' else 'DEMO_KEY (LIMITED!)'}
{'=' * 72}
"""
    print(banner)
    logger.info(f"Starting fetch for {years} years")


# ============================================================================
# MAIN
# ============================================================================
def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Fetch NASA NeoWs historical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python scripts/step1_fetch_historical.py\n"
               "  python scripts/step1_fetch_historical.py --years 6\n"
               "  python scripts/step1_fetch_historical.py --years 10"
    )
    parser.add_argument(
        "--years", type=int, default=DEFAULT_YEARS,
        help=f"Number of years to fetch (default: {DEFAULT_YEARS})"
    )
    args = parser.parse_args()

    # Date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365 * args.years)

    print_banner(args.years)

    logger.info(f"Date range: {start_date} -> {end_date}")
    logger.info(f"Total days: {(end_date - start_date).days}")

    # Warn if using DEMO_KEY for large fetches
    if API_KEY == "DEMO_KEY" and args.years > 1:
        logger.warning("=" * 60)
        logger.warning("USING DEMO_KEY for large fetch!")
        logger.warning("DEMO_KEY is limited to 30 requests/hour, 50/day.")
        logger.warning("Get a free key from https://api.nasa.gov")
        logger.warning("=" * 60)

    # Generate chunks
    chunks = generate_date_chunks(start_date, end_date, CHUNK_SIZE_DAYS)
    logger.info(f"Total chunks to process: {len(chunks)}")

    # Resume logic
    pending = []
    skipped = 0
    for start, end in chunks:
        path = get_output_path(start, end)
        if path.exists() and path.stat().st_size > 0:
            skipped += 1
        else:
            pending.append((start, end))

    if skipped > 0:
        logger.info(f"Resume mode: {skipped} chunks already exist, skipping.")
    logger.info(f"Pending: {len(pending)} chunks")

    if not pending:
        logger.info("All chunks already downloaded. Nothing to do.")
        print_summary_existing()
        return

    # Time estimate
    avg_seconds_per_chunk = SLEEP_BETWEEN_REQUESTS + 2.0
    estimated_seconds = len(pending) * avg_seconds_per_chunk
    logger.info(f"Estimated time: ~{format_duration(estimated_seconds)}")

    # Fetch loop
    start_time = time.time()
    total_asteroids = 0
    failed_chunks = []

    progress = tqdm(
        pending,
        desc="Fetching",
        unit="chunk",
        bar_format="{l_bar}{bar:30}{r_bar}"
    )
    for start, end in progress:
        progress.set_postfix_str(f"{start}")
        path = get_output_path(start, end)

        try:
            data = fetch_chunk(start, end)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            count = count_asteroids(data)
            total_asteroids += count
            logger.info(f"OK   {start} -> {end}: {count:>4} asteroids -> {path.name}")

        except Exception as e:
            logger.error(f"FAIL {start} -> {end}: {e}")
            failed_chunks.append((start, end))

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    elapsed = time.time() - start_time

    # Summary
    print("\n")
    logger.info("=" * 72)
    logger.info("SUMMARY")
    logger.info("=" * 72)
    logger.info(f"Total time:        {format_duration(elapsed)}")
    logger.info(f"Successful chunks: {len(pending) - len(failed_chunks)}/{len(pending)}")
    logger.info(f"Asteroids fetched: {total_asteroids:,}")
    logger.info(f"Output location:   {OUTPUT_DIR}")

    if failed_chunks:
        logger.warning(f"\nFailed chunks ({len(failed_chunks)}):")
        for start, end in failed_chunks:
            logger.warning(f"  - {start} -> {end}")
        logger.info("Run the script again to retry failed chunks (resume logic).")
    else:
        logger.info("\nAll chunks downloaded successfully!")

    # Folder structure summary
    print_folder_structure()


def print_summary_existing():
    """Print summary when all files already exist."""
    files = list(OUTPUT_DIR.rglob("*.json"))
    total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
    logger.info(f"Existing files: {len(files)}")
    logger.info(f"Total size:     {total_size:.1f} MB")
    print_folder_structure()


def print_folder_structure():
    """Print a tree view of the data folder."""
    logger.info("\nFolder structure:")
    if not OUTPUT_DIR.exists():
        return

    years = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()])
    for year_dir in years:
        year_files = list(year_dir.rglob("*.json"))
        logger.info(f"  data/raw/{year_dir.name}/ ({len(year_files)} files)")
        months = sorted([d for d in year_dir.iterdir() if d.is_dir()])
        for month_dir in months:
            month_files = list(month_dir.glob("*.json"))
            logger.info(f"    |- {month_dir.name}/ ({len(month_files)} files)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user. Run the script again to resume.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
