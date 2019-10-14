
import ecdsa
import os
import binascii

from utils.config import ADDRESS_SIZE, O_COIN_TYPE, CONTRACT_TYPE
from utils.crypto.cipher import encrypt, decrypt
from utils.crypto.hash import mac, sha3_hex


def create_nodebase(public_key: bytes):
    """ create account address
    :param public_key: (bytes) public key
    :return: (bytes) account address
    >>> create_nodebase(b"~\xe2\x15(\x07\x02?l\xd8\x87...")
    >>> return b'gBx7dfae3...'
    """
    address = sha3_hex(public_key)[-40:]
    prefix_address = b''.join((O_COIN_TYPE, address))
    assert len(prefix_address) == ADDRESS_SIZE
    return prefix_address


def create_contract(node_base, nonce):
    """ create contract address
    :param node_base: (bytes) account address
    :param nonce: (int) account nonce
    :return: (bytes) contract address
    >>> create_contract(b'gBx7dfae3...', 45)
    >>> return b'gBca8fed...'
    """

    address = sha3_hex(b''.join((node_base, str(nonce).encode())))[-40:]
    prefix_address = b''.join((CONTRACT_TYPE, address))
    assert len(prefix_address) == ADDRESS_SIZE
    return prefix_address


class Address:
    """ address management class
    """

    @classmethod
    def create(cls, node_dir, seed):
        """ create address
        :param node_dir: (str) directory path
        :param seed: (bytes) keystore password
        :return: tuple(nodebase, Signingkey)
        >>> create('./test/', b'seed')
        >>> return b'gBx34fb...', SigningKey()
        """
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        node_base = create_nodebase(public_key.to_string())
        cipher = encrypt(seed, private_key.to_pem())
        node_base_path = os.path.join(node_dir, mac(seed).hex())
        with open(node_base_path, 'wb') as key_file:
            key_file.write(cipher)

        return node_base, private_key

    @classmethod
    def load(cls, node_dir, seed):
        """ load address
        :param node_dir: (str) directory path
        :param seed: (bytes) keystore password
        :return: tuple(nodebase, SigningKey)
        >>> load('./test/', b'seed')
        >>> return b'gBx34fb...', SigningKey()
        """
        node_base_path = os.path.join(node_dir, mac(seed).hex())
        with open(node_base_path, 'rb') as key_file:
            cipher = key_file.read()

        plain = decrypt(seed, cipher)
        private_key = ecdsa.SigningKey.from_pem(plain.decode())
        public_key = private_key.get_verifying_key()
        node_base = create_nodebase(public_key.to_string())
        return node_base, private_key

    @classmethod
    def change(cls, node_dir, old_seed, new_seed):
        """ keystore password change
        :param node_dir: directory path
        :param old_seed: current keystore password
        :param new_seed: change new keystore password
        :return: tuple(nodebase, SigningKey)
        """
        old_base_path = os.path.join(node_dir, mac(old_seed).hex())
        new_base_path = os.path.join(node_dir, mac(new_seed).hex())

        old_base, private_key = cls.load(node_dir, old_seed)
        public_key = private_key.get_verifying_key()
        node_base = create_nodebase(public_key.to_string())
        if os.path.isfile(old_base_path):
            os.remove(old_base_path)

        cipher = encrypt(new_seed, private_key.to_pem())
        with open(new_base_path, 'wb') as key_file:
            key_file.write(cipher)

        return node_base, private_key

    @classmethod
    def import_key(cls, node_dir, key, seed):
        """ import private key
        :param node_dir: directory path
        :param key: private key
        :param seed: keystore password
        :return: tuple(nodebase, SigningKey)
        """

        raw_key = binascii.unhexlify(key.decode())
        private_key = ecdsa.SigningKey.from_string(raw_key, curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        node_base = create_nodebase(public_key.to_string())
        node_base_path = os.path.join(node_dir, mac(seed.encode()).hex())
        cipher = encrypt(seed.encode(), private_key.to_pem())
        with open(node_base_path, 'wb') as file:
            file.write(cipher)
        return node_base, private_key


def load_node_base(node_dir, seed, new_seed=None):
    """ load node base
    :param node_dir: (str) directory path
    :param seed: (str) keystore password
    :param new_seed: union[None, bytes] new keystore password
    :return: tuple(bytes, SigningKey)
    >>> load_node_base('./test/', 'seed', Optional[Union[None, 'new-seed']])
    """
    seed = seed.encode()
    if seed and new_seed:
        new_seed = new_seed.encode()
        return Address.change(node_dir, seed, new_seed)

    node_base_path = os.path.join(node_dir, mac(seed).hex())
    if os.path.isfile(node_base_path):
        return Address.load(node_dir, seed)
    else:
        return Address.create(node_dir, seed)


