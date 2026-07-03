"""
SQLAlchemy database setup and connection pool configuration.

Dynamically switches between local SQLite files and production PostgreSQL backends.
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobs.db")

# SQLite needs connect_args for multithreaded uvicorn/celery workers compatibility
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # Align heroku/supabase postgres:// schema discrepancy to standard postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
