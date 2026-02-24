import os
import json
from typing import List, Tuple

from psycopg2.extras import execute_values
from src.config import DATA_FILE_PATH
from src.db.conn import get_conn

def load_seed_rows_from_file() -> List[Tuple[str, str, str]]:
    if not os.path.exists(DATA_FILE_PATH):
        raise FileNotFoundError(
            f"Could not find data.json at: {DATA_FILE_PATH}. Place it in project root."
        )

    with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("data.json must contain a JSON array of objects.")

    rows: List[Tuple[str, str, str]] = []
    required_fields = {"name", "city", "status"}

    for i, r in enumerate(payload):
        if not isinstance(r, dict):
            raise ValueError(f"Row {i} is invalid. Each row must be a JSON object.")
        if not required_fields.issubset(r.keys()):
            raise ValueError(f"Row {i} missing required fields. Expected keys: {required_fields}")

        rows.append((str(r["name"]), str(r["city"]), str(r["status"])))

    if not rows:
        raise ValueError("data.json is empty (no rows).")

    return rows

def validate_seed_rows(rows: List[Tuple[str, str, str]]) -> None:
    allowed_status = {"active", "inactive"}

    bad_blank = []
    bad_status = []

    for i, (name, city, status) in enumerate(rows):
        name_t = (name or "").strip()
        city_t = (city or "").strip()
        status_t = (status or "").strip().lower()

        if not name_t or not city_t or not status_t:
            bad_blank.append(i)

        if status_t and status_t not in allowed_status:
            bad_status.append((i, status))

    if bad_blank:
        raise ValueError(f"DQ failed: blank fields in rows (0-based indexes): {bad_blank[:20]}")

    if bad_status:
        sample = bad_status[:10]
        raise ValueError(f"DQ failed: invalid status. Allowed={sorted(allowed_status)}. Sample={sample}")

def seed_rows_into_db(rows: List[Tuple[str, str, str]]) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE customers RESTART IDENTITY;")
            execute_values(cur, "INSERT INTO customers (full_name, city, status) VALUES %s;", rows)
        conn.commit()
    return len(rows)