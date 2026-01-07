import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Tuple

def encrypt_file(input_file: str, output_file: str, key: bytes) -> None:
    """Encrypts the content of a file using AES (CBC mode).

    Args:
        input_file (str): Path to the input file to be encrypted.
        output_file (str): Path where the encrypted file will be saved.
        key (bytes): The encryption key (must be 16, 24, or 32 bytes long).
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The input file '{input_file}' does not exist.")
    
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv

    with open(input_file, 'rb') as f:
        plaintext = f.read()

    # Padding
    padding_length = AES.block_size - len(plaintext) % AES.block_size
    plaintext += bytes([padding_length]) * padding_length

    ciphertext = cipher.encrypt(plaintext)

    with open(output_file, 'wb') as f:
        f.write(iv + ciphertext)

def decrypt_file(input_file: str, output_file: str, key: bytes) -> None:
    """Decrypts the content of a file using AES (CBC mode).

    Args:
        input_file (str): Path to the encrypted file.
        output_file (str): Path where the decrypted file will be saved.
        key (bytes): The decryption key (must be 16, 24, or 32 bytes long).
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The input file '{input_file}' does not exist.")
    
    with open(input_file, 'rb') as f:
        iv = f.read(16)
        ciphertext = f.read()

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(ciphertext)

    # Remove padding
    padding_length = plaintext[-1]
    plaintext = plaintext[:-padding_length]

    with open(output_file, 'wb') as f:
        f.write(plaintext)

def generate_key() -> bytes:
    """Generates a new AES key.

    Returns:
        bytes: A new AES key (32 bytes long).
    """
    return get_random_bytes(32)

def store_key(key_id: str, key: bytes) -> None:
    """Stores the key in a secure storage (simulated here as a file).

    Args:
        key_id (str): Identifier for the key.
        key (bytes): The key to be stored.
    """
    with open(f'{key_id}.key', 'wb') as f:
        f.write(key)

def retrieve_key(key_id: str) -> bytes:
    """Retrieves the key from secure storage (simulated here as a file).

    Args:
        key_id (str): Identifier for the key.

    Returns:
        bytes: The retrieved key.
    """
    if not os.path.exists(f'{key_id}.key'):
        raise FileNotFoundError(f"The key file '{key_id}.key' does not exist.")
    
    with open(f'{key_id}.key', 'rb') as f:
        return f.read()

if __name__ == "__main__":
    # Demo usage
    key = generate_key()
    store_key('mykey', key)

    key = retrieve_key('mykey')
    encrypt_file('example.txt', 'example.enc', key)
    decrypt_file('example.enc', 'example_decrypted.txt', key)