import os
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def now():
    return datetime.now(timezone.utc)


class Monitor(Base):
    __tablename__ = "monitors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


class Check(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    ok = Column(Boolean, nullable=False)
    checked_at = Column(DateTime(timezone=True), default=now)
