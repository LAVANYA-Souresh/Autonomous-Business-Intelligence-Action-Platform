# analytics/db.py

from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:Lav$2001@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)