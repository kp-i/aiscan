"""
Encryption module using AES-256-GCM with PBKDF2-HMAC-SHA256 key derivation.

File format: [salt(16)] [nonce(12)] [ciphertext + GCM tag(16)]
"""
import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ITERATIONS = 600_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES-256 key from the master password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: bytes, password: str) -> bytes:
    """Encrypt plaintext with AES-256-GCM. Returns salt+nonce+ciphertext."""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    """Decrypt AES-256-GCM ciphertext. Raises ValueError on wrong password."""
    if len(data) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Data too short to be a valid vault file.")
    salt = data[:SALT_SIZE]
    nonce = data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = data[SALT_SIZE + NONCE_SIZE:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError("復号に失敗しました。マスターパスワードが間違っています。")
