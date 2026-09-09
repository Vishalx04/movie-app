from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.recommendation import RecommendationResponse
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/similar-taste/{movielens_user_id}", response_model=RecommendationResponse)
def get_similar_taste_recommendations(
    movielens_user_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    is_personalized, movies = recommendation_service.get_cf_recommendations(
        db, movielens_user_id, n=limit
    )
    return RecommendationResponse(is_personalized=is_personalized, recommendations=movies)


@router.get("/popular", response_model=RecommendationResponse)
def get_popular_movies(
    limit : int = Query(10, ge=1, le=50),
    db : Session = Depends(get_db)
):
    movies = recommendation_service.get_popular_movies(db, n=limit)
    return RecommendationResponse(is_personalized=False, recommendations=movies)

@router.get("/because-you-liked/{movie_id}", response_model=RecommendationResponse)
def get_similar_content_movies(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    movies = recommendation_service.get_similar_movies(db, movie_id, n=limit)
    return RecommendationResponse(is_personalized=bool(movies), recommendations=movies)