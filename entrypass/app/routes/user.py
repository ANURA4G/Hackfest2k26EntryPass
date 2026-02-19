"""
User Routes
============

This module handles all user-related routes and functionality.

Routes:
- GET /user - User dashboard
- GET /user/dashboard - User dashboard with ticket list
- GET /user/tickets - List all tickets for logged-in user
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

user_bp = Blueprint('user', __name__, url_prefix='/user')


def user_required(f):
    """Decorator to require user login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') not in ['user', 'admin']:
            flash('Please login to continue', 'error')
            return redirect(url_for('auth.login_user'))
        return f(*args, **kwargs)
    return decorated_function


@user_bp.route('/')
@user_required
def index():
    """User index - redirect to dashboard."""
    return redirect(url_for('user.dashboard'))


@user_bp.route('/dashboard')
@user_required
def dashboard():
    """User dashboard with ticket list."""
    return render_template('dashboard_user.html')


@user_bp.route('/tickets')
@user_required
def tickets():
    """List all tickets for logged-in user."""
    return "My Tickets - Coming Soon"


@user_bp.route('/tickets/<ticket_id>')
@user_required
def ticket_detail(ticket_id):
    """View specific ticket details."""
    return f"Ticket Details: {ticket_id}"


@user_bp.route('/tickets/<ticket_id>/qr')
@user_required
def ticket_qr(ticket_id):
    """Download QR code for ticket."""
    return f"QR Code for Ticket: {ticket_id}"


@user_bp.route('/tickets/<ticket_id>/pdf')
@user_required
def ticket_pdf(ticket_id):
    """Download PDF ticket."""
    return f"PDF Ticket: {ticket_id}"
