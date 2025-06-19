import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DB_URL
from dotenv import load_dotenv


load_dotenv()
DB_URL = os.getenv("DB_URL")

if DB_URL is None:
    raise ValueError("DB_URL not found. Check your .env file!")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()