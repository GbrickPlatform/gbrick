
import hashlib
import hmac

from utils.config import NODE_SEED


def mac(seed):
    return hmac.digest(seed, NODE_SEED(seed), hashlib.sha3_256)


def sha3_hex(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha3_256(value).hexdigest().encode()


def sha3_bytes(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha3_256(value).digest()

