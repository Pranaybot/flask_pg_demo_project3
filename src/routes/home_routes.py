from flask import Blueprint, jsonify

home_bp = Blueprint("home", __name__)

@home_bp.get("/")
def home():
    """
    Root endpoint.
    Acts as a health check + API overview.
    """
    return jsonify({
        "service": "Flask PostgreSQL Demo API",
        "status": "running",
        "available_endpoints": {
            "POST /seed": "Load data from data.json",
            "POST /index": "Create database indexes",
            "GET /search": "Search customers with filters",
            "GET /perf": "Compare query performance",
            "GET /dq/analyze": "Run dataset quality checks"
        }
    })