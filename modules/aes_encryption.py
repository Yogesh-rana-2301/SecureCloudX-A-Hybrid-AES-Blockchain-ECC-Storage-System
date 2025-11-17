"""
Dynamic AES Encryption Module
Provides functions to generate AES keys and encrypt/decrypt files using AES-256 CBC mode.
"""

import os
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def generate_aes_key():
    """
    Generate a random 256-bit (32-byte) AES key.
    
    Returns:
        bytes: A 32-byte random key suitable for AES-256 encryption
    """
    return get_random_bytes(32)


def encrypt_file(file_path: str, key: bytes) -> dict:
    """
    Encrypt a file using AES-256 in CBC mode with PKCS7 padding.
    
    Args:
        file_path: Path to the file to encrypt
        key: 32-byte AES key
        
    Returns:
        dict: Contains 'encrypted_data' (base64 encoded) and 'iv' (base64 encoded)
        
    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValueError: If key is not 32 bytes
    """
    if len(key) != 32:
        raise ValueError("AES key must be 32 bytes for AES-256")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the file content
    with open(file_path, 'rb') as f:
        plaintext = f.read()
    
    # Generate a random IV (Initialization Vector)
    iv = get_random_bytes(16)
    
    # Create cipher object and encrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    
    # Return base64 encoded results
    return {
        'encrypted_data': base64.b64encode(ciphertext).decode('utf-8'),
        'iv': base64.b64encode(iv).decode('utf-8')
    }


def decrypt_file(encrypted_data: str, key: bytes, iv: str) -> bytes:
    """
    Decrypt AES-256 encrypted data using the provided key and IV.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        key: 32-byte AES key used for encryption
        iv: Base64 encoded initialization vector
        
    Returns:
        bytes: Decrypted file content
        
    Raises:
        ValueError: If key is not 32 bytes or decryption fails
    """
    if len(key) != 32:
        raise ValueError("AES key must be 32 bytes for AES-256")
    
    # Decode base64 inputs
    ciphertext = base64.b64decode(encrypted_data)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher object and decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    return plaintext


def save_encrypted_file(encrypted_data: str, iv: str, output_path: str):
    """
    Save encrypted file data and IV to disk.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        iv: Base64 encoded initialization vector
        output_path: Path where encrypted file should be saved
    """
    import json
    
    data = {
        'encrypted_data': encrypted_data,
        'iv': iv
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f)


def load_encrypted_file(file_path: str) -> dict:
    """
    Load encrypted file data and IV from disk.
    
    Args:
        file_path: Path to the encrypted file
        
    Returns:
        dict: Contains 'encrypted_data' and 'iv'
    """
    import json
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return data
