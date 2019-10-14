
from abc import ABC, abstractmethod


class BaseTrie(ABC):
    types = None

    @abstractmethod
    def serialize(self, value):
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, value):
        raise NotImplementedError

    @abstractmethod
    def get(self, key):
        raise NotImplementedError

    @abstractmethod
    def put(self, key, value):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        raise NotImplementedError



