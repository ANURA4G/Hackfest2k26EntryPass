"""
QR Code Generation Utilities
=============================

This module handles QR code generation for event tickets.

Security:
- Payload is encrypted before encoding in QR
- HMAC signature prevents tampering
- Contains ticket_id, user_id, timestamp, and signature
"""

import os
import json
import time
from io import BytesIO

# Try to import qrcode, use placeholder if not available
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from utils.security import encrypt_data, decrypt_data, generate_signature, verify_signature


def generate_qr_payload(ticket_id: str, user_id: str, team_name: str) -> str:
    """
    Generate an encrypted and signed QR payload.
    
    The payload contains:
    - ticket_id: Unique ticket identifier
    - user_id: User who owns the ticket
    - team_name: Team name for display
    - timestamp: When the QR was generated
    - signature: HMAC signature for verification
    
    Args:
        ticket_id: Unique ticket ID
        user_id: User ID associated with ticket
        team_name: Team name
    
    Returns:
        Encrypted payload string safe for QR encoding
    """
    # Create payload data
    payload_data = {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'team_name': team_name,
        'timestamp': int(time.time())
    }
    
    # Convert to JSON string
    payload_json = json.dumps(payload_data, separators=(',', ':'))
    
    # Generate signature
    signature = generate_signature(payload_json)
    
    # Add signature to payload
    payload_data['signature'] = signature
    
    # Convert final payload to JSON
    final_payload = json.dumps(payload_data, separators=(',', ':'))
    
    # Encrypt the payload
    encrypted = encrypt_data(final_payload)
    
    return encrypted.decode('utf-8')


def decode_qr_payload(encrypted_payload: str) -> dict:
    """
    Decode and verify a QR payload.
    
    Args:
        encrypted_payload: The encrypted payload from QR scan
    
    Returns:
        Dictionary with:
        - valid: True if payload is valid and signature matches
        - data: The decoded ticket data
        - error: Error message if invalid
    """
    try:
        # Decrypt the payload
        decrypted = decrypt_data(encrypted_payload.encode('utf-8'))
        
        # Parse JSON
        payload_data = json.loads(decrypted)
        
        # Extract signature
        signature = payload_data.pop('signature', '')
        
        # Recreate the original payload for verification
        original_json = json.dumps(payload_data, separators=(',', ':'))
        
        # Verify signature
        if not verify_signature(original_json, signature):
            return {
                'valid': False,
                'error': 'Invalid signature - payload may be tampered'
            }
        
        return {
            'valid': True,
            'data': payload_data
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Failed to decode payload: {str(e)}'
        }


def generate_qr_image_bytes(payload: str) -> BytesIO:
    """
    Generate a QR code image in memory (BytesIO).
    No files are stored on disk.
    
    Args:
        payload: The encrypted payload to encode
    
    Returns:
        BytesIO buffer containing the PNG image
    """
    buf = BytesIO()
    
    if HAS_QRCODE:
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buf, format='PNG')
    else:
        buf.write(f"QR_PAYLOAD:{payload}".encode())
    
    buf.seek(0)
    return buf


def generate_qr_image_tempfile(payload: str) -> str:
    """
    Generate a QR code to a temporary file (needed for PDF embedding).
    Caller should delete the file after use.
    
    Returns:
        Path to temporary PNG file
    """
    import tempfile
    buf = generate_qr_image_bytes(payload)
    
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp.write(buf.read())
    tmp.close()
    return tmp.name
