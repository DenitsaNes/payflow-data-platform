"""PayFlow — database connection helper."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.utils.config import DB_URL


def get_engine() -> Engine:
    """Return a SQLAlchemy engine for MySQL."""
    return create_engine(DB_URL, future=True)


def test_connection() -> bool:
    """Test that we can connect to MySQL."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
