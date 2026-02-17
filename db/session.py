import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fix for Supabase/SQLAlchemy 2.0 protocol
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# echo=True is great for development; it prints every SQL query to your terminal
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# This creates a "factory" for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)