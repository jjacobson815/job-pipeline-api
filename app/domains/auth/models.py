"""
SQLAlchemy models for user accounts and execution run histories.
"""

from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """Registered application user credentials, configurations, and profile."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Profile & Settings
    resume_text = Column(Text, nullable=True, default="")
    gemini_api_key = Column(String(255), nullable=True)
    teal_api_key = Column(String(255), nullable=True)

    # Relations
    runs = relationship("PipelineRun", back_populates="user", cascade="all, delete-orphan")


class PipelineRun(Base):
    """Historical record of an alignment ingestion and match pipeline run."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255), unique=True, index=True, nullable=False)
    timestamp = Column(String(255), nullable=False)
    total_jobs = Column(Integer, nullable=False, default=0)
    succeeded_jobs = Column(Integer, nullable=False, default=0)
    avg_score = Column(Float, nullable=False, default=0.0)
    result_json = Column(Text, nullable=False)  # Serialised JSON output

    # Relations
    user = relationship("User", back_populates="runs")
