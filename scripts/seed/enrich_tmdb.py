import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.services.enrichment_service import enrich_pending_movies, TMDBAuthError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=200,
        help="Max number of movies to enrich this run. 0 = no limit."
    )
    args = parser.parse_args()

    try:
        result = enrich_pending_movies(limit=args.limit)
    except TMDBAuthError as e:
        print(f"\nFATAL: {e}")
        print("Fix TMDB_READ_ACCESS_TOKEN in .env before retrying.")
        sys.exit(1)

    print("\nEnrichment complete.")
    print(f"  Enriched:   {result['enriched']}")
    print(f"  Not found:  {result['not_found']}")
    print(f"  Failed:     {result['failed']}")


if __name__ == "__main__":
    main()