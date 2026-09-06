from pydantic import BaseModel

from app.schemas.movie import MovieListItem

class RecommendationResponse(BaseModel):
    is_personalized : bool
    recommendations: list[MovieListItem]

