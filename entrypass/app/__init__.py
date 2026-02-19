"""
App Package Initialization
===========================

This module initializes the Flask application package.

Responsibilities:
- Initialize the Flask app instance
- Register blueprints for routes
- Configure app settings
- Set up any required middleware

Note: All configuration values including secrets are hardcoded
in the respective modules (primarily utils/security.py).
No environment variables are used.
"""

from app.app import app

__all__ = ['app']
