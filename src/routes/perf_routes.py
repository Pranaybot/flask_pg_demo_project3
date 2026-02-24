import time
from typing import Any, Dict
from flask import Blueprint, request, jsonify

from src.db.schema import init_db
from src.db.conn import get_conn

perf_bp = Blueprint("perf", __name__)

@perf_bp.get("/perf")
def perf():
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
        "note": "Create indexes (POST /index) and filter on city/status for clearer differences."
    })