"""Database engine and session management (T007)."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import settings
from src.models import Base

_is_sqlite = settings.database_url.startswith("sqlite")
_is_memory = _is_sqlite and ":memory:" in settings.database_url
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
_engine_kwargs = {}
if _is_memory:
    # Share one in-memory database across all connections/threads.
    _engine_kwargs["poolclass"] = StaticPool
engine = create_engine(
    settings.database_url, connect_args=_connect_args, future=True, **_engine_kwargs
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create all tables (bootstrap; migrations framework can replace this later)."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
