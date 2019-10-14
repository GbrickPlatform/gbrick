
import base64
import hashlib

from Crypto.Cipher import AES

BS = 16
pad = (lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode())
un_pad = (lambda s: s[:-ord(s[len(s) - 1:])])


def encrypt(raw_key, val):
    pad_str = pad(val)
    key = hashlib.sha256(raw_key).digest()
    encryptor = AES.new(key, AES.MODE_CBC, b' '*16)
    cipher = encryptor.encrypt(pad_str)
    return base64.b64encode(cipher)


def decrypt(raw_key, val):
    cipher = base64.b64decode(val)
    key = hashlib.sha256(raw_key).digest()
    decryptor = AES.new(key, AES.MODE_CBC, b' ' * 16)
    plain = decryptor.decrypt(cipher)
    return un_pad(plain)

