"""
Database engine configuration with SQLite WAL mode for concurrent access.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from database.models import Base, Settings, Floor, User, DEFAULT_SETTINGS, DEFAULT_FLOORS

# Database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'footfall.db')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f'sqlite:///{DB_PATH}'

# Create engine with settings optimized for concurrent LAN access
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and optimizations after each connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")  # Wait 5s on lock
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session():
    """Get a new database session (caller must close)."""
    return SessionLocal()


def init_database():
    """Initialize database with tables and default data."""
    import bcrypt

    # Create all tables
    Base.metadata.create_all(bind=engine)

    with get_db_session() as db:
        # Insert default settings if not exist
        for key, value in DEFAULT_SETTINGS.items():
            existing = db.query(Settings).filter(Settings.key == key).first()
            if not existing:
                db.add(Settings(key=key, value=value))

        # Insert default floors if none exist
        floor_count = db.query(Floor).count()
        if floor_count == 0:
            for floor_data in DEFAULT_FLOORS:
                db.add(Floor(**floor_data))

        # Create default admin user if no users exist
        user_count = db.query(User).count()
        if user_count == 0:
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                username='admin',
                password_hash=password_hash,
                role='admin',
                full_name='Administrator'
            )
            db.add(admin_user)

        db.commit()


def get_setting(key: str, default: str = None) -> str:
    """Get a setting value by key."""
    with get_db_session() as db:
        setting = db.query(Settings).filter(Settings.key == key).first()
        return setting.value if setting else default


def set_setting(key: str, value: str, user_id: int = None):
    """Set a setting value."""
    with get_db_session() as db:
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
            setting.updated_by = user_id
        else:
            db.add(Settings(key=key, value=value, updated_by=user_id))
        db.commit()


def reset_floors_to_defaults():
    """Reset floors to default values."""
    with get_db_session() as db:
        # Delete existing floors
        db.query(Floor).delete()

        # Insert default floors
        for floor_data in DEFAULT_FLOORS:
            db.add(Floor(**floor_data))

        db.commit()
    return len(DEFAULT_FLOORS)
