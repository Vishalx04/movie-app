from app.core.celery_app import celery_app
from app.services.enrichment_service import enrich_pending_movies, TMDBAuthError

@celery_app.task
def enrich_pending_movies_task():
    try:
        result = enrich_pending_movies(100)
    except TMDBAuthError as e:
        print(f"FATAL: {e}. Fix TMDB_READ_ACCESS_TOKEN - skipping this run.")
        return {"error" : str(e)}


    print(f"Scheduled enrichment complete: {result}")
    return result