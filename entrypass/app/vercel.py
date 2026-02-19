"""
Vercel Serverless Handler
==========================
Simplified handler for Vercel serverless deployment.
"""

# For Vercel, we want a minimal reliable handler
from app import app

# Export the Flask app for Vercel
application = app
