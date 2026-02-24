from flask import Blueprint, jsonify
from src.db.schema import init_db
from src.services.dq import run_dataset_quality_checks

dq_bp = Blueprint("dq", __name__)

@dq_bp.get("/dq/analyze")
def dq_analyze():
    init_db()
    try:
        report = run_dataset_quality_checks()
        return jsonify(report)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500