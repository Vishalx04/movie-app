from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_ENV : str = "development"
    APP_TITLE : str = "Movie app"
    APP_VERSION : str = "0.1.0"
    SECRET_KEY : str 


    DATABASE_URL : str = "postgresql+psycopg2://postgres:postgres@localhost:5432/movie_db"

    ACCESS_TOKEN_EXPIRE_MINUTES : int = 30
    REFRESH_TOKEN_EXPIRE_DAYS : int = 7


    TMDB_API_KEY : str
    TMDB_BASE_URL : str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL :str ="https://image.tmdb.org/t/p"


    ALLOWED_ORIGINS : List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        class_sensitive = "True"


settings = Settings()