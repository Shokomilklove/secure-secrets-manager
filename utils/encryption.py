import os

from cryptography.fernet import Fernet


def get_fernet(fernet_key: str) -> Fernet:
    if not fernet_key:
        raise RuntimeError("FERNET_KEY environment variable is not set")
    return Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)


def generate_key() -> str:
    return Fernet.generate_key().decode()


def encrypt(plaintext: str, fernet_key: str) -> str:
    f = get_fernet(fernet_key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, fernet_key: str) -> str:
    f = get_fernet(fernet_key)
    return f.decrypt(ciphertext.encode()).decode()
