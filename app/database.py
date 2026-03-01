"""Database configuration for ChurGPT."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - default to SQLite for development
# For PostgreSQL: postgresql://postgres:postgres@localhost:5432/churgpt
# For SQLite: sqlite:///./churgpt.db
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./churgpt.db"
)

# Create engine with appropriate configuration for SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
