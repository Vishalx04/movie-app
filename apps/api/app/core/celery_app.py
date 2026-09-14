from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "movie_app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.beat_schedule = {
    "sanity-check-every-10-seconds": {
        "task" : "app.core.celery_app.sanity_check_task",
        "schedule" : 10.0
    },
}

@celery_app.task
def sanity_check_task():
    print("Celery Beat fired this task automatically — plumbing works.")
