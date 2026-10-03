from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Run lightweight schema migrations for existing SQLite databases."""
    with engine.connect() as conn:
        columns_to_add = [
            ("users", "location_type", "VARCHAR DEFAULT 'HOME'"),
            ("users", "onboarding_completed", "BOOLEAN DEFAULT 0"),
            ("videos", "profile", "VARCHAR DEFAULT 'ROAD_PARKING'"),
            ("videos", "source_type", "VARCHAR DEFAULT 'upload'"),
            ("videos", "camera_id", "INTEGER"),
            ("incidents", "zone_id", "INTEGER"),
            ("incidents", "type", "VARCHAR DEFAULT 'ACCIDENT'"),
            ("incidents", "bbox", "JSON"),
            ("incidents", "description", "TEXT"),
            ("incidents", "reviewed_status", "VARCHAR DEFAULT 'FLAGGED_FOR_REVIEW'"),
        ]

        for table, col, col_def in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def};"))
                conn.commit()
            except Exception:
                # Column likely already exists
                pass
