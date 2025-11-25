# app/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Setup SQLite Database
DB_URL = "sqlite:///./data/logs.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Table
class FlaggedPrompt(Base):
    __tablename__ = "flagged_prompts"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String)
    blocked_layer = Column(String)  # e.g., 'Static', 'ML'
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    blocked_content = Column(Text)  # Used by output validator to store the unsafe response

# Create the database file if it doesn't exist
Base.metadata.create_all(bind=engine)


def ensure_blocked_content_column() -> None:
    """Adds the blocked_content column for existing deployments without running migrations."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "flagged_prompts" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("flagged_prompts")}
    if "blocked_content" in columns:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE flagged_prompts ADD COLUMN blocked_content TEXT"))


ensure_blocked_content_column()