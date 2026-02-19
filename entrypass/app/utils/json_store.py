"""
JSON Store Utilities
=====================

This module handles all JSON file read/write operations.

Data Files Managed:
- users.json: User accounts (both admin and regular users)
- tickets.json: All generated tickets with event info
- attendance.json: Check-in records with timestamps
"""

import os
import json
from datetime import datetime

# Path to data directory - improved for serverless
# Try multiple path resolution strategies
script_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(script_dir)
DATA_DIR = os.path.join(app_dir, 'data')

# Fallback for serverless environments
if not os.path.exists(DATA_DIR):
    # Try alternative paths
    alt_data_dir = os.path.join(os.getcwd(), 'app', 'data')
    if os.path.exists(alt_data_dir):
        DATA_DIR = alt_data_dir
    else:
        # Create data directory if it doesn't exist
        DATA_DIR = os.path.join(app_dir, 'data')
        os.makedirs(DATA_DIR, exist_ok=True)

# Data file names
USERS_FILE = 'users.json'
TICKETS_FILE = 'tickets.json'
ATTENDANCE_FILE = 'attendance.json'


def load_json(filename: str) -> dict:
    """Read a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        # Return default structure based on filename
        if filename == USERS_FILE:
            return {"users": []}
        elif filename == TICKETS_FILE:
            return {"tickets": []}
        elif filename == ATTENDANCE_FILE:
            return {"attendance": []}
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure data has proper structure
            if filename == USERS_FILE and 'users' not in data:
                data['users'] = []
            elif filename == TICKETS_FILE and 'tickets' not in data:
                data['tickets'] = []
            elif filename == ATTENDANCE_FILE and 'attendance' not in data:
                data['attendance'] = []
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {filename}: {e}")
        # Return proper default structure
        if filename == USERS_FILE:
            return {"users": []}
        elif filename == TICKETS_FILE:
            return {"tickets": []}
        elif filename == ATTENDANCE_FILE:
            return {"attendance": []}
        return {}


def save_json(filename: str, data: dict) -> bool:
    """Write data to a JSON file."""
    filepath = os.path.join(DATA_DIR, filename)
    
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError:
        return False


def get_all_users() -> list:
    """Get all users from users.json."""
    data = load_json(USERS_FILE)
    return data.get('users', [])


def get_all_tickets() -> list:
    """Get all tickets from tickets.json."""
    data = load_json(TICKETS_FILE)
    return data.get('tickets', [])


def get_attendance_records() -> list:
    """Get all attendance records."""
    data = load_json(ATTENDANCE_FILE)
    # Use 'records' as the primary field, fallback to 'attendance' for compatibility
    return data.get('records', data.get('attendance', []))


# ============================================================
# USER OPERATIONS
# ============================================================

def add_user(user_data: dict) -> bool:
    """
    Add a new user to users.json.
    
    Args:
        user_data: Dictionary with user info (id, username, password_hash, role, etc.)
    
    Returns:
        True if successful
    """
    data = load_json(USERS_FILE)
    users = data.get('users', [])
    users.append(user_data)
    data['users'] = users
    return save_json(USERS_FILE, data)


def get_user_by_id(user_id: str) -> dict:
    """Find a user by their ID."""
    users = get_all_users()
    for user in users:
        if user.get('id') == user_id:
            return user
    return {}


def get_user_by_username(username: str) -> dict:
    """Find a user by username."""
    users = get_all_users()
    for user in users:
        if user.get('username') == username:
            return user
    return {}


# ============================================================
# TICKET OPERATIONS
# ============================================================

def add_ticket(ticket_data: dict) -> bool:
    """
    Add a new ticket to tickets.json.
    
    Args:
        ticket_data: Dictionary with ticket info
    
    Returns:
        True if successful
    """
    data = load_json(TICKETS_FILE)
    tickets = data.get('tickets', [])
    tickets.append(ticket_data)
    data['tickets'] = tickets
    return save_json(TICKETS_FILE, data)


def get_ticket_by_id(ticket_id: str) -> dict:
    """Find a ticket by its ID."""
    tickets = get_all_tickets()
    for ticket in tickets:
        if ticket.get('ticket_id') == ticket_id:
            return ticket
    return {}


def update_ticket(ticket_id: str, updates: dict) -> bool:
    """Update a ticket's data."""
    data = load_json(TICKETS_FILE)
    tickets = data.get('tickets', [])
    
    for i, ticket in enumerate(tickets):
        if ticket.get('ticket_id') == ticket_id:
            tickets[i].update(updates)
            data['tickets'] = tickets
            return save_json(TICKETS_FILE, data)
    return False


def delete_ticket(ticket_id: str) -> bool:
    """
    Delete a ticket and its associated user.
    
    Args:
        ticket_id: Ticket ID to delete
    
    Returns:
        True if successful
    """
    # Get ticket to find user_id
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return False
    
    user_id = ticket.get('user_id')
    
    # Delete ticket
    data = load_json(TICKETS_FILE)
    tickets = data.get('tickets', [])
    tickets = [t for t in tickets if t.get('ticket_id') != ticket_id]
    data['tickets'] = tickets
    save_json(TICKETS_FILE, data)
    
    # Delete associated user
    if user_id:
        user_data = load_json(USERS_FILE)
        users = user_data.get('users', [])
        users = [u for u in users if u.get('id') != user_id]
        user_data['users'] = users
        save_json(USERS_FILE, user_data)
    
    # Delete attendance record if exists
    attendance_data = load_json(ATTENDANCE_FILE)
    records = attendance_data.get('records', [])
    records = [r for r in records if r.get('ticket_id') != ticket_id]
    attendance_data['records'] = records
    save_json(ATTENDANCE_FILE, attendance_data)
    
    return True



# ============================================================
# ATTENDANCE OPERATIONS
# ============================================================

def add_attendance_record(record: dict) -> bool:
    """
    Add an attendance record.
    
    Args:
        record: Dictionary with ticket_id, timestamp, status
    
    Returns:
        True if successful
    """
    data = load_json(ATTENDANCE_FILE)
    records = data.get('records', [])
    records.append(record)
    data['records'] = records
    return save_json(ATTENDANCE_FILE, data)


def get_attendance_by_ticket(ticket_id: str) -> dict:
    """Get attendance record for a specific ticket."""
    records = get_attendance_records()
    for record in records:
        if record.get('ticket_id') == ticket_id:
            return record
    return {}


def is_ticket_used(ticket_id: str) -> bool:
    """Check if a ticket has already been used for entry."""
    record = get_attendance_by_ticket(ticket_id)
    return record.get('status') == 'present'


def mark_team_attendance_record(ticket_id: str, member_attendance: list, scanned_by: str = 'admin') -> dict:
    """
    Mark attendance for a team with individual member tracking.
    
    Args:
        ticket_id: Ticket ID
        member_attendance: List of member attendance records
        scanned_by: Who scanned the ticket
    
    Returns:
        Result dictionary with success status and message
    """
    # Check if ticket exists
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return {'success': False, 'message': 'Ticket not found', 'status': 'INVALID'}
    
    # Check if already used
    if is_ticket_used(ticket_id):
        existing = get_attendance_by_ticket(ticket_id)
        return {
            'success': False, 
            'message': 'Team attendance already recorded',
            'status': 'USED',
            'scanned_at': existing.get('timestamp')
        }
    
    # Create team attendance record
    timestamp = datetime.now().isoformat()
    record = {
        'ticket_id': ticket_id,
        'user_id': ticket.get('user_id'),
        'team_name': ticket.get('team_name'),
        'timestamp': timestamp,
        'status': 'present',
        'scanned_by': scanned_by,
        'member_attendance': member_attendance,
        'team_size': ticket.get('team_size', len(member_attendance)),
        'present_count': len([m for m in member_attendance if m.get('status') == 'present'])
    }
    
    add_attendance_record(record)
    
    return {
        'success': True,
        'message': 'Team attendance recorded',
        'status': 'VALID',
        'ticket': ticket,
        'timestamp': timestamp,
        'attendance_details': member_attendance
    }


def mark_attendance(ticket_id: str, scanned_by: str = 'admin') -> dict:
    """
    Mark attendance for a ticket.
    
    Args:
        ticket_id: Ticket to mark as attended
        scanned_by: Who scanned the ticket
    
    Returns:
        Result dictionary with success status and message
    """
    # Check if ticket exists
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return {'success': False, 'message': 'Ticket not found', 'status': 'INVALID'}
    
    # Check if already used
    if is_ticket_used(ticket_id):
        existing = get_attendance_by_ticket(ticket_id)
        return {
            'success': False, 
            'message': 'Ticket already used',
            'status': 'USED',
            'scanned_at': existing.get('timestamp')
        }
    
    # Mark as present
    record = {
        'ticket_id': ticket_id,
        'user_id': ticket.get('user_id'),
        'team_name': ticket.get('team_name'),
        'timestamp': datetime.now().isoformat(),
        'status': 'present',
        'scanned_by': scanned_by
    }
    
    add_attendance_record(record)
    
    return {
        'success': True,
        'message': 'Entry allowed',
        'status': 'VALID',
        'ticket': ticket,
        'timestamp': record['timestamp']
    }


# ============================================================
# STATISTICS
# ============================================================

def get_stats() -> dict:
    """Get dashboard statistics."""
    tickets = get_all_tickets()
    records = get_attendance_records()
    users = get_all_users()
    
    checked_in = len([r for r in records if r.get('status') == 'present'])
    
    return {
        'total_tickets': len(tickets),
        'checked_in': checked_in,
        'pending': len(tickets) - checked_in,
        'total_users': len(users)
    }
