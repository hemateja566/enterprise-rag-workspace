#!/usr/bin/env python3
"""Main Flask Application Enterprise RAG Workspace.

This module initializes the Flask application, configures extensions,
registers blueprints, and provides the API entry point.
"""

import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize extensions (lazy - configured later)
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_path=None):
    """Application factory pattern.

    Args:
        config_path: Path to configuration object or file. If None,
                     default config is loaded from environment variables.

    Returns:
        Flask application instance.
    """
    app = Flask(__name__)

    # --- Configuration ---
    # Security & Auth
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

    # Database (MySQL)
    mysql_uri = os.getenv(
        "MYSQL_URI",
        "mysql+pymysql://root@localhost:3306/enterprise_rag"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS - configure for production origins later
    CORS(app, supports_credentials=True)

    # JWT Initialization
    jwt.init_app(app)

    # --- Database Initialization ---
    db.init_app(app)

    # Create database tables within app context
    with app.app_context():
        db.create_all()

    # --- Blueprints Registration ---
    # Auth blueprint (login, register, token refresh)
    from api.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # Documents blueprint (upload, metadata, delete)
    from api.routes.documents import documents_bp
    app.register_blueprint(documents_bp, url_prefix="/api/documents")

    # Queries blueprint (submission, SSE streaming, status)
    from api.routes.queries import queries_bp
    app.register_blueprint(queries_bp, url_prefix="/api/queries")

    # Health check route
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "enterprise-rag-api"})

    app.logger.info("Enterprise RAG API initialized successfully")
    return app


# Allow running directly: python app.py
if __name__ == "__main__":
    app = create_app()
    # Debug mode should be disabled in production
    app.run(host="0.0.0.0", port=int(os.getenv("API_PORT", "5000")), debug=bool(os.getenv("FLASK_DEBUG", False)))