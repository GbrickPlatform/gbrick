
from abc import ABC, abstractmethod


class BaseEvent(ABC):
    _event = None

    @property
    @abstractmethod
    def event(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def _run(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def prepare(self, is_run):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def reset(self, chain):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def clear(self, chain, block):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def transaction_exists(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def candidate_exists(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def vote_exists(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def confirm_exists(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def finalize_exists(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def get_transaction(self):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def get_candidate(self, height):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def get_vote(self, height):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def get_confirm(self, height):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def get_finalize_block(self, height):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def send(self, obj, exchange):
        raise NotImplementedError('event: method not implement')

    @abstractmethod
    def set_info(self, count, terms):
        raise NotImplementedError('event: method not implement')


class BaseEventContext(ABC):

    def __init__(self):
        self._height = 0
        self._creators = []
        self._timestamp = []
        self._data = {}

    @property
    def time(self):
        if self._timestamp is None:
            raise AttributeError
        return self._timestamp

    @property
    def height(self):
        if self._height is None:
            raise AttributeError
        return self._height

    @property
    def creators(self):
        if self._creators is None:
            raise AttributeError
        return self._creators

    @property
    def data(self):
        return self._data

    def set_height(self, h):
        self._height = h

    def set_creators(self, creators):
        self._creators.extend(creators)

    @abstractmethod
    def set_timestamp(self, ts):
        raise NotImplementedError('event context: method not implement')

    @abstractmethod
    def get(self, key):
        raise NotImplementedError('event context: method not implement')

    @abstractmethod
    def set(self, data):
        raise NotImplementedError('event context: method not implement')

    @abstractmethod
    def remove(self, key):
        raise NotImplementedError('event context: method not implement')





