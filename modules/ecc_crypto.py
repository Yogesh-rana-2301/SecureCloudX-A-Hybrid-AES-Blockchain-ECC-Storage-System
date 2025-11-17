"""
ECC (Elliptic Curve Cryptography) Module
Provides functions for ECC key generation and secure AES key exchange using SECP256R1 curve.
"""

import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os


def generate_ecc_keypair():
    """
    Generate an ECC key pair using the SECP256R1 (P-256) curve.
    
    Returns:
        dict: Contains 'private_key' and 'public_key' in PEM format (base64 encoded strings)
    """
    # Generate private key using SECP256R1 curve
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # Get the corresponding public key
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return {
        'private_key': private_pem.decode('utf-8'),
        'public_key': public_pem.decode('utf-8')
    }


def encrypt_aes_key_with_ecc(aes_key: bytes, recipient_public_key_pem: str) -> str:
    """
    Encrypt an AES key using the recipient's ECC public key via ECIES-like scheme.
    
    This uses ECDH (Elliptic Curve Diffie-Hellman) to derive a shared secret,
    then uses that to encrypt the AES key.
    
    Args:
        aes_key: The AES key to encrypt (32 bytes)
        recipient_public_key_pem: Recipient's public key in PEM format
        
    Returns:
        str: Base64 encoded encrypted package containing ephemeral public key and encrypted AES key
    """
    # Load recipient's public key
    recipient_public_key = serialization.load_pem_public_key(
        recipient_public_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    
    # Generate ephemeral key pair for this encryption
    ephemeral_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    ephemeral_public_key = ephemeral_private_key.public_key()
    
    # Perform ECDH to get shared secret
    shared_secret = ephemeral_private_key.exchange(ec.ECDH(), recipient_public_key)
    
    # Derive encryption key from shared secret using HKDF
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'aes-key-encryption',
        backend=default_backend()
    ).derive(shared_secret)
    
    # Encrypt the AES key using the derived key
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_aes_key = encryptor.update(aes_key) + encryptor.finalize()
    
    # Serialize ephemeral public key
    ephemeral_public_pem = ephemeral_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Package everything together: ephemeral_public_key_length + ephemeral_public_key + iv + encrypted_aes_key
    package = (
        len(ephemeral_public_pem).to_bytes(4, 'big') +
        ephemeral_public_pem +
        iv +
        encrypted_aes_key
    )
    
    return base64.b64encode(package).decode('utf-8')


def decrypt_aes_key_with_ecc(encrypted_package: str, private_key_pem: str) -> bytes:
    """
    Decrypt an AES key using the recipient's ECC private key.
    
    Args:
        encrypted_package: Base64 encoded package from encrypt_aes_key_with_ecc
        private_key_pem: Recipient's private key in PEM format
        
    Returns:
        bytes: Decrypted AES key (32 bytes)
    """
    # Decode the package
    package = base64.b64decode(encrypted_package)
    
    # Extract components
    ephemeral_key_length = int.from_bytes(package[:4], 'big')
    ephemeral_public_pem = package[4:4+ephemeral_key_length]
    iv = package[4+ephemeral_key_length:4+ephemeral_key_length+16]
    encrypted_aes_key = package[4+ephemeral_key_length+16:]
    
    # Load keys
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    
    ephemeral_public_key = serialization.load_pem_public_key(
        ephemeral_public_pem,
        backend=default_backend()
    )
    
    # Perform ECDH to get shared secret
    shared_secret = private_key.exchange(ec.ECDH(), ephemeral_public_key)
    
    # Derive decryption key from shared secret
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'aes-key-encryption',
        backend=default_backend()
    ).derive(shared_secret)
    
    # Decrypt the AES key
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    aes_key = decryptor.update(encrypted_aes_key) + decryptor.finalize()
    
    return aes_key
