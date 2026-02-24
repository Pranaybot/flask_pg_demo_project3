import os
import time
import json
from typing import Any, Dict, List, Tuple

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

load_dotenv()

# ------------------------------------------------------------
# DB connection (defaults match your pgacid container on 5432)
# ------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")   # pgacid shows 5432/tcp
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app = Flask(__name__)

# data.json should live next to app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR, "data.json")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS customers (
        id BIGSERIAL PRIMARY KEY,
        full_name TEXT NOT NULL,
        city TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


def load_seed_rows_from_file() -> List[Tuple[str, str, str]]:
    """
    Loads rows from ./data.json

    Expected format:
      [
        ["Ava Smith", "Minneapolis", "active"],
        ...
      ]
    """
    if not os.path.exists(DATA_FILE_PATH):
        raise FileNotFoundError(
            f"Could not find data.json at: {DATA_FILE_PATH}. "
            "Place data.json in the same folder as app.py."
        )

    with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("data.json must contain a JSON array of rows.")

    rows: List[Tuple[str, str, str]] = []
    for i, r in enumerate(payload):
        if not isinstance(r, list) or len(r) != 3:
            raise ValueError(
                f"Row {i} is invalid. Each row must be an array of exactly 3 values: "
                "[full_name, city, status]."
            )
        rows.append((str(r[0]), str(r[1]), str(r[2])))

    if not rows:
        raise ValueError("data.json is empty (no rows).")

    return rows


def seed_rows_into_db(rows: List[Tuple[str, str, str]]) -> int:
    """
    Truncates and inserts rows into customers.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE customers RESTART IDENTITY;")
            execute_values(
                cur,
                "INSERT INTO customers (full_name, city, status) VALUES %s;",
                rows
            )
        conn.commit()
    return len(rows)


def create_indexes():
    """
    Basic DB optimization:
      - B-tree indexes for equality filters on city/status
    """
    sql = """
    CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
    CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


@app.post("/seed")
def seed():
    """
    Seeds the customers table from ./data.json (same folder as app.py).

    Usage:
      curl -X POST http://localhost:5000/seed
    """
    try:
        init_db()
        rows = load_seed_rows_from_file()
        inserted = seed_rows_into_db(rows)
        return jsonify({
            "ok": True,
            "inserted": inserted,
            "source": "data.json"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/index")
def index():
    """
    Creates indexes for the filtered search.
    Usage:
      curl -X POST http://localhost:5000/index
    """
    init_db()
    create_indexes()
    return jsonify({"ok": True, "message": "Indexes created (city, status)."})


@app.get("/search")
def search():
    """
    Filtered search endpoint:
      /search?city=Minneapolis&status=active&name=Ava

    Filters are optional. `name` uses ILIKE with %...% for partial match.
    """
    init_db()

    city = request.args.get("city")
    status = request.args.get("status")
    name = request.args.get("name")

    where = []
    params = []

    if city:
        where.append("city = %s")
        params.append(city)

    if status:
        where.append("status = %s")
        params.append(status)

    if name:
        where.append("full_name ILIKE %s")
        params.append(f"%{name}%")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
    SELECT id, full_name, city, status
    FROM customers
    {where_sql}
    ORDER BY id
    LIMIT 50;
    """

    t0 = time.perf_counter()
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    t1 = time.perf_counter()

    return jsonify({
        "filters": {"city": city, "status": status, "name": name},
        "query_time_ms": round((t1 - t0) * 1000, 3),
        "results": rows
    })


@app.get("/perf")
def perf():
    """
    BEFORE vs AFTER query plan + timing.

    BEFORE: discourage index usage (Seq Scan is likely)
    AFTER : normal planning (indexes can be used)

    Example:
      /perf?city=Minneapolis&status=active&name=Ava
    """
    init_db()

    city = request.args.get("city")
    status = request.args.get("status")
    name = request.args.get("name")

    where = []
    params = []

    if city:
        where.append("city = %s")
        params.append(city)

    if status:
        where.append("status = %s")
        params.append(status)

    if name:
        where.append("full_name ILIKE %s")
        params.append(f"%{name}%")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    base_query = f"""
    SELECT id, full_name, city, status
    FROM customers
    {where_sql}
    ORDER BY id
    LIMIT 50;
    """

    explain_query = "EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + base_query

    def run_explain(mode: str) -> Dict[str, Any]:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if mode == "before":
                    cur.execute("SET LOCAL enable_indexscan = off;")
                    cur.execute("SET LOCAL enable_bitmapscan = off;")
                    cur.execute("SET LOCAL enable_indexonlyscan = off;")
                else:
                    cur.execute("SET LOCAL enable_indexscan = on;")
                    cur.execute("SET LOCAL enable_bitmapscan = on;")
                    cur.execute("SET LOCAL enable_indexonlyscan = on;")

                t0 = time.perf_counter()
                cur.execute(explain_query, tuple(params))
                lines = [r[0] for r in cur.fetchall()]
                t1 = time.perf_counter()

        scan_type = None
        planning_ms = None
        exec_ms = None

        for ln in lines:
            if scan_type is None:
                if "Seq Scan" in ln:
                    scan_type = "Seq Scan"
                elif "Bitmap" in ln:
                    scan_type = "Bitmap Scan"
                elif "Index Scan" in ln:
                    scan_type = "Index Scan"

            if "Planning Time:" in ln:
                try:
                    planning_ms = float(ln.split("Planning Time:")[1].strip().split()[0])
                except Exception:
                    pass

            if "Execution Time:" in ln:
                try:
                    exec_ms = float(ln.split("Execution Time:")[1].strip().split()[0])
                except Exception:
                    pass

        return {
            "scan_type_hint": scan_type,
            "planning_time_ms": planning_ms,
            "execution_time_ms": exec_ms,
            "wall_clock_ms": round((t1 - t0) * 1000, 3),
            "plan": lines
        }

    before = run_explain("before")
    after = run_explain("after")

    return jsonify({
        "filters": {"city": city, "status": status, "name": name},
        "before": before,
        "after": after,
        "note": "For a clearer difference, create indexes (POST /index) and filter on city/status. With very small tables, times may still be close."
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)