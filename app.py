import os
from flask import Flask, redirect, url_for, flash, request
from flask_jwt_extended import JWTManager
from config.database import init_db, db
from controller.auth_controller import auth_bp
from controller.course_controller import course_bp
from controller.quiz_controller import quiz_bp
from controller.admin_controller import admin_bp
from controller.certificate_controller import certificate_bp

# Import models for db.create_all()
import models.user
import models.course
import models.quiz
import models.progress
import models.review
import models.certificate
import models.audit_log

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['JWT_SECRET_KEY'] = 'dev-jwt-secret-key-32-characters-long-minimum-secure'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    init_db(app)
    jwt = JWTManager(app)

    # Handle missing JWT tokens gracefully for web browsers
    @jwt.unauthorized_loader
    def missing_token_callback(err_string):
        if request.is_json or request.path.startswith("/api"):
            return {"message": "Authorization token missing"}, 401
        flash("Please log in first to access this page.", "warning")
        return redirect(url_for('auth.web_login'))

    # Handle expired or invalid JWT tokens
    @jwt.invalid_token_loader
    def invalid_token_callback(err_string):
        if request.is_json or request.path.startswith("/api"):
            return {"message": "Invalid token"}, 401
        flash("Session expired or invalid token. Please log in again.", "warning")
        return redirect(url_for('auth.web_login'))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(certificate_bp)

    @app.route("/health", methods=['GET'])
    def health():
        try:
            return "Healthy", 200
        except Exception:
            return "Unhealthy", 500

    @app.route('/')
    def index():
        return redirect(url_for('auth.web_login'))

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)