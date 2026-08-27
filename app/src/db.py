"""Database engine and session management (T007)."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
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
    _run_additive_migrations()


def _run_additive_migrations() -> None:
    """Idempotent additive migrations for existing databases.

    Adds columns introduced after initial release when they are missing, so an
    existing SQLite database keeps working without a migration framework.
    """
    inspector = inspect(engine)
    if "test_results" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("test_results")}
        if "log" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE test_results ADD COLUMN log TEXT"))


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
