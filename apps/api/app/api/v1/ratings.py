from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.db.models import User
from app.schemas.rating import RatingCreate, RatingResponse
from app.services import rating_service

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/", response_model=RatingResponse, status_code=201)
def rate_movie(payload:RatingCreate,db:Session = Depends(get_db), current_user:User = Depends(get_current_user) ):
    try:
        return rating_service.upsert_rating(db,current_user.id, payload.movie_id,payload.rating)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/me", response_model=list[RatingResponse])
def get_my_ratings(db:Session = Depends(get_db), current_user : User = Depends(get_current_user)  ):
    return rating_service.get_user_ratings(db, current_user.id)

@router.get("/movie/{movie_id}", response_model=RatingResponse)
def get_my_rating_for_movie(movie_id :int,db:Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    rating = rating_service.get_user_rating_for_movie(db,current_user.id,movie_id )
    if not rating:
        raise HTTPException(status_code=404, detail="You havent rated this movie")

    return rating

@router.delete("/movie/{movie_id}", status_code=204)
def unrate_movie(movie_id : int , db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    deleted = rating_service.delete_rating(db,current_user.id, movie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rating not found")