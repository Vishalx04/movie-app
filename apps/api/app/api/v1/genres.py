from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.schemas.genre import GenreResponse, GenreCreate
from app.services import genre_service

router = APIRouter(prefix="/genres", tags=["Genres"])

@router.get("/", response_model=list[GenreResponse])
def list_genres(db: Session = Depends(get_db)):
    return genre_service.get_all_genres(db)


@router.post("/", response_model=GenreResponse, status_code=201)
def create_genre(payload: GenreCreate, db:Session = Depends(get_db)):
    try: 
        return genre_service.create_genre(db,payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))