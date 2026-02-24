from flask import Blueprint, jsonify
from src.db.schema import init_db, create_indexes

index_bp = Blueprint("index", __name__)

@index_bp.post("/index")
def index():
    init_db()
    create_indexes()
    return jsonify({"ok": True, "message": "Indexes created (city, status)."})