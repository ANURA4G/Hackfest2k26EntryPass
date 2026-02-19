"""
Authentication Routes
======================

This module handles authentication for Admin role only.

Routes:
- GET/POST /login - Admin login page
- GET /logout - Logout and session cleanup
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.json_store import load_json

auth_bp = Blueprint('auth', __name__)

# Admin credentials
ADMIN_USERNAME = "adminmkce"
ADMIN_PASSWORD = "hackfest-2k26"


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/login/admin', methods=['GET', 'POST'])
def login():
    """Admin login page with authentication."""
    # If already logged in, go to dashboard
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user_id'] = 'admin-001'
            session['username'] = 'admin'
            session['role'] = 'admin'
            flash('Welcome to Admin Dashboard!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('login_admin.html')


@auth_bp.route('/login/user', methods=['GET', 'POST'])
def login_user():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Check user credentials from JSON
        data = load_json('users.json')
        users = data.get('users', [])
        
        for user in users:
            if user.get('username') == username and user.get('role') == 'user':
                if user.get('password_plain') == password:
                    session['user_id'] = user.get('id')
                    session['username'] = username
                    session['role'] = 'user'
                    flash('Welcome!', 'success')
                    return redirect(url_for('user.dashboard'))
        
        flash('Invalid credentials', 'error')
        return redirect(url_for('auth.login_user'))
    
    return render_template('login_user.html')


@auth_bp.route('/logout')
def logout():
    """Handle logout for both user and admin."""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))
