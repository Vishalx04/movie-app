from fastapi import FastAPI
from app.db.database import engine
from sqlalchemy import text
app = FastAPI(
    title="Movie App",
    description="A movie recommendation app",
    version="0.1.0"
)

@app.get("/")
def hello():
    return {"message: hello world"}


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"database" : "connected"}