"""Database session and connection management."""

from __future__ import annotations
import logging
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings
from src.database.models import Base

logger = logging.getLogger(__name__)

def _get_sqlite_url() -> str:
    default_path = Path(__file__).parent.parent.parent / "data" / "leadforge.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_path}"

db_url = settings.database_url

def _create_engine_safely():
    global db_url
    if db_url.startswith("sqlite"):
        db_path = Path(db_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(db_url, connect_args={"check_same_thread": False})
    
    # Try PostgreSQL/External DB
    try:
        eng = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database: Connected successfully to external database")
        return eng
    except Exception as e:
        logger.warning("Database: External database connection failed (%s); falling back to local SQLite", e)
        db_url = _get_sqlite_url()
        return create_engine(db_url, connect_args={"check_same_thread": False})

engine = _create_engine_safely()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def init_db() -> None:
    """Initialize database schema tables and seed default organization and admin."""
    global engine, SessionLocal, db_url
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Schema creation failed on primary engine (%s). Falling back to SQLite.", e)
        db_url = _get_sqlite_url()
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)

    try:
        from src.security.auth import seed_default_data
        with get_db() as session:
            seed_default_data(session)
    except Exception as e:
        logger.warning("Default seed data check: %s", e)


@contextmanager
def get_db():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session():
    return get_db()

