
from event.base import BaseEventContext


class CandidateContext(BaseEventContext):

    def set_timestamp(self, ts):
        self._timestamp.extend(ts)

    def get(self, key):
        return self.data[key]

    def set(self, data):
        self.data.update(data)

    def get_data_list(self):
        tmp = []
        for v in self.data.copy().values():
            tmp.append(v)
        return tmp

    def remove(self, key):
        del self.data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for k, v in self.data.copy().items():
            yield v


class VoteContext(BaseEventContext):

    def set_timestamp(self, ts):
        self._timestamp = ts

    def get(self, key):
        return self.data[key]

    def set(self, data):
        self.data.update(data)

    def remove(self, key):
        del self._data[key]

    def get_data_list(self):
        tmp = []
        for v in self.data.copy().values():
            tmp.append(v)
        return tmp

    def __iter__(self):
        for k, v in self.data.copy().items():
            yield v


