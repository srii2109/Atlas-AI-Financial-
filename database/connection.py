import os
from peewee import SqliteDatabase
from dotenv import load_dotenv

load_dotenv()

# Default database path
db_path = os.getenv("DB_PATH", "finance_assistant.db")

# Initialize database
db = SqliteDatabase(db_path)

def get_db():
    return db
