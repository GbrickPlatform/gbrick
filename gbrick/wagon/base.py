
import asyncio
from weakref import WeakSet
from abc import ABC, abstractmethod
from gbrick.validation import validate_address
from utils.exceptions import FinalizeError


class BaseWagon(ABC):
    _status = None
    _state = None
    _trie = None
    _receipts = []
    _total_paid = 0

    def __init__(self, db_context, header):
        self._db_context = db_context
        self.header = header
        self._tasks = WeakSet()

    async def event(self):
        loop = asyncio.get_event_loop()
        f = [asyncio.ensure_future(self._event(), loop=loop)]
        try:
            done, tasks = await asyncio.wait(f, timeout=30, loop=loop)
        except asyncio.futures.CancelledError:
            for fut in f:
                fut.cancel()
            raise FinalizeError("don't complete tasks.")
        if not done:
            for task in tasks:
                task.cancel()
            raise FinalizeError
        return

    async def _event(self):
        while True:
            await asyncio.sleep(0.005)
            if len(self._tasks) == 0:
                return

    @property
    @abstractmethod
    def state(self):
        raise NotImplementedError('wagon: method not implement')

    @abstractmethod
    def genesis_declare(self, genesis, constant):
        raise NotImplementedError('wagon: method not implement')

    @abstractmethod
    def prepare_executor(self, index, transaction):
        raise NotImplementedError('wagon: method not implement')

    @abstractmethod
    def execute_transaction(self, version, index, header, transaction):
        raise NotImplementedError('wagon: method not implement')

    @abstractmethod
    def execute_transactions(self, version, header):
        raise NotImplementedError('wagon: method not implement')

    @abstractmethod
    def set_execute_result(self, context, header, transaction):
        raise NotImplementedError('wagon: method not implement')


class BaseState(ABC):

    def __init__(self, db_context, header):
        self._db_context = db_context
        self.header = header
        if self.header is not None:
            self.state_db.set_root(header.hash_state_root)

    @property
    @abstractmethod
    def state_db(self):
        raise NotImplementedError('state: method not implement')

    @property
    @abstractmethod
    def cache_trie_root(self):
        raise NotImplementedError('state: method not implement')

    @property
    @abstractmethod
    def state_root(self):
        raise NotImplementedError('state: method not implement')

    @classmethod
    @abstractmethod
    def genesis_declare(cls, header, constant):
        raise NotImplementedError('state: method not implement')

    @abstractmethod
    def execute_transaction(self, version, header, transaction, executor, context):
        raise NotImplementedError('state: method not implement')

    @abstractmethod
    def validate_transaction(self, version, transaction):
        raise NotImplementedError('state: method not implement')

    @abstractmethod
    def commit(self):
        raise NotImplementedError('state: method not implement')

    @abstractmethod
    def clear(self):
        raise NotImplementedError('state: method not implement')


class BaseExecuteContext(ABC):
    _ratio = None
    _code = None
    _code_lookup = None
    _message = {}
    _create_address = b''
    _error = ''
    _state = {}
    __slots__ = ('index', '_limited', '_fee', '_tx_base', '_nonce', 'to', 'value', '_type')

    def __init__(self, index, tx_base, to, value, fee, nonce, type):
        self.index = index
        self._limited = fee
        self.value = value
        validate_address(tx_base)
        self._tx_base = tx_base
        self._fee = 0
        self._nonce = nonce
        self.to = to
        self._type = type

    @property
    @abstractmethod
    def is_create(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def create_address(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def txbase(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def limited(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def code(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def fee_remainder(self):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def is_precompile(self):
        raise NotImplementedError('execute context: method not implement')

    @property
    @abstractmethod
    def nonce(self):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def set_error(self, err):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def use(self, cmd):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def set_code(self, code):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def set_message(self, message):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def set_address(self, create_address):
        raise NotImplementedError('execute context: method not implement')

    @abstractmethod
    def increase_nonce(self):
        raise NotImplementedError('execute context: method not implement')


class BaseExecutor(ABC):

    @abstractmethod
    def validate_context(self, state, context, transaction):
        raise NotImplementedError('executor: method not implement')

    @abstractmethod
    def prepare_execute(self, state, context, transaction):
        raise NotImplementedError('executor: method not implement')

    @abstractmethod
    def execute(self, state, context):
        raise NotImplementedError('executor: method not implement')

    @abstractmethod
    def __call__(self, state, context, transaction):
        raise NotImplementedError('executor: method not implement')


