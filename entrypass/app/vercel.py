"""
Vercel Serverless Handler
==========================

This module adapts the Flask application for Vercel's serverless environment.

Responsibilities:
- Import the Flask app from app.py
- Expose the app as a WSGI-compatible handler for Vercel
- Handle serverless function invocation
- Provide error handling for debugging

Important Notes:
- Vercel uses ephemeral filesystem - JSON data resets on each deploy
- Cold starts may affect initial response times
- All routes are handled through this single serverless function

Usage:
- vercel.json points to this file as the handler
- No modifications needed for deployment
"""

import sys
import traceback

try:
    from app import app
    
    # Expose app for Vercel's WSGI handler
    # Vercel will import this as the application handler
    application = app
    
    # For Vercel serverless functions
    handler = app
    
    # Add a test route for debugging
    @app.route('/test')
    def test():
        return {"status": "ok", "message": "Vercel handler working"}
        
except Exception as e:
    # Create a simple error app if main app fails
    from flask import Flask
    
    error_app = Flask(__name__)
    
    @error_app.route('/')
    def error():
        return {
            "error": "Application failed to import",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "python_path": sys.path
        }
    
    application = error_app
    handler = error_app
