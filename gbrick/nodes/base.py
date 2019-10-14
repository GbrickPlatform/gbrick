
from abc import ABC, abstractmethod


class BaseNode(ABC):
    _sync_mode = False

    @property
    @abstractmethod
    def event(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def chain(self):
        raise NotImplementedError

    async def run(self):
        await self._run()

    @abstractmethod
    async def _run(self):
        raise NotImplementedError


