"""
Routes Package Initialization
==============================

This module initializes the routes package containing all Flask blueprints.

Available Blueprints:
- auth_bp: Handles user and admin authentication (login/logout)
- admin_bp: Admin dashboard and ticket management
- user_bp: User dashboard and ticket viewing
- scan_bp: QR code scanning and verification endpoints

Responsibilities:
- Export all blueprints for registration in the main app
- Define common route utilities if needed
"""

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp
from routes.scan import scan_bp

__all__ = ['auth_bp', 'admin_bp', 'user_bp', 'scan_bp']
