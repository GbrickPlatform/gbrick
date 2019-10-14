
import copy
from collections import OrderedDict
from utils.logger import getLogger


class Storage:
    _logger = None

    def __init__(self):
        self._storage = OrderedDict()
        self._cache = []

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger('storage')
        return self._logger

    @property
    def cache(self):
        return copy.deepcopy(self._cache)

    def items(self):
        storage = copy.deepcopy(self._storage)
        return storage.items()

    def cache_clear(self):
        self._cache.clear()

    def get(self, key):
        return copy.deepcopy(self._storage.get(key))

    def range(self, *args):
        if len(args) == 1:
            swc = 0
            end, *_ = args
            if not isinstance(end, int):
                if end == 'all':
                    for k, v in self.items():
                        yield v

            else:
                for k, v in self.items():
                    if swc < end:
                        self._cache.append(k)
                        yield v
                    swc += 1

        elif len(args) == 2:
            swc = 0
            start, end, *_ = args
            if not isinstance(start, int):
                raise ValueError
            if not isinstance(end, int):
                raise ValueError
            for k, v in self.items():
                if swc >= start:
                    if swc < end:
                        self._cache.append(k)
                        yield v
                swc += 1
        else:
            raise AttributeError

    def delete_keys(self, keys: list):
        for key in keys:
            self.delete(key)

    def delete(self, key):
        try:
            del self._storage[key]
        except KeyError as err:
            self.logger.debug("storage:KeyError:{}".format(str(err)))

    def __contains__(self, key):
        return key in self._storage

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __getitem__(self, key):
        if key in self._storage:
            return self._storage[key]
        else:
            return None

    def __len__(self):
        return len(self._storage)



