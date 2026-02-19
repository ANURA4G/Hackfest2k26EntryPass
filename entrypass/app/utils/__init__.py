"""
Utils Package Initialization
=============================

This module initializes the utilities package.
"""

from utils.security import (
    SECRET_KEY,
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    generate_signature,
    verify_signature
)

from utils.json_store import (
    load_json,
    save_json,
    get_all_users,
    get_all_tickets,
    get_attendance_records,
    add_user,
    add_ticket,
    get_user_by_id,
    get_user_by_username,
    get_ticket_by_id,
    mark_attendance,
    get_stats
)

from utils.qr import (
    generate_qr_payload,
    generate_qr_image_bytes,
    generate_qr_image_tempfile,
    decode_qr_payload
)

from utils.pdf import (
    generate_ticket_pdf,
)

__all__ = [
    'SECRET_KEY',
    'hash_password',
    'verify_password',
    'encrypt_data',
    'decrypt_data',
    'generate_signature',
    'verify_signature',
    'load_json',
    'save_json',
    'get_all_users',
    'get_all_tickets',
    'get_attendance_records',
    'add_user',
    'add_ticket',
    'get_user_by_id',
    'get_user_by_username',
    'get_ticket_by_id',
    'mark_attendance',
    'get_stats',
    'generate_qr_payload',
    'generate_qr_image_bytes',
    'generate_qr_image_tempfile',
    'decode_qr_payload',
    'generate_ticket_pdf'
]
