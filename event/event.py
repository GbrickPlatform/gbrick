
import asyncio

from event.base import BaseEvent
from event.manager.prepare import prepare_event
from weakref import WeakSet
from event.event_context import CandidateContext, VoteContext
from utils.singleton import singleton


class Event:
    transaction = asyncio.Event()
    finalize = asyncio.Event()
    vote = asyncio.Event()
    candidate = asyncio.Event()
    confirm = asyncio.Event()


@singleton
class GBrickEvent(BaseEvent):

    def __init__(self):
        self._tasks = WeakSet()
        self._evt = Event()

    @property
    def event(self):
        if self._event is None:
            self._event = prepare_event()
        return self._event

    def prepare(self, chain):
        self._common_run()
        if chain.is_validator:
            self._run()

    def _common_run(self):
        for name in self.event.__slots__[:2]:
            obj = getattr(self.event, name)     # get manager class
            obj.set_event(getattr(self._evt, name))
            self._tasks.add(
                asyncio.ensure_future(obj.event_run())
            )

    def _run(self):
        for name in self.event.__slots__[2:]:
            obj = getattr(self.event, name)  # get manager class
            obj.set_event(getattr(self._evt, name))
            self._tasks.add(
                asyncio.ensure_future(obj.event_run())
            )
    #  common : tx, finalize
    #  validator: candi, vote, confirm

    async def reset(self, chain) -> None:
        self._common_reset()
        if chain.is_validator:
            self._reset()

    def _common_reset(self):
        for name in self.event.__slots__[:2]:
            obj = getattr(self._evt, name)
            obj.clear()

    def _reset(self):
        for name in self.event.__slots__[2:]:
            obj = getattr(self._evt, name)
            obj.clear()

    async def clear(self, chain, block) -> None:
        self._common_clear(block)
        if chain.is_validator:
            self._clear(block)
        await self.reset(chain)

    def _common_clear(self, block):
        for name in self.event.__slots__[:2]:
            event = getattr(self.event, name)
            event.clear(block)

    def _clear(self, block):
        for name in self.event.__slots__[2:]:
            event = getattr(self.event, name)
            event.clear(block)

    async def transaction_exists(self):
        await self.event.transaction.exists()
        return await self._evt.transaction.wait()

    async def candidate_exists(self):
        await self.event.candidate.exists()
        return await self._evt.candidate.wait()

    async def vote_exists(self):
        await self.event.vote.exists()
        return await self._evt.vote.wait()

    async def confirm_exists(self):
        await self.event.confirm.exists()
        return await self._evt.confirm.wait()

    async def finalize_exists(self):
        await self.event.finalize.exists()
        return await self._evt.finalize.wait()

    def set_info(self, count, terms):
        self.event.candidate.set_info(count, terms)
        self.event.vote.set_info(count, terms)

    def get_transaction(self):
        return self.event.transaction.get_list(60)

    def get_candidate(self, height) -> CandidateContext:
        return self.event.candidate.get(height)

    def get_vote(self, height) -> VoteContext:
        return self.event.vote.get(height)

    def get_confirm(self, height):
        return self.event.confirm.get(height)

    def get_finalize_block(self, height):
        return self.event.finalize.get(height)

    async def send(self, obj, exchange):
        event = getattr(self.event, exchange)
        await event.send(obj)



