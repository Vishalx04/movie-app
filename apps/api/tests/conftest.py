import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.database import Base
from app.db.models import User, Movie, MovieStatus

engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db):
    user = User(
        email="testuser@example.com",
        username="testuser",
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_movie(db):
    movie = Movie(
        tmdb_id="999999",
        title="Test Movie",
        status=MovieStatus.released,
        adult=False,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@pytest.fixture
def enriched_movie(db, test_movie):
    test_movie.poster_path = "/fake-poster.jpg"
    test_movie.backdrop_path = "/fake-backdrop.jpg"
    db.commit()
    db.refresh(test_movie)
    return test_movie