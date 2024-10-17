import hashlib
import os
import base64


class PasswordValidationError(Exception):
    pass


def hash_password(password: str):
    salt = os.urandom(24)
    pow = 13
    n = 2**pow
    r = 8
    p = 10
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p)
    return f"scrypt${pow}${r}${p}${base64.b64encode(salt).decode()}${base64.b64encode(hashed).decode()}"


def verify_password(password: str, hash: str):
    try:
        algo, pow, r, p, salt, hashed = hash.split("$")
        n = 2 ** int(pow)
        r = int(r)
        p = int(p)
        salt = base64.b64decode(salt)
        expected_hash = base64.b64decode(hashed)
    except ValueError:
        raise PasswordValidationError("Corrupted password")

    if algo != "scrypt":
        raise PasswordValidationError("Unrecognized algorithm")

    hashed = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p)
    if hashed != expected_hash:
        raise PasswordValidationError("Password mismatch")
