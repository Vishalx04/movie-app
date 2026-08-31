import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token
from app.db.database import Base, get_db
from app.db.models import Movie, MovieStatus, User, UserRole
from app.main import app


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

@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_user(db):

    user = User(
        email = "admin@example.com",
        username = "adminuser",
        name = "Admin user",
        role = UserRole.admin
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_auth_headers(admin_user):
    token = create_access_token({"sub" : str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}
    