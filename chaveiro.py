import platform
import hashlib
from cryptography.fernet import Fernet
import base64


def decrypt_openssl(senha: str, privkey_path: str) -> str:
    from .run import read
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
    key = generate_system_key()
    # print('Decrypting with key:', key)
    f = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
    decrypted_bytes = f.decrypt(encrypted_bytes)
    return decrypted_bytes.decode('utf-8')
