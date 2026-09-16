from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "movie_app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.discovery", "app.tasks.enrichment"],
)

celery_app.conf.beat_schedule = {
   "sync-new-releases-daily": {
       "task" : "app.tasks.discovery.sync_new_releases",
       "schedule" : 60*60*24
   },
   "enrich-new-movies-hourly": {
     "task" : "app.tasks.enrichment.enrich_pending_movies_task",
     "schedule": 60*60
   },
}

celery_app.autodiscover_tasks(["app.tasks"])