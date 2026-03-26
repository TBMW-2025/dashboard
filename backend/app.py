import os
import sys

# Add backend directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually


from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from models import db
from routes.auth import auth_bp
from routes.students import students_bp
from routes.companies import companies_bp
from routes.placements import placements_bp
from routes.internships import internships_bp
from routes.reports import reports_bp
from routes.export import export_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..')  # dashboard-1/

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# ─── Configuration ────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = 'placement-dashboard-secret-key-2026-rru'
app.config['JWT_SECRET_KEY'] = 'jwt-placement-dashboard-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'placement.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # No expiry for dev; set timedelta in prod

# ─── Extensions ───────────────────────────────────────────────────────────────
db.init_app(app)
jwt = JWTManager(app)
CORS(app, origins=['http://127.0.0.1:5001', 'http://localhost:5001',
                   'null', 'file://'])

# ─── API Blueprints ───────────────────────────────────────────────────────────
app.register_blueprint(auth_bp,        url_prefix='/api/auth')
app.register_blueprint(students_bp,    url_prefix='/api/students')
app.register_blueprint(companies_bp,   url_prefix='/api/companies')
app.register_blueprint(placements_bp,  url_prefix='/api/placements')
app.register_blueprint(internships_bp, url_prefix='/api/internships')
app.register_blueprint(reports_bp,     url_prefix='/api/reports')
app.register_blueprint(export_bp,      url_prefix='/api/export')


# ─── Frontend Static Serving ──────────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(full_path):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({'error': 'Not found'}), 404


# ─── Error Handlers ───────────────────────────────────────────────────────────
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'code': 'invalid_token'}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'No token provided', 'code': 'authorization_required'}), 401


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ─── DB Init ──────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Placement Dashboard API")
    print("  Running at: http://127.0.0.1:5001")
    print("  Open:        http://127.0.0.1:5001  (login page)")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5001)
