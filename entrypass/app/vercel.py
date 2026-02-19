"""
Vercel Serverless Handler
==========================

This module adapts the Flask application for Vercel's serverless environment.

Responsibilities:
- Set up sys.path so bare imports inside app.py work correctly
- Import the Flask app from app.py
- Expose the WSGI application as ``app`` for @vercel/python

Important Notes:
- Vercel uses ephemeral filesystem – JSON data resets on cold starts
- Cold starts may affect initial response times
- All routes are handled through this single serverless function
- vercel.json points to this file as the handler
"""

import sys
import os
import traceback

# ---------------------------------------------------------------------------
# PATH SETUP – Vercel's Python runtime puts the *project root* on sys.path.
# The Flask app (app.py) uses bare imports such as
#     from routes.auth import auth_bp
#     from utils.json_store import ...
# These resolve only when the ``app/`` directory itself is on sys.path.
# ---------------------------------------------------------------------------
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    # ``app.py`` is in the same directory; this import gets the Flask instance
    from app import app

    # Vercel @vercel/python runtime looks for a variable named ``app``
    # (WSGI callable).  We also expose ``application`` and ``handler``
    # for compatibility.
    application = app
    handler = app

except Exception as e:
    # Fallback: surface the import error so it's easy to debug on Vercel
    from flask import Flask

    _err_app = Flask(__name__)

    @_err_app.route("/", defaults={"path": ""})
    @_err_app.route("/<path:path>")
    def _error(path):
        return {
            "error": "Application failed to import",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "python_path": sys.path,
        }, 500

    app = _err_app
    application = _err_app
    handler = _err_app
