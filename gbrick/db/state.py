
from pickle import dumps, loads

from gbrick.db.base import BaseStateDB
from gbrick.types.base import BaseAccount
from gbrick.types.prepare import prepare_rep, prepare_account

from utils.crypto.hash import sha3_hex
from utils.exceptions import ValidationError, CacheError
from utils.config import Lookup
from gbrick.types.config import REP_DICT
from gbrick.types.deserializer import deserialize_account
from utils.trie.prepare import prepare_trie
from utils.logger import getLogger

from utils.util import (
    int_to_bytes32, bytes_to_int,
    extract_values, get_trie_key
)

from gbrick.validation import (
    validate_address, validate_contract,
    validate_code
)


class StateDB(BaseStateDB):

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger('statedb')
        return self._logger

    @property
    def state_root(self):
        return self._root

    @property
    def cache_trie_root(self):
        return self._trie.root

    def set_root(self, state_root):
        self._trie = prepare_trie(state_root, self._db)
        self._root = self._trie.root

    def serialize(self, obj):
        return dumps(obj.to_dict())

    def deserialize(self, raw_obj):
        return self._deserialize(loads(raw_obj))

    def _deserialize(self, dict_obj) -> BaseAccount:
        return deserialize_account(dict_obj)

    def _get_account(self, address) -> BaseAccount:
        if address in self._cache:
            return self._cache[address]
        try:
            trie_key = get_trie_key(address)
            account = self._deserialize(self._trie.get(trie_key))
        except KeyError:
            account = prepare_account(address_account=address)
        self._cache[address] = account
        return account

    def _set_account(self, address, account):
        self._cache[address] = account
        trie_key = get_trie_key(address)
        self._trie.put(trie_key, account.to_dict())

    def get_minimum(self):
        return bytes_to_int(self._db.get(Lookup.minimum()))

    def set_minimum(self, value):
        self._db.put(Lookup.minimum(), int_to_bytes32(value))

    def get_nonce(self, address):
        validate_address(address)
        account = self._get_account(address)
        return account.nonce

    def increase_nonce(self, address):
        validate_address(address)
        account = self._get_account(address)
        self._set_account(address, account.copy(nonce=account.nonce+1))

    def compute_balance(self, address, consume):
        validate_address(address)
        self.set_balance(address, self.get_balance(address) + consume)

    def compute_stake_balance(self, address, stake):
        validate_address(address)
        account = self._get_account(address)
        new_balance = account.delegated_stake_balance + stake
        self._set_account(address, account.copy(delegated_stake_balance=new_balance))

    def set_balance(self, address, balance):
        validate_address(address)
        account = self._get_account(address)
        self._set_account(address, account.copy(balance=balance))

    def get_balance(self, address):
        validate_address(address)
        account = self._get_account(address)
        return account.balance

    def get_account(self, address):
        validate_address(address)
        account = self._get_account(address)

        # print('_get_const_validator : ', self.get_validator(address).to_dict())
        # print('get_const_validator_list : ', self.get_const_validator_list())
        return account

    def get_delegated_balance(self, address):
        validate_address(address)
        account = self._get_account(address)
        return account.delegated_stake_balance

    def get_code(self, address):
        try:
            validate_contract(address)
        except ValidationError:
            return None
        account = self._get_account(address)
        if account.code in self._code_cache:
            return self._code_cache[account.code]
        try:
            code = self._db.get(account.code)
        except KeyError:
            return b''
        self._code_cache[account.code] = code
        return code

    def set_code(self, address, code):
        validate_contract(address)
        code = validate_code(code)
        account = self._get_account(address)
        hashcode = sha3_hex(code)
        self._code_cache[hashcode] = code
        self._db.put(hashcode, code)
        self._set_account(address, account.copy(code=hashcode))

    def _set_delegated(self, hash_key, value):
        if hash_key not in self._db:
            self._db.put(hash_key, dumps(value))
        else:
            address, to, new_value = value
            _address, _to, old_value = self._get_delegated(hash_key)
            if address != _address:
                raise ValueError
            change_value = old_value + new_value
            self._db.put(hash_key, dumps((address, to, change_value)))

    def set_delegated(self, address, to, value):
        hash_key = sha3_hex(b''.join((address, to)))
        account = self._get_account(address)
        account_to = self._get_account(address)

        delegated = account.delegated
        delegated_stake = account_to.delegated
        if hash_key not in account.delegated:
            delegated.append(hash_key)
        if hash_key not in account_to.delegated:
            delegated.append(hash_key)

        self._set_account(address, account.copy(delegated=delegated))
        self._set_account(to, account_to.copy(delegated=delegated_stake))
        self.compute_balance(address, -1 * value)
        self.compute_stake_balance(to, value)
        self._set_delegated(hash_key, (address, to, value))

    def _get_delegated(self, hash_key):
        return loads(self._db.get(hash_key))

    def get_delegated(self, address):
        account = self._get_account(address)
        delegate = account.delegated
        delegated_info = []
        for key in delegate:
            delegated_info.append(self._get_delegated(key))
        return delegated_info

    def get_account_delegate(self, address):
        info = self.get_delegated(address)
        account_delegate = 0
        for sender, to, value in info:
            if sender == to:
                account_delegate += value
        return account_delegate

    def register_validator(self, address, rep_id, signature):
        account = self._get_account(address)
        if self.get_account_delegate(address) < self.get_minimum():
            # raise ValidationError("{} is not qualify".format(address))
            return
        self._set_account(address, account.copy(node_id=rep_id,
                                                node_signature=signature))
        self._set_const_validator(address, rep_id)

    def _set_const_validator(self, address, rep_id):
        # update coming soon TODO
        trie_key = get_trie_key(Lookup.constant_rep())
        rep = prepare_rep(node_id=rep_id,
                          account=address,
                          delegate=self.get_delegated_balance(address))
        try:
            qualify = self.get_const_validator_list()
            qualify.append(rep.to_dict())
            self._trie.put(trie_key, qualify)
        except KeyError:
            self._trie.put(trie_key, [rep.to_dict()])

    def _get_const_validator(self):
        # update coming soon TODO
        trie_key = get_trie_key(Lookup.constant_rep())
        validators = self._trie.get(trie_key)
        list_validators = []
        for rep in validators:
            ex = extract_values(rep, REP_DICT)
            rep_obj = prepare_rep(node_id=ex.node_id.encode(),
                                  account=ex.account.encode(),
                                  delegate=ex.delegated)
            list_validators.append(rep_obj)
        return list_validators

    def _get_const_validator_list(self):
        trie_key = get_trie_key(Lookup.constant_rep())
        reps = self._trie.get(trie_key)
        return reps

    def get_const_validator(self):
        return self._get_const_validator()

    def get_const_validator_list(self):
        return self._get_const_validator_list()

    def get_validator_id(self):
        validators = self.get_const_validator()
        validator_di_set = [rep.node_id for rep in validators]
        return validator_di_set

    def get_validator(self, validator_id):
        list_validators = self.get_const_validator()
        validator = None
        for rep in list_validators:
            if validator_id == rep.node_id:
                validator = rep.copy()
                break
        return validator

    def get_validator_count(self):
        reps = self._get_const_validator_list()
        reps_count = len(reps)
        allow = int((reps_count - 1) / 3)
        return reps_count, allow

    def _compute_promote_rank(self):
        # rep node: delegated stake balance was ranked compute
        # coming soon, update is not yet
        pass

    def commit(self):
        # state cache. committed db before compare cache??
        for address, account in self._cache.copy().items():
            trie_key = get_trie_key(address)
            try:
                acc = self._trie.get(trie_key)
            except KeyError:
                pass
            else:
                if account.to_dict() != acc:
                    self.logger.debug("statedb cache: {},  "
                                      "trie cache: {}".format(account.to_dict(), acc))
                    raise CacheError("latest account state error, "
                                     "{}".format(address.decode()))

        self._root = self._trie.commit()

    def clear(self):
        self._cache.clear()
        self._code_cache.clear()
        self._trie.clear()


# TODO: finalize cache 처리.

