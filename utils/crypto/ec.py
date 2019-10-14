
import binascii
import hashlib
import struct
import time

from utils.util import bytes_to_int, int_to_bytes32
from utils.crypto.hash import sha3_bytes
from utils.address import create_nodebase
from ecdsa.rfc6979 import generate_k
from utils.exceptions import ValidationError


class Curve:
    a = 0
    b = 7
    p = 2 ** 256 - 2 ** 32 - 977
    n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
    Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
    Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
    G = (Gx, Gy)


CURVE = Curve()


def inverse(p, q):
    if p == 0:
        return 0

    l, h = 1, 0
    low, high = p % q, q
    while low > 1:
        r = high // low
        _n, n = h - l * r, high - low * r
        l, low, h, high = _n, n, l, low
    return l % q


def from_mtx(p):
    k = inverse(p[2], CURVE.p)
    return (p[0] * k**2) % CURVE.p, (p[1] * k**3) % CURVE.p


def to_mtx(p):
    return p[0], p[1], 1


def mtx_double(p):
    if not p[1]:
        return 0, 0, 0

    _y = (p[1]**2) % CURVE.p
    _s = (4 * p[0] * _y) % CURVE.p
    _m = (3 * p[0]**2 + CURVE.a * p[2]**4) % CURVE.p

    x = (_m**2 - 2 * _s) % CURVE.p
    y = (_m * (_s - x) - 8 * _y ** 2) % CURVE.p
    z = (2 * p[1] * p[2]) % CURVE.p
    return x, y, z


def mtx_add(p, q):
    if not p[1]:
        return q
    if not q[1]:
        return p

    x1 = (p[0] * q[2] ** 2) % CURVE.p
    x2 = (q[0] * p[2] ** 2) % CURVE.p
    y1 = (p[1] * q[2] ** 3) % CURVE.p
    y2 = (q[1] * p[2] ** 3) % CURVE.p
    if x1 == x2:
        if y1 != y2:
            return 0, 0, 1
        return mtx_double(p)

    _x = x2 - x1
    _y = y2 - y1
    _u = (_x * _x) % CURVE.p
    _v = (_x * _u) % CURVE.p
    _uv = (x1 * _u) % CURVE.p

    x = (_y**2 - _v - 2 * _uv) % CURVE.p
    y = (_y * (_uv - x) - y1 * _v) % CURVE.p
    z = (_x * p[2] * q[2]) % CURVE.p
    return x, y, z


def mtx_mul(p, q):
    if p[1] == 0 or q == 0:
        return 0, 0, 1
    if q == 1:
        return p
    if q < 0 or q >= CURVE.n:
        return mtx_mul(p, q // 2)
    if (q % 2) == 0:
        return mtx_double(mtx_mul(p, q // 2))
    if (q % 2) == 1:
        return mtx_add(mtx_double(mtx_mul(p, q // 2)), p)


def mul(p, q):
    return from_mtx(mtx_mul(to_mtx(p), q))


def parse_curve(sig):
    return (
        bytes_to_int(sig[:32]),
        bytes_to_int(sig[32:64]),
        int(sig[64:].hex())
    )


def sign(msg_hash, pk, k):
    msg_hash = bytes_to_int(msg_hash)
    r, y = mul(CURVE.G, k)
    s = inverse(k, CURVE.n) * (msg_hash + r * bytes_to_int(pk)) % CURVE.n
    _v = (y % 2) ^ (0 if s * 2 < CURVE.n else 1)
    s = s if s * 2 < CURVE.n else CURVE.n - s
    v = '01' if _v == 1 else '00'
    sig = int_to_bytes32(r) + int_to_bytes32(s)
    assert len(sig) == 64
    return sig.hex() + v


async def recover(msg_hash, sig):
    r, s, v = parse_curve(sig)
    x = r
    a = ((x * x * x) + (CURVE.a * x) + CURVE.b) % CURVE.p
    b = pow(a, (CURVE.p + 1) // 4, CURVE.p)

    y = b if (b - (v % 2)) % 2 == 0 else CURVE.p - b
    e = bytes_to_int(msg_hash)

    mg = mtx_mul((CURVE.Gx, CURVE.Gy, 1), (CURVE.n - e) % CURVE.n)
    xy = mtx_mul((x, y, 1), s)
    _xy = mtx_add(mg, xy)
    mtx = mtx_mul(_xy, inverse(r, CURVE.n))
    p, q = from_mtx(mtx)
    return int_to_bytes32(p) + int_to_bytes32(q)


class ECSigner:
    __slots__ = '_ephem_keystore'

    def __init__(self, node_key):
        self._ephem_keystore = node_key

    def make_signature(self, msg_hash):
        msg_hash = binascii.unhexlify(msg_hash)
        k = generate_k(
            order=CURVE.n,
            secexp=bytes_to_int(self._ephem_keystore.to_string()),
            hash_func=hashlib.sha3_256,
            data=sha3_bytes(msg_hash + struct.pack('d', time.time()))
        )
        sig = sign(msg_hash, self._ephem_keystore.to_string(), k)
        return sig.encode()

    def __call__(self, obj_hash):
        return self.make_signature(obj_hash)


async def verify(msg_hash, sig, sender):
    signature = binascii.unhexlify(sig)
    msg_hash = binascii.unhexlify(msg_hash)
    public_key = await recover(msg_hash, signature)

    if isinstance(sender, str):
        sender = sender.encode()
    if sender != create_nodebase(public_key):
        raise ValidationError(
            "object base on {} "
            "but signature signer is {}".format(
                sender,
                create_nodebase(public_key)
            )
        )




