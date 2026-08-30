import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

import requests  
from app.core.config import settings 
from app.db.database import sessionLocal  
from app.db.models import Movie, MovieStatus  

REQUEST_DELAY_SECONDS = 0.05
MAX_RETRIES = 3
CONNECTION_RETRY_DELAY = 3
NOT_FOUND_MARKER = ""  # poster_path sentinel: "tried TMDB, no match found"

STATUS_MAP = {
    "Released": MovieStatus.released,
    "Post Production": MovieStatus.post_production,
    "In Production": MovieStatus.in_production,
    "Planned": MovieStatus.planned,
    "Cancelled": MovieStatus.cancelled,
    "Rumored": MovieStatus.rumored,
}


def fetch_tmdb_details(session: requests.Session, tmdb_id: str) -> dict | None:

    url = f"{settings.TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {"language": "en-US"}
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, headers=headers, params=params, timeout=15)
        except requests.exceptions.RequestException as e:
            print(f"    connection error ({type(e).__name__}), retrying ({attempt}/{MAX_RETRIES})")
            time.sleep(CONNECTION_RETRY_DELAY)
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 401:
            print("\nFATAL: TMDB rejected the API key (401 Unauthorized).")
            print("This is not a per-movie problem — stopping immediately so no")
            print("data gets incorrectly marked as 'not found'. Fix TMDB_READ_ACCESS_TOKEN in .env first.")
            sys.exit(1)

        if response.status_code == 404:
            return None  # deprecated / missing id, not an error worth retrying

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            print(f"    rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        print(f"    tmdb_id={tmdb_id} returned {response.status_code}, retrying ({attempt}/{MAX_RETRIES})")
        time.sleep(1)

    return None


def apply_tmdb_data(movie: Movie, data: dict) -> None:
    movie.original_title = data.get("original_title")
    movie.tagline = data.get("tagline") or None
    movie.description = data.get("overview") or None
    movie.runtime = data.get("runtime") or None
    movie.released_on = data.get("release_date") or None
    movie.poster_path = data.get("poster_path")
    movie.backdrop_path = data.get("backdrop_path")
    movie.original_language = data.get("original_language")
    movie.budget = data.get("budget") or None
    movie.revenue = data.get("revenue") or None
    movie.adult = bool(data.get("adult", False))
    movie.tmdb_vote_average = data.get("vote_average")
    movie.tmdb_vote_count = data.get("vote_count")
    movie.imdb_id = data.get("imdb_id") or None

    tmdb_status = data.get("status")
    if tmdb_status in STATUS_MAP:
        movie.status = STATUS_MAP[tmdb_status]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=200,
        help="Max number of movies to enrich this run. 0 = no limit."
    )
    args = parser.parse_args()

    db = sessionLocal()
    session = requests.Session()

    enriched = 0
    not_found = 0
    failed = 0

    try:
        query = db.query(Movie).filter(Movie.poster_path.is_(None))
        if args.limit > 0:
            query = query.limit(args.limit)

        movies = query.all()
        total = len(movies)
        print(f"Enriching {total} movie(s)...")

        for i, movie in enumerate(movies, start=1):
            data = fetch_tmdb_details(session, movie.tmdb_id)

            if data is None:
                movie.poster_path = NOT_FOUND_MARKER
                db.commit()
                not_found += 1
                print(f"  [{i}/{total}] tmdb_id={movie.tmdb_id} '{movie.title}' — not found, marked skipped")
                time.sleep(REQUEST_DELAY_SECONDS)
                continue

            try:
                apply_tmdb_data(movie, data)
                db.commit()
                enriched += 1
            except Exception as e:
                db.rollback()
                failed += 1
                print(f"  [{i}/{total}] tmdb_id={movie.tmdb_id} '{movie.title}' — failed to save: {e}")

            if i % 50 == 0:
                print(f"  ...{i}/{total} processed")

            time.sleep(REQUEST_DELAY_SECONDS)

    finally:
        db.close()
        session.close()

    print("\nEnrichment complete.")
    print(f"  Enriched:   {enriched}")
    print(f"  Not found:  {not_found}")
    print(f"  Failed:     {failed}")


if __name__ == "__main__":
    main()