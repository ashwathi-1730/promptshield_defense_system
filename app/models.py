# app/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
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

# Create the database file if it doesn't exist
Base.metadata.create_all(bind=engine)