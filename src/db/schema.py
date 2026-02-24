from src.db.conn import get_conn

def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS customers (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        full_name TEXT NOT NULL,
        city TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()

def create_indexes():
    sql = """
    CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
    CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()