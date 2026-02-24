import time
from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor

from src.db.schema import init_db
from src.db.conn import get_conn
from src.services.masking import mask_customer_row
from src.config import MASK_SALT

search_bp = Blueprint("search", __name__)

@search_bp.get("/search")
def search():
    init_db()

    city = request.args.get("city")
    status = request.args.get("status")
    name = request.args.get("name")

    mask = request.args.get("mask", "false").lower() in ("1", "true", "yes", "y")
    mask_salt = MASK_SALT  # ✅ fixed: was os.genenv (typo) in your file

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

    if mask:
        rows = [mask_customer_row(r, salt=mask_salt) for r in rows]

    return jsonify({
        "filters": {"city": city, "status": status, "name": name},
        "masked": mask,
        "query_time_ms": round((t1 - t0) * 1000, 3),
        "results": rows
    })