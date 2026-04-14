import subprocess


def encrypt(text: str) -> str:
    """
    Encrypts a text using a key derived from system information.
    Relies on rust's syskey-crypt CLI app.
    PS: A implementacao antiga em python, que continha tambem opcao de openssl, esta em legado.
    """
    result = subprocess.run(["/usr/local/bin/syskey-crypt", "encrypt", text],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def decrypt(encrypted_text: str) -> str:
    """
    Decrypts a text using a key derived from system information.
    Relies on rust's syskey-crypt CLI app.
    PS: A implementacao antiga em python, que continha tambem opcao de openssl, esta em legado.
    """
    result = subprocess.run(["/usr/local/bin/syskey-crypt", "decrypt", encrypted_text],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def decrypt_from_tempfile(filepath: str, consume: bool = True) -> str:
    """
    Decrypts a text written inside a given file, optionally consuming it.
    If consume=True (default), the file gets deleted after read!
    """
    consume_arg = '--consume' if consume else ''
    result = subprocess.run(["/usr/local/bin/syskey-crypt", "decrypt", "--file", filepath, consume_arg],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


if __name__ == '__main__':
    import sys
    assert len(sys.argv) == 3 and sys.argv[1] in ('encrypt', 'decrypt'),  \
        f'Usage: {sys.argv[0]} <encrypt|decrypt> <text>'

    function = encrypt if sys.argv[1] == 'encrypt' else decrypt
    print(function(sys.argv[2]))
