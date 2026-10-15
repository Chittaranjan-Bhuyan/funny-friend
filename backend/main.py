import os
import random
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

# ---------- MySQL settings (change here or set environment variables) ----------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "system")
DB_NAME = os.getenv("DB_NAME", "crush_calculator")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def raw_connection(with_db: bool = True):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if with_db else None,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )


@contextmanager
def get_cursor():
    conn = raw_connection()
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def init_db():
    """Create the database and table if they don't exist yet."""
    conn = raw_connection(with_db=False)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()

    with get_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                your_name VARCHAR(50) NOT NULL,
                crush_name VARCHAR(50) NOT NULL,
                score TINYINT UNSIGNED NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Crush Calculator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CalculateRequest(BaseModel):
    your_name: str
    crush_name: str

    @field_validator("your_name", "crush_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name can't be empty")
        if len(value) > 50:
            raise ValueError("Name must be 50 characters or fewer")
        return value


@app.post("/api/calculate")
def calculate(payload: CalculateRequest):
    score = random.randint(90, 99)  # always between 90 and 99 percent
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO results (your_name, crush_name, score) VALUES (%s, %s, %s)",
                (payload.your_name, payload.crush_name, score),
            )
            new_id = cur.lastrowid
    except pymysql.MySQLError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    return {
        "id": new_id,
        "your_name": payload.your_name,
        "crush_name": payload.crush_name,
        "score": score,
    }


@app.get("/api/results")
def recent_results(limit: int = 10):
    limit = max(1, min(limit, 50))
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, your_name, crush_name, score, created_at "
                "FROM results ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
    except pymysql.MySQLError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return rows


# Serve the website from the same server (must be added last)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")