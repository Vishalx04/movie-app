from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Table,
    ForeignKey,
    BigInteger,
    Boolean,
    Float,
    Text,
    Date,
    UniqueConstraint,
)
from datetime import datetime, timezone
from app.db.database import Base
from sqlalchemy.orm import relationship
import enum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MovieStatus(str, enum.Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"
    planned = "Planned"
    cancelled = "Cancelled"
    rumored = "Rumored"


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    tmdb_id = Column(String(50), nullable=False, unique=True)
    imdb_id = Column(String(50), nullable=True, unique=True)
    movielens_id = Column(Integer, nullable=True, unique=True)

    title = Column(String(255), nullable=False)
    original_title = Column(String(255), nullable=True)
    tagline = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    runtime = Column(Integer, nullable=True)
    released_on = Column(Date, nullable=True)

    poster_path = Column(String(255), nullable=True)
    backdrop_path = Column(String(255), nullable=True)
    original_language = Column(String(10), nullable=True)

    status = Column(
        Enum(MovieStatus), nullable=False, default=MovieStatus.released
    )

    budget = Column(BigInteger, nullable=True)
    revenue = Column(BigInteger, nullable=True)
    adult = Column(Boolean, nullable=False, default=False)

    tmdb_vote_average = Column(Float, nullable=True)
    tmdb_vote_count = Column(Integer, nullable=True)
    trailer_link = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    genres = relationship("Genre", secondary=movie_genres, backref="movies")
    cast = relationship("MovieCast", back_populates="movie")
    platforms = relationship("MoviePlatform", back_populates="movie")
    ratings = relationship("Rating", back_populates="movie")
    watchlist_items = relationship("WatchlistItem", back_populates="movie")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id = Column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    rating = Column(Float, nullable=False)
    rated_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")


class WatchlistStatus(str, enum.Enum):
    want_to_watch = "want_to_watch"
    watched = "watched"
    abandoned = "abandoned"


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id = Column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum(WatchlistStatus),
        nullable=False,
        default=WatchlistStatus.want_to_watch,
    )
    added_at = Column(DateTime, default=utcnow, nullable=False)
    watched_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "movie_id", name="uq_user_movie_watchlist"
        ),
    )

    user = relationship("User", back_populates="watchlist_items")
    movie = relationship("Movie", back_populates="watchlist_items")


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=True)
    tmdb_id = Column(String(50), nullable=False, unique=True)
    imdb_id = Column(String(50), nullable=True, unique=True)

    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    birthday = Column(DateTime, nullable=True)
    deathday = Column(DateTime, nullable=True)
    place_of_birth = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    movie_credits = relationship("MovieCast", back_populates="person")


class MovieCast(Base):
    __tablename__ = "movie_cast"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)

    character_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    billing_order = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "movie_id", "person_id", "role", name="uq_movie_person_role"
        ),
    )

    movie = relationship("Movie", back_populates="cast")
    person = relationship("Person", back_populates="movie_credits")


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    logo_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


class PlatformType(str, enum.Enum):
    stream = "stream"
    rent = "rent"
    buy = "buy"
    subscribe = "subscribe"


class MoviePlatform(Base):
    __tablename__ = "movie_platforms"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    platform_type = Column(Enum(PlatformType), nullable=False)
    region = Column(String(5), nullable=True)
    url = Column(String(500), nullable=True)
    checked_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "movie_id",
            "platform_id",
            "platform_type",
            "region",
            name="uq_movie_platform_type_region",
        ),
    )

    movie = relationship("Movie", back_populates="platforms")
    platform = relationship("Platform")


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    role = Column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.user
    )
    is_seed_user = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    credentials = relationship(
        "UserCredentials", back_populates="user", uselist=False
    )
    ratings = relationship("Rating", back_populates="user")
    watchlist_items = relationship("WatchlistItem", back_populates="user")


class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True
    )
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    user = relationship("User", back_populates="credentials")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User")