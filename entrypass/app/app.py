"""
Flask Application Entry Point
==============================

This is the main Flask application file.

Responsibilities:
- Create and configure the Flask application
- Register all route blueprints (auth, admin, user, scan)
- Set up session configuration
- Define the landing page route
- Configure static files and templates paths
"""

import os
from flask import Flask, render_template

# Import blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp
from routes.scan import scan_bp

# Import security for secret key
from utils.security import SECRET_KEY

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(scan_bp)


@app.route('/')
def home():
    """Landing page route - redirect to admin login."""
    from flask import redirect, url_for
    return redirect(url_for('auth.login'))


@app.route('/health')
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Development server entry point
    app.run(debug=True)
