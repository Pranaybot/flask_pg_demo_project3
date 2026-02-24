from typing import Any, Dict
from psycopg2.extras import RealDictCursor
from src.db.conn import get_conn

def run_dataset_quality_checks() -> Dict[str, Any]:
    report = {
        "row_count": 0,
        "status_distribution": {},
        "top_city": None,
        "warnings": [],
        "passed": True
    }

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM customers;")
            report["row_count"] = cur.fetchone()["cnt"]

            if report["row_count"] == 0:
                report["warnings"].append("Table is empty.")
                report["passed"] = False
                return report

            cur.execute("""
                SELECT status, COUNT(*) AS c
                FROM customers
                GROUP BY status;
            """)
            status_rows = cur.fetchall()

            total = report["row_count"]
            for r in status_rows:
                pct = round((r["c"] / total) * 100, 2)
                report["status_distribution"][r["status"]] = pct
                if pct > 95:
                    report["warnings"].append(
                        f"Status '{r['status']}' dominates dataset ({pct}%). Possible pipeline issue."
                    )

            cur.execute("""
                SELECT city, COUNT(*) AS c
                FROM customers
                GROUP BY city
                ORDER BY c DESC
                LIMIT 1;
            """)
            top_city = cur.fetchone()

            city_pct = round((top_city["c"] / total) * 100, 2)
            report["top_city"] = {"city": top_city["city"], "percentage": city_pct}

            if city_pct > 80:
                report["warnings"].append(
                    f"City '{top_city['city']}' holds {city_pct}% of records."
                )

    if report["warnings"]:
        report["passed"] = False

    return report