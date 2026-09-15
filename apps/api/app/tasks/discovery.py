import time

import requests

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import sessionLocal
from app.db.models import Movie

REQUEST_DELAY_SECONDS = 0.05
MAX_RETRIES = 3
CONNECTION_RETRY_DELAY = 3


def fetch_now_playing_page(session: requests.Session, page: int) -> dict | None:
    url = f"{settings.TMDB_BASE_URL}/movie/now_playing"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}",
    }
    params = {"language": "en-US", "page": page}

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
            print("FATAL: TMDB rejected the API key (401). Stopping run.")
            return None

        print(f"    page={page} returned {response.status_code}, retrying ({attempt}/{MAX_RETRIES})")
        time.sleep(1)

    return None


@celery_app.task
def sync_new_releases():
    db = sessionLocal()
    session = requests.Session()

    inserted = 0
    skipped_existing = 0

    try:
        existing_tmdb_ids = {m.tmdb_id for m in db.query(Movie.tmdb_id)}

        page = 1
        total_pages = 1

        while page <= total_pages:
            data = fetch_now_playing_page(session, page)

            if data is None:
                # Real, persistent failure (auth or repeated connection
                # errors) — stop the run rather than silently looping
                # forever or reporting a false "complete".
                print(f"Aborting sync — failed to fetch page {page} after retries.")
                break

            total_pages = min(data.get("total_pages", 1), 5)

            for result in data.get("results", []):
                tmdb_id = str(result["id"])

                if tmdb_id in existing_tmdb_ids:
                    skipped_existing += 1
                    continue

                movie = Movie(
                    tmdb_id=tmdb_id,
                    title=result.get("title", "Untitled"),
                    adult=result.get("adult", False),
                )

                db.add(movie)
                existing_tmdb_ids.add(tmdb_id)
                inserted += 1

            db.commit()
            page += 1
            time.sleep(REQUEST_DELAY_SECONDS)

    finally:
        db.close()
        session.close()

    print(f"Discovery job complete. Inserted: {inserted}, already_existing: {skipped_existing}")
    return {"inserted": inserted, "skipped_existing": skipped_existing}