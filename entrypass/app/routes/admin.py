"""
Admin Routes
=============

This module handles all admin-related routes and functionality.

Features:
- Admin dashboard with statistics
- Create team/ticket with on-demand QR and PDF generation
- View all registrations
- Attendance records
"""

import uuid
import random
import string
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file

from utils.json_store import (
    add_ticket, get_all_tickets, get_all_users,
    get_attendance_records, get_stats, get_ticket_by_id, delete_ticket
)
from utils.qr import generate_qr_payload, generate_qr_image_bytes, generate_qr_image_tempfile
from utils.pdf import generate_ticket_pdf

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ============================================================
# ADMIN AUTH CHECK
# ============================================================

@admin_bp.before_request
def require_admin():
    """Require admin login for all admin routes."""
    if session.get('role') != 'admin':
        flash('Please login to access admin panel', 'error')
        return redirect(url_for('auth.login'))


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_user_id() -> str:
    """Generate a unique user ID like HF26XXXXXX."""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"HF26{random_part}"


def generate_ticket_id() -> str:
    """Generate a unique ticket UUID."""
    return str(uuid.uuid4())[:8].upper()


# ============================================================
# ROUTES
# ============================================================

@admin_bp.route('/')
def index():
    """Admin index - redirect to dashboard."""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with statistics and overview."""
    stats = get_stats()
    return render_template('dashboard_admin.html', stats=stats)


@admin_bp.route('/tickets')
def tickets():
    """View all tickets/registrations."""
    all_tickets = get_all_tickets()
    attendance = get_attendance_records()
    
    # Create a lookup for attendance status
    attendance_map = {r.get('ticket_id'): r for r in attendance}
    
    # Enrich tickets with attendance status
    for ticket in all_tickets:
        ticket_id = ticket.get('ticket_id')
        if ticket_id in attendance_map:
            ticket['attendance_status'] = 'Present'
            ticket['scanned_at'] = attendance_map[ticket_id].get('timestamp')
        else:
            ticket['attendance_status'] = 'Not Checked In'
    
    return render_template('tickets_list.html', tickets=all_tickets)


@admin_bp.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    """
    Create a new team/ticket entry.
    
    POST creates:
    - New ticket with unique ID
    - QR payload (stored in database, not as file)
    - No PDF or QR files stored (generated on-demand)
    """
    if request.method == 'POST':
        # Get form data
        team_name = request.form.get('team_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        team_leader_email = request.form.get('team_leader_email', '').strip()
        team_code = request.form.get('team_code', '').strip()
        team_size = request.form.get('team_size', '3').strip()
        slot = request.form.get('slot', '20 Feb 9:00 AM - 21 Feb 9:00 AM').strip()
        event_name = request.form.get('event_name', 'HACKFEST2K26').strip()
        
        # Get team member names
        team_members = []
        for i in range(1, int(team_size) + 1):
            member_name = request.form.get(f'member_{i}_name', '').strip()
            if member_name:
                team_members.append({
                    'name': member_name,
                    'position': 'Team Leader' if i == 1 else f'Member {i}',
                    'member_id': i
                })
        
        # Validation
        if not team_name:
            flash('Team name is required', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        if not college_name:
            flash('College name is required', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        if not team_leader_email:
            flash('Team leader email is required', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        if not team_code:
            flash('Team code is required', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        if len(team_members) != int(team_size):
            flash('All team member names are required', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        # Validate team code length
        if len(team_code) > 15:
            flash('Team code must be 15 characters or less', 'error')
            return redirect(url_for('admin.create_ticket'))
        
        # Check if team code already exists
        all_tickets = get_all_tickets()
        for ticket in all_tickets:
            if ticket.get('user_id') == team_code.upper():
                flash('Team code already exists. Please choose a different one.', 'error')
                return redirect(url_for('admin.create_ticket'))
        
        # Use provided team code
        user_id = team_code.upper()
        ticket_id = generate_ticket_id()
        
        # Generate encrypted QR payload (deterministic - same payload every time)
        qr_payload = generate_qr_payload(ticket_id, user_id, team_name)
        
        # Create ticket record (no files stored)
        ticket_data = {
            'ticket_id': ticket_id,
            'user_id': user_id,
            'team_name': team_name,
            'college_name': college_name,
            'team_leader_email': team_leader_email,
            'team_size': int(team_size),
            'team_members': team_members,
            'slot': slot,
            'event_name': event_name,
            'qr_payload': qr_payload,
            'created_at': datetime.now().isoformat(),
            'created_by': 'admin'
        }
        
        # Save ticket
        add_ticket(ticket_data)
        
        # Store result in session for display
        session['last_created_ticket'] = {
            'ticket_id': ticket_id,
            'user_id': user_id,
            'team_name': team_name,
            'college_name': college_name,
            'team_leader_email': team_leader_email,
            'team_members': team_members,
            'slot': slot
        }
        
        flash(f'Ticket created successfully for {team_name}!', 'success')
        return redirect(url_for('admin.ticket_created'))
    
    # GET - show create form
    return render_template('ticket_create.html')


@admin_bp.route('/tickets/created')
def ticket_created():
    """Show the result after creating a ticket."""
    ticket_info = session.get('last_created_ticket')
    if not ticket_info:
        return redirect(url_for('admin.tickets'))
    return render_template('ticket_created.html', ticket=ticket_info)


@admin_bp.route('/tickets/<ticket_id>')
def ticket_detail(ticket_id):
    """View details of a specific ticket."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('admin.tickets'))
    
    ticket['qr_url'] = url_for('admin.download_qr', ticket_id=ticket_id)
    ticket['pdf_url'] = url_for('admin.download_pdf', ticket_id=ticket_id)
    
    return render_template('ticket_detail.html', ticket=ticket)


@admin_bp.route('/tickets/<ticket_id>/qr')
def download_qr(ticket_id):
    """Download QR code image for a ticket (generated in memory, not stored)."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('admin.tickets'))
    
    qr_payload = ticket.get('qr_payload')
    if not qr_payload:
        flash('QR payload not found', 'error')
        return redirect(url_for('admin.tickets'))
    
    try:
        qr_buffer = generate_qr_image_bytes(qr_payload)
        return send_file(qr_buffer, mimetype='image/png',
                         as_attachment=True, download_name=f'{ticket_id}_qr.png')
    except Exception as e:
        flash(f'Failed to generate QR code: {str(e)}', 'error')
        return redirect(url_for('admin.tickets'))


@admin_bp.route('/tickets/<ticket_id>/pdf')
def download_pdf(ticket_id):
    """Download PDF for a ticket (generated in memory, not stored)."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('admin.tickets'))
    
    try:
        import os
        # Generate QR to temp file (needed for PDF embedding)
        qr_payload = ticket.get('qr_payload')
        temp_qr_path = generate_qr_image_tempfile(qr_payload)
        
        # Generate PDF in memory
        pdf_data = {
            'ticket_id': ticket_id,
            'user_id': ticket.get('user_id'),
            'team_name': ticket.get('team_name'),
            'college_name': ticket.get('college_name'),
            'team_leader_email': ticket.get('team_leader_email'),
            'team_size': ticket.get('team_size'),
            'slot': ticket.get('slot'),
            'event_name': ticket.get('event_name'),
            'qr_path': temp_qr_path
        }
        pdf_buffer = generate_ticket_pdf(pdf_data)
        
        # Clean up temp QR file
        try:
            os.unlink(temp_qr_path)
        except:
            pass
        
        return send_file(pdf_buffer, mimetype='application/pdf',
                         as_attachment=True, download_name=f'{ticket_id}_pass.pdf')
    except Exception as e:
        flash(f'Failed to generate PDF: {str(e)}', 'error')
        return redirect(url_for('admin.tickets'))


@admin_bp.route('/tickets/<ticket_id>/delete', methods=['POST'])
def delete_ticket_route(ticket_id):
    """Delete a ticket and its associated data."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('admin.tickets'))
    
    team_name = ticket.get('team_name', 'Unknown')
    
    # Delete ticket and attendance records
    if delete_ticket(ticket_id):
        flash(f'Team "{team_name}" deleted successfully', 'success')
    else:
        flash('Failed to delete ticket', 'error')
    
    return redirect(url_for('admin.tickets'))


@admin_bp.route('/tickets/clear-all', methods=['POST'])
def clear_all_teams():
    """Clear all teams and attendance records."""
    # Clear tickets
    from utils.json_store import save_json, TICKETS_FILE, ATTENDANCE_FILE
    save_json(TICKETS_FILE, {'tickets': []})
    
    # Clear attendance
    save_json(ATTENDANCE_FILE, {'records': []})
    
    flash('All teams cleared successfully', 'success')
    return redirect(url_for('admin.tickets'))



@admin_bp.route('/attendance')
def attendance():
    """View all attendance records."""
    records = get_attendance_records()
    stats = get_stats()
    return render_template('attendance.html', records=records, stats=stats)


@admin_bp.route('/users')
def users():
    """View all users."""
    all_users = get_all_users()
    # Filter out admin users for display
    team_users = [u for u in all_users if u.get('role') == 'user']
    return render_template('users_list.html', users=team_users)


# ============================================================
# API ENDPOINTS
# ============================================================

@admin_bp.route('/api/stats')
def api_stats():
    """API endpoint to get dashboard statistics."""
    stats = get_stats()
    return jsonify(stats)


@admin_bp.route('/api/tickets')
def api_tickets():
    """API endpoint to get all tickets."""
    tickets = get_all_tickets()
    return jsonify({'tickets': tickets})


@admin_bp.route('/api/create-ticket', methods=['POST'])
def api_create_ticket():
    """API endpoint to create a ticket (JSON)."""
    data = request.get_json() or {}
    
    team_name = data.get('team_name', '').strip()
    slot = data.get('slot', '').strip()
    event_name = data.get('event_name', 'HackFest 2K26').strip()
    
    if not team_name or not slot:
        return jsonify({'success': False, 'error': 'team_name and slot are required'}), 400
    
    # Generate identifiers
    user_id = generate_user_id()
    ticket_id = generate_ticket_id()
    temp_password = generate_temp_password()
    password_hash = hash_password(temp_password)
    
    # Create user
    user_data = {
        'id': user_id,
        'username': user_id.lower(),
        'password_hash': password_hash,
        'password_plain': temp_password,
        'role': 'user',
        'team_name': team_name,
        'created_at': datetime.now().isoformat(),
        'created_by': 'admin'
    }
    add_user(user_data)
    
    # Generate QR payload (stored in JSON, not as file)
    qr_payload = generate_qr_payload(ticket_id, user_id, team_name)
    
    # Create ticket
    ticket_data = {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'team_name': team_name,
        'slot': slot,
        'event_name': event_name,
        'qr_payload': qr_payload,
        'created_at': datetime.now().isoformat(),
        'created_by': 'admin'
    }
    add_ticket(ticket_data)
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'user_id': user_id,
        'temp_password': temp_password,
        'qr_url': url_for('admin.download_qr', ticket_id=ticket_id),
        'pdf_url': url_for('admin.download_pdf', ticket_id=ticket_id)
    })
