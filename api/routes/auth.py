#!/usr/bin/env python3
"""Authentication Routes for Enterprise RAG Workspace.

Handles JWT-based authentication: login, registration, and token management.
All routes return JSON responses and include proper error handling.
"""

from flask import Blueprint, request, jsonify
from api.app import db, jwt
from api.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and issue JWT access/refresh tokens.

    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "secret123"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        # Generic error to avoid email enumeration
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "Account disabled"}), 403

    # Create JWT tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }
    ), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Expected JSON payload:
    {
        "email": "newuser@example.com",
        "password": "securepassword",
        "full_name": "Optional Full Name"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    password_hash = generate_password_hash(password)

    # Create user (default: regular user, not admin)
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name if full_name else None,
        is_admin=False,
        is_active=True,
    )

    db.session.add(user)
    db.session.commit()

    # Issue tokens upon registration
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }
    ), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return current user info from JWT identity."""
    user_id = get_jwt_identity()
    from api.models import User
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    user_id = get_jwt_identity()
    from api.app import create_access_token
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token}), 200