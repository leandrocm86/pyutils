import os
import getpass
import platform
import hashlib
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def _load_aes_key(key_path):
    """Loads a Base64 encoded AES key from a file."""
    try:
        with open(key_path, 'r') as f:
            key_b64 = f.read().strip()
            key = base64.b64decode(key_b64)
            if len(key) != 32:  # Check if the key is 256 bits (32 bytes)
                raise ValueError("The key must be 32 bytes (256 bits)")
            return key
    except FileNotFoundError:
        raise FileNotFoundError(f"Key file not found at: {key_path}")
    except ValueError as e:
        raise ValueError(f"Invalid key file: {e}")


def encrypt_aes(plaintext, key_path):
    '''
    Encrypts plaintext using AES-256-GCM.
    OBS: Nao eh compativel com openssl. Um texto encriptado com essa funcao deve ser desencriptado com a funcao decrypt_aes.
    '''
    key = _load_aes_key(key_path)
    nonce = os.urandom(12)  # GCM typically uses 96 bits/12 bytes for nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
    return base64.b64encode(nonce + encryptor.tag + ciphertext).decode('utf-8')


def decrypt_aes(ciphertext, key_path):
    '''
    Decrypts ciphertext using AES-256-GCM.
    OBS: Nao eh compativel com openssl. Esta funcao soh pode descriptografar textos encriptados com a funcao encrypt_aes.
    '''
    key = _load_aes_key(key_path)
    decoded_data = base64.b64decode(ciphertext.encode('utf-8'))
    nonce = decoded_data[:12]
    tag = decoded_data[12:28]  # GCM tag is 16 bytes
    ciphertext = decoded_data[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode('utf-8')


@DeprecationWarning
def decrypt_openssl(senha: str, privkey_path: str) -> str:
    from .system import read
    cmd = f"echo -n \"{senha}\" | base64 --decode | openssl pkeyutl -decrypt -inkey '{privkey_path}'"
    return read(cmd)


def get_hardware_id() -> str:
    """
    Gets stable hardware identifiers that persist across Docker containers.
    Returns a tuple of identifiers found.
    """
    identifiers: list[str] = []

    with open('/proc/cpuinfo') as f:
        infos = [line.lower() for line in f.readlines()]
        idkeys = ('serial', 'uuid', 'physical id', 'model name')
        idlines = [line for line in infos if any(key in line for key in idkeys)]
        for line in idlines:
            identifiers.append(line.split(':')[1].strip())

    with open('/sys/class/dmi/id/bios_vendor') as f:
        identifiers.append(f.read().strip())
    with open('/sys/class/dmi/id/bios_version') as f:
        identifiers.append(f.read().strip())

    return '|'.join(identifiers)


def generate_system_key():
    """
    Generates a key based on system information.
    Returns a 32-byte key suitable for Fernet encryption.
    """
    # Collect system information
    system_info = [
        platform.system(),
        platform.platform(),
        platform.version(),
        platform.machine(),
        platform.node(),
        platform.processor(),
        os.getlogin(),
        getpass.getuser(),
        get_hardware_id()
    ]
    
    # print('System info:', system_info)
    # Create a consistent string from system info
    system_string = "|".join(system_info)

    # Generate a SHA-256 hash of the system information
    key_hash = hashlib.sha256(system_string.encode()).digest()

    # Convert to URL-safe base64 encoding as required by Fernet
    key = base64.urlsafe_b64encode(key_hash)

    return key


def encrypt(text: str) -> str:
    """
    Encrypts a text using a key derived from system information.
    """
    key = generate_system_key()
    # print('Encrypting with key:', key)
    f = Fernet(key)
    encrypted_bytes = f.encrypt(text.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')


def decrypt(encrypted_text: str) -> str:
    """
    Decrypts a text using a key derived from system information.
    """
    f = Fernet(generate_system_key())

    def encrypted_bytes(encrypted_text: str):
        return base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))

    return f.decrypt(encrypted_bytes(encrypted_text)).decode('utf-8')


def decrypt_from_tempfile(filepath: str) -> str:
    """
    Decrypts a text written inside a given file, consuming it.
    The file gets deleted after read!
    """
    try:
        with open(filepath, 'r') as f:
            return decrypt(f.read())
    finally:
        os.remove(filepath)
    