from .seed_routes import seed_bp
from .search_routes import search_bp
from .perf_routes import perf_bp
from .dq_routes import dq_bp
from .index_routes import index_bp
from .home_routes import home_bp  

def register_routes(app):
    app.register_blueprint(home_bp) 
    app.register_blueprint(seed_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(perf_bp)
    app.register_blueprint(dq_bp)
    app.register_blueprint(index_bp) 