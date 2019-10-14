
from abc import ABC, abstractmethod


class BaseManager(ABC):
    _channel = None
    _evt = None

    def get(self, key):
        return self.storage.get(key)

    def range(self, *args):
        return self.storage.range(*args)

    def delete_keys(self, keys: list):
        self.storage.delete_keys(keys)

    def delete(self, key):
        self.storage.delete(key)

    def get_cache(self):
        return self.storage.cache

    def cache_clear(self):
        self.storage.cache_clear()

    @property
    @abstractmethod
    def storage(self):
        raise NotImplementedError('manager: method not implement')

    @abstractmethod
    def event_run(self):
        raise NotImplementedError('manager: method not implement')

    @abstractmethod
    def process_event(self, channel, body, envelope, properties):
        raise NotImplementedError('server: method not implement')

    def __len__(self):
        return len(self.storage)


