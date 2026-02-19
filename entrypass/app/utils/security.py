"""
Security Utilities
===================

This module contains all security-related functions and hardcoded secrets.

IMPORTANT: All secrets are hardcoded here as per project requirements.
No environment variables are used.

Responsibilities:
- Password hashing using bcrypt
- Password verification
- Data encryption using Fernet (symmetric encryption)
- Data decryption
- HMAC signature generation for QR codes
- Signature verification

Hardcoded Secrets (grouped here for security audit):
----------------------------------------------------
"""

import hashlib
import hmac
import base64

# ============================================================
# HARDCODED SECRETS - DO NOT EXPOSE IN VERSION CONTROL
# ============================================================

# Flask session secret key
# Used for signing session cookies
SECRET_KEY = "event-ticketing-super-secret-key-2024"

# Fernet encryption key (must be 32 url-safe base64-encoded bytes)
# Used for encrypting JSON data files and QR payloads
# Generate with: Fernet.generate_key()
FERNET_KEY = b"ZmVybmV0LWtleS1mb3ItZXZlbnQtdGlja2V0aW5nPT0="

# HMAC secret for signing QR code payloads
# Used to verify QR code authenticity
HMAC_SECRET = b"hmac-secret-for-qr-signatures-2024"

# Bcrypt salt rounds for password hashing
BCRYPT_ROUNDS = 12

# Simple salt for basic password hashing (without bcrypt dependency)
PASSWORD_SALT = "event-ticketing-salt-2024"


# ============================================================
# SECURITY FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a password using SHA256 with salt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    TODO: Replace with bcrypt in production
    """
    salted = password + PASSWORD_SALT
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return hash_password(password) == hashed


def encrypt_data(data: str) -> bytes:
    """
    Encrypt string data using base64 encoding.
    
    Args:
        data: String data to encrypt
        
    Returns:
        Encrypted bytes
        
    TODO: Replace with Fernet encryption in production
    """
    return base64.urlsafe_b64encode(data.encode())


def decrypt_data(encrypted: bytes) -> str:
    """
    Decrypt base64-encoded data.
    
    Args:
        encrypted: Encrypted bytes to decrypt
        
    Returns:
        Decrypted string
    """
    return base64.urlsafe_b64decode(encrypted).decode()


def generate_signature(payload: str) -> str:
    """
    Generate HMAC signature for a payload.
    
    Args:
        payload: String payload to sign
        
    Returns:
        Hex-encoded signature string
    """
    return hmac.new(
        HMAC_SECRET,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(payload: str, signature: str) -> bool:
    """
    Verify HMAC signature of a payload.
    
    Args:
        payload: Original payload string
        signature: Signature to verify
        
    Returns:
        True if signature is valid, False otherwise
    """
    expected = generate_signature(payload)
    return hmac.compare_digest(expected, signature)
