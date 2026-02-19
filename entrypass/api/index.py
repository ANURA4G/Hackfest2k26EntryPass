"""
Vercel Serverless Entry Point
===============================

Standard Vercel Python handler at api/index.py.
Vercel auto-detects this and creates a serverless function.

The Flask app lives in ../app/app.py with bare imports
(e.g. ``from routes.auth import auth_bp``).  We add the
app/ directory to sys.path so those imports resolve.
"""

import sys
import os
import traceback

# ── Path setup ────────────────────────────────────────────────
# app.py uses bare imports like ``from routes.auth import auth_bp``
# so the ``app/`` directory must be on sys.path.
_app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    # Import the Flask instance from app/app.py
    # (NOT from the app package – we bypass __init__.py)
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        "flask_app", os.path.join(_app_dir, "app.py")
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    app = _mod.app          # WSGI callable – Vercel looks for this name
    application = app
    handler = app

except Exception as e:
    from flask import Flask

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _boot_error(path):
        return {
            "error": "Application failed to start",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "sys_path": sys.path,
            "app_dir": _app_dir,
        }, 500
