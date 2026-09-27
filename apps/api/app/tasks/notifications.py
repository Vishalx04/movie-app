from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.db.database import sessionLocal
from app.db.models import Movie, Rating, Notification
from app.services.notification_service import (
    notification_exists,
    get_pending_movies,
    find_interested_users,
    generate_notification_text,
)


@celery_app.task
def generate_notifications():
    db = sessionLocal()
    try:
        pending_movies = get_pending_movies(db)
        created = 0

        for movie in pending_movies:
            interested_users = find_interested_users(db, movie)

            for user_id, anchor_movie_id in interested_users.items():
                if notification_exists(db, user_id, movie.id):
                    continue

                anchor_movie = (
                    db.query(Movie).filter(Movie.id == anchor_movie_id).first()
                )
                if not anchor_movie:
                    continue

                message = generate_notification_text(anchor_movie.title, movie.title)
                if not message:
                    continue

                notification = Notification(
                    user_id=user_id,
                    movie_id=movie.id,
                    message=message,
                )

                db.add(notification)
                try:
                    db.commit()
                    created += 1
                except Exception:
                    db.rollback()

            movie.notified_at = datetime.now(timezone.utc)
            db.commit()

        print(f"Notification run complete. Created: {created}")
        return {"created": created}
    finally:
        db.close()
