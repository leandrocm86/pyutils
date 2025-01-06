from .run import read
import platform
import hashlib
from cryptography.fernet import Fernet
import base64


def decrypt_openssl(senha: str, privkey_path: str) -> str:
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
        idlines = set(line for line in infos if any(key in line for key in idkeys))
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

    # Create a consistent string from system info
    system_string = "|".join(system_info)

    # Generate a SHA-256 hash of the system information
    key_hash = hashlib.sha256(system_string.encode()).digest()

    # Convert to URL-safe base64 encoding as required by Fernet
    key = base64.urlsafe_b64encode(key_hash)

    return key


def encrypt(message: str):
    """
    Encrypts a message using a key derived from system information.
    """
    key = generate_system_key()
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message


def decrypt(encrypted_message: str):
    """
    Decrypts a message using a key derived from system information.
    """
    key = generate_system_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message).decode()
    return decrypted_message
