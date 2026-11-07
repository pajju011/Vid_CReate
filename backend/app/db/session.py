from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import app.models.entities
    # Enable WAL mode for concurrent multi-threaded safety in SQLite
    if "sqlite" in settings.DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.execute(text("PRAGMA synchronous=NORMAL;"))
                conn.commit()
            except Exception:
                pass

    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate columns if missing in SQLite
    if "sqlite" in settings.DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(jobs)"))
                cols = [row[1] for row in res.fetchall()]
                if "checkpoint_data" not in cols:
                    conn.execute(text("ALTER TABLE jobs ADD COLUMN checkpoint_data JSON DEFAULT '{}'"))
                if "privacy_mode" not in cols:
                    conn.execute(text("ALTER TABLE jobs ADD COLUMN privacy_mode VARCHAR DEFAULT 'private_hybrid'"))
                conn.commit()
            except Exception:
                pass

