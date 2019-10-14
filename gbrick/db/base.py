
import plyvel

from abc import ABC, abstractmethod

# 미세한 차이로 leveldb보다 빠르다...


class BaseDB:
    __slots__ = ('_path', '_db')

    def __init__(self, path):
        if not path:
            raise AttributeError('path confused {}'.format(path))
        self._path = path
        self._db = plyvel.DB(
            self._path,
            create_if_missing=True,
        )

    def write_batch(self):
        return self._db.write_batch()

    def snapshot(self):
        return self._db.snapshot()

    def exists(self, key: bytes) -> bool:
        return self._db.get(key) is not None

    def close(self) -> None:
        self._db.close()

    def get(self, key):
        if isinstance(key, str):
            key = key.encode()
        value = self._db.get(key)
        if value is None:
            raise KeyError(str(value))
        return value

    def put(self, key: bytes, value: bytes) -> None:
        self._db.put(key, value)

    def iter(self, start=None, end=None):
        if not start:
            sn = self.snapshot()
            sn_iter = sn.iterator()
        else:
            sn = self.snapshot()
            if not end:
                sn_iter = sn.iterator(start=start)
            else:
                sn_iter = sn.iterator(start=start, stop=end)
        return sn_iter

    def __contains__(self, key: bytes):
        return self.exists(key)


class DB(BaseDB):
    pass


class BaseChainDB(ABC):

    def __init__(self, db: BaseDB):
        self.db = db

    @abstractmethod
    def serialize(self, obj):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def deserialize(self, raw_obj, context):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_chain_id(self):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_block_hash(self, height):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_block_from_height(self, height):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_header_from_height(self, height):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_block_from_hash(self, block_hash):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_header_from_hash(self, block_hash):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_current_height(self):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_transaction_from_lookup(self, tx_hash):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_vote_from_lookup(self, vote_hash):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def set_trie(self, trie):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def get_receipt(self, tx_hash):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def commit(self, block):
        raise NotImplementedError("chain_db: method not implement")

    @abstractmethod
    def __contains__(self, block_hash):
        raise NotImplementedError("chain_db: method not implement")


class BaseStateDB(ABC):
    _logger = None
    _root = None
    _trie = None

    def __init__(self, db: BaseDB):
        self._db = db
        self._cache = {}
        self._code_cache = {}

    @property
    @abstractmethod
    def state_root(self):
        raise NotImplementedError("state_db: method not implement")

    @property
    @abstractmethod
    def cache_trie_root(self):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def set_root(self, state_root):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def serialize(self, obj):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def deserialize(self, raw_obj):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_code(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def set_code(self, address, code):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def increase_nonce(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def set_balance(self, address, balance):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def compute_balance(self, address, consume):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_account(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_balance(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def set_minimum(self, value):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def set_delegated(self, address, to, value):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def register_validator(self, address, rep_id, signature):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_account_delegate(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_const_validator(self):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_const_validator_list(self):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def get_nonce(self, address):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def commit(self):
        raise NotImplementedError("state_db: method not implement")

    @abstractmethod
    def clear(self):
        raise NotImplementedError("state_db: method not implement")

