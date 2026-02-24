import psycopg2
from src.config import DATABASE_URL

def get_conn():
    return psycopg2.connect(DATABASE_URL)