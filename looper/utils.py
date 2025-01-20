import hashlib

SALT = "pink Himalayan rock"


def hashit(thing) -> str:
    return hashlib.md5(f"{thing}{SALT}".encode()).hexdigest()
