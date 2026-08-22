from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    movie_id: int
    rating: float = Field(ge=0.5, le=5.0)


class RatingResponse(BaseModel):
    id: int
    movie_id: int
    rating: float
    rated_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)