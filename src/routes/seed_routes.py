from flask import Blueprint, jsonify
from src.db.schema import init_db
from src.services.seeding import load_seed_rows_from_file, validate_seed_rows, seed_rows_into_db

seed_bp = Blueprint("seed", __name__)

@seed_bp.post("/seed")
def seed():
    try:
        init_db()
        rows = load_seed_rows_from_file()
        validate_seed_rows(rows)
        inserted = seed_rows_into_db(rows)
        return jsonify({"ok": True, "inserted": inserted, "source": "data.json"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400