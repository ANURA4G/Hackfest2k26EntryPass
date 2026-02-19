"""
Flask Application Entry Point
==============================

This is the main Flask application file.
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
    """Landing page route."""
    return render_template('landing.html')


@app.route('/health')
def health_check():
    """Health check endpoint for deployment verification."""
    import sys
    import os
    return {
        "status": "OK",
        "message": "Event Ticketing App is running",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment": "production" if os.getenv('FLASK_ENV') == 'production' else "development"
    }


@app.route('/admin')
def admin_shortcut():
    """Direct admin access route - requires login."""
    from flask import redirect, url_for, session
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))


if __name__ == "__main__":
    # Development server entry point
    app.run(debug=True)
    app.run(debug=True)
