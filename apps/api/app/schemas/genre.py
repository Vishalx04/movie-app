from pydantic import BaseModel, ConfigDict
from datetime import datetime

class GenreCreate(BaseModel):
    name : str
    slug:str

class GenreResponse(BaseModel):
    id: int
    name:str
    slug:str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    