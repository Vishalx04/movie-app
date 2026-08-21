from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.core.dependencies import require_admin
from app.db.database import get_db
from app.schemas.genre import GenreResponse, GenreCreate
from app.services import genre_service
from app.db.models import User

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("/", response_model=list[GenreResponse])
def list_genres(db: Session = Depends(get_db)):
    return genre_service.get_all_genres(db)


@router.post("/", response_model=GenreResponse, status_code=201)
def create_genre(
    payload: GenreCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return genre_service.create_genre(db, payload)
