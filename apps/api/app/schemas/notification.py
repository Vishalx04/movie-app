from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    id : int 
    movie_id : int 
    message : str
    is_read = bool
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)
