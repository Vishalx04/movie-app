from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.db.models import WatchlistStatus

class WatchlistCreate(BaseModel):
    movie_id : int

class WatchlistStatusUpdate(BaseModel):
    status : WatchlistStatus

class WatchlistResponse(BaseModel):
    id : int
    movie_id : int
    status : WatchlistStatus
    added_at:datetime
    watched_at:datetime | None

    model_config = ConfigDict(from_attributes=True)

    