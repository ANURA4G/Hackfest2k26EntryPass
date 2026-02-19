"""
QR Scan Routes
===============

This module handles QR code scanning and ticket verification.

Features:
- Display QR scanner interface
- Verify scanned QR payloads
- Check signature integrity
- Mark attendance
- Prevent duplicate entries
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session

from utils.qr import decode_qr_payload
from utils.json_store import (
    get_ticket_by_id, mark_attendance, is_ticket_used,
    get_attendance_by_ticket, mark_team_attendance_record
)

scan_bp = Blueprint('scan', __name__, url_prefix='/scan')


@scan_bp.route('/')
def index():
    """Display QR scanner page."""
    return render_template('scan.html')


@scan_bp.route('/camera')
def camera():
    """Camera-based QR scanner page."""
    return render_template('scan.html')


@scan_bp.route('/verify', methods=['POST'])
def verify():
    """
    API endpoint to verify a scanned QR payload.
    
    Accepts JSON with 'qr_data' containing the encrypted payload.
    
    Returns:
        JSON response with:
        - success: Boolean
        - status: VALID, USED, or INVALID
        - message: Human readable message
        - ticket: Ticket details (if valid)
    """
    data = request.get_json() or {}
    qr_data = data.get('qr_data', '').strip()
    
    if not qr_data:
        return jsonify({
            'success': False,
            'status': 'INVALID',
            'message': 'No QR data provided'
        })
    
    # Step 1: Decode and verify the QR payload
    decode_result = decode_qr_payload(qr_data)
    
    if not decode_result.get('valid'):
        return jsonify({
            'success': False,
            'status': 'INVALID',
            'message': decode_result.get('error', 'Invalid QR code')
        })
    
    # Extract ticket data from decoded payload
    payload_data = decode_result.get('data', {})
    ticket_id = payload_data.get('ticket_id')
    user_id = payload_data.get('user_id')
    team_name = payload_data.get('team_name')
    
    if not ticket_id:
        return jsonify({
            'success': False,
            'status': 'INVALID',
            'message': 'Invalid ticket data in QR code'
        })
    
    # Step 2: Verify ticket exists in database
    ticket = get_ticket_by_id(ticket_id)
    
    if not ticket:
        return jsonify({
            'success': False,
            'status': 'INVALID',
            'message': f'Ticket {ticket_id} not found in system'
        })
    
    # Step 3: Verify user_id matches (additional security)
    if ticket.get('user_id') != user_id:
        return jsonify({
            'success': False,
            'status': 'INVALID',
            'message': 'Ticket data mismatch - possible tampering'
        })
    
# Step 4: Check if team already checked in
    if is_ticket_used(ticket_id):
        existing = get_attendance_by_ticket(ticket_id)
        return jsonify({
            'success': False,
            'status': 'USED',
            'message': 'Team already checked in',
            'scanned_at': existing.get('timestamp'),
            'ticket': {
                'ticket_id': ticket_id,
                'team_name': ticket.get('team_name'),
                'user_id': user_id,
                'team_members': ticket.get('team_members', [])
            },
            'attendance_details': existing.get('member_attendance', [])
        })

    # Step 5: Show team member selection for attendance
    return jsonify({
        'success': True,
        'status': 'TEAM_ATTENDANCE',
        'message': 'Select team members present',
        'ticket': {
            'ticket_id': ticket_id,
            'team_name': ticket.get('team_name'),
            'user_id': user_id,
            'slot': ticket.get('slot'),
            'event_name': ticket.get('event_name'),
            'team_members': ticket.get('team_members', []),
            'team_size': ticket.get('team_size', 3)
        }
    })


@scan_bp.route('/team-attendance', methods=['POST'])
def mark_team_attendance():
    """
    Mark attendance for selected team members.
    
    Expects JSON with:
    - ticket_id: Team ticket ID
    - present_members: List of member IDs that are present
    """
    data = request.get_json() or {}
    ticket_id = data.get('ticket_id', '').strip()
    present_member_ids = data.get('present_members', [])
    
    if not ticket_id:
        return jsonify({
            'success': False,
            'message': 'Ticket ID is required'
        })
    
    # Verify ticket exists
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({
            'success': False,
            'message': 'Ticket not found'
        })
    
    # Check if already processed
    if is_ticket_used(ticket_id):
        return jsonify({
            'success': False,
            'status': 'USED',
            'message': 'Team attendance already recorded'
        })
    
    # Get team members
    team_members = ticket.get('team_members', [])
    if not team_members:
        return jsonify({
            'success': False,
            'message': 'No team members found for this ticket'
        })
    
    # Build member attendance records
    member_attendance = []
    present_count = 0
    
    for member in team_members:
        member_id = member.get('member_id')
        is_present = str(member_id) in [str(mid) for mid in present_member_ids]
        
        member_attendance.append({
            'member_id': member_id,
            'name': member.get('name'),
            'position': member.get('position'),
            'status': 'present' if is_present else 'absent'
        })
        
        if is_present:
            present_count += 1
    
    # Mark team attendance
    scanned_by = session.get('username', 'scanner')
    result = mark_team_attendance_record(ticket_id, member_attendance, scanned_by)
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'status': 'VALID',
            'message': f'✅ Team Attendance Recorded - {present_count} members present',
            'ticket': {
                'ticket_id': ticket_id,
                'team_name': ticket.get('team_name'),
                'user_id': ticket.get('user_id'),
                'slot': ticket.get('slot'),
                'event_name': ticket.get('event_name')
            },
            'attendance_summary': {
                'total_members': len(team_members),
                'present_count': present_count,
                'member_details': member_attendance
            },
            'timestamp': result.get('timestamp')
        })
    else:
        return jsonify({
            'success': False,
            'status': 'ERROR',
            'message': result.get('message', 'Failed to record attendance')
        })


@scan_bp.route('/manual', methods=['GET', 'POST'])
def manual():
    """
    Manual ticket ID verification.
    
    For cases where QR scanner doesn't work.
    """
    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id', '').strip().upper()
        
        if not ticket_id:
            flash('Please enter a ticket ID', 'error')
            return redirect(url_for('scan.manual'))
        
        # Check if ticket exists
        ticket = get_ticket_by_id(ticket_id)
        
        if not ticket:
            flash(f'Ticket {ticket_id} not found', 'error')
            return render_template('scan_result.html', result={
                'success': False,
                'status': 'INVALID',
                'message': f'Ticket {ticket_id} not found in system',
                'ticket_id': ticket_id
            })
        
        # Check if already used
        if is_ticket_used(ticket_id):
            existing = get_attendance_by_ticket(ticket_id)
            return render_template('scan_result.html', result={
                'success': False,
                'status': 'USED',
                'message': 'Ticket already used for entry',
                'ticket': ticket,
                'scanned_at': existing.get('timestamp')
            })
        
        # Check if team has members for individual attendance
        team_members = ticket.get('team_members', [])
        if len(team_members) > 1:
            return render_template('scan_result.html', result={
                'success': True,
                'status': 'TEAM_ATTENDANCE',
                'message': 'Select team members for attendance',
                'ticket': ticket,
                'team_members': team_members
            })
        
        # Mark attendance for single person team
        scanned_by = session.get('username', 'manual')
        result = mark_attendance(ticket_id, scanned_by)
        
        if result.get('success'):
            flash(f'✅ Entry allowed for {ticket.get("team_name")}', 'success')
            return render_template('scan_result.html', result={
                'success': True,
                'status': 'VALID',
                'message': 'Entry Allowed',
                'ticket': ticket,
                'timestamp': result.get('timestamp')
            })
        else:
            return render_template('scan_result.html', result=result)
    
    # GET - show manual entry form
    return render_template('scan.html')


@scan_bp.route('/result')
def result_page():
    """Display a scan result page."""
    return render_template('scan.html')


@scan_bp.route('/result/<ticket_id>')
def result(ticket_id):
    """Display scan result for a specific ticket."""
    ticket = get_ticket_by_id(ticket_id)
    attendance = get_attendance_by_ticket(ticket_id)
    
    if not ticket:
        result = {
            'success': False,
            'status': 'INVALID',
            'message': 'Ticket not found',
            'ticket_id': ticket_id
        }
    elif attendance:
        result = {
            'success': True,
            'status': 'CHECKED_IN',
            'message': 'Already checked in',
            'ticket': ticket,
            'scanned_at': attendance.get('timestamp')
        }
    else:
        result = {
            'success': True,
            'status': 'VALID',
            'message': 'Ticket is valid',
            'ticket': ticket
        }
    
    return render_template('scan_result.html', result=result)


# ============================================================
# API ENDPOINTS (for JavaScript scanner)
# ============================================================

@scan_bp.route('/api/check/<ticket_id>')
def api_check(ticket_id):
    """API to check ticket status without marking attendance."""
    ticket = get_ticket_by_id(ticket_id)
    
    if not ticket:
        return jsonify({
            'exists': False,
            'message': 'Ticket not found'
        })
    
    used = is_ticket_used(ticket_id)
    
    return jsonify({
        'exists': True,
        'used': used,
        'ticket': {
            'ticket_id': ticket_id,
            'team_name': ticket.get('team_name'),
            'user_id': ticket.get('user_id'),
            'slot': ticket.get('slot')
        }
    })


@scan_bp.route('/api/ticket-details/<ticket_id>')
def api_ticket_details(ticket_id):
    """
    API endpoint to get full ticket details including team members and attendance status.
    Used by the manual entry flow to decide whether to show team member selection.
    """
    ticket_id = ticket_id.strip().upper()
    ticket = get_ticket_by_id(ticket_id)
    
    if not ticket:
        return jsonify({
            'success': False,
            'message': f'Ticket "{ticket_id}" not found'
        })
    
    used = is_ticket_used(ticket_id)
    attendance = get_attendance_by_ticket(ticket_id) if used else None
    
    return jsonify({
        'success': True,
        'used': used,
        'ticket': {
            'ticket_id': ticket_id,
            'team_name': ticket.get('team_name'),
            'user_id': ticket.get('user_id'),
            'slot': ticket.get('slot'),
            'event_name': ticket.get('event_name'),
            'team_size': ticket.get('team_size', 1),
            'team_members': ticket.get('team_members', [])
        },
        'scanned_at': attendance.get('timestamp') if attendance else None,
        'attendance_details': attendance.get('member_attendance', []) if attendance else []
    })


@scan_bp.route('/api/mark-attendance', methods=['POST'])
def api_mark_attendance():
    """
    API endpoint to mark simple attendance (no team member selection).
    Used for teams with no individual member tracking.
    """
    data = request.get_json() or {}
    ticket_id = data.get('ticket_id', '').strip().upper()
    
    if not ticket_id:
        return jsonify({ 'success': False, 'status': 'INVALID', 'message': 'No ticket ID provided' })
    
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({ 'success': False, 'status': 'INVALID', 'message': 'Ticket not found' })
    
    if is_ticket_used(ticket_id):
        return jsonify({ 'success': False, 'status': 'USED', 'message': 'Already checked in' })
    
    scanned_by = session.get('username', 'manual')
    result = mark_attendance(ticket_id, scanned_by)
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'status': 'VALID',
            'message': 'Attendance recorded',
            'ticket': {
                'ticket_id': ticket_id,
                'team_name': ticket.get('team_name'),
                'user_id': ticket.get('user_id')
            },
            'timestamp': result.get('timestamp')
        })
    
    return jsonify({ 'success': False, 'status': 'ERROR', 'message': result.get('message', 'Failed') })
