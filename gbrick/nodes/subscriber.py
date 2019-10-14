
import asyncio
import datetime

from gbrick.chains.base import BaseChain
from event.base import BaseEvent
from gbrick.nodes.base import BaseNode
from utils.exceptions import FinalizeError, ValidationError
from utils.util import chain_information
from utils.logger import getLogger
from weakref import WeakSet


class Subscriber(BaseNode):
    _logger = None

    def __init__(self, chain, event, syncer):
        self._chain = chain
        self._event = event
        self._syncer = syncer
        self._task = WeakSet()

    @property
    def chain(self) -> BaseChain:
        return self._chain

    @property
    def event(self) -> BaseEvent:
        return self._event

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger('node')
        return self._logger

    def syncer_run(self):
        asyncio.ensure_future(self._syncer.load())

    async def event_finalize(self):
        return await self.event.finalize_exists()

    async def finalize(self, blk):
        await self.chain.finalize(blk)

    def get_finalize(self, permit_header):
        return self.event.get_finalize_block(permit_header.num_height + 1)

    async def accumulated_processing(self):
        self.logger.info('accumulated block processing... start at {}'.format(self.chain.height))
        try:
            while True:
                permit_header = self.chain.get_header_from_height(self.chain.height)
                blk = self.get_finalize(permit_header)
                try:
                    await self.finalize(blk)
                except ValidationError:
                    continue
                await self.event.clear(self.chain, blk)
        except IndexError:
            return

    async def prepare_node_synchronization(self):
        await self._syncer.run()

    async def _run(self):
        self.syncer_run()
        self.event.prepare(self.chain)
        await self._worker()

    async def _worker(self):
        await self.prepare_node_synchronization()
        while True:
            chain_information(self.chain, self.chain.logger)
            permit_header = self.chain.get_header_from_height(self.chain.height)
            try:
                await self.event_finalize()
                final_blk = self.get_finalize(permit_header)
            except (FinalizeError, ValidationError):
                self.logger.info("sync-start at "
                                 "{}, {}".format(self.chain.height, datetime.datetime.now()))
                await self._syncer.run()
            except AttributeError:
                await self.accumulated_processing()
            else:
                await self.finalize(final_blk)
                await self.event.clear(self.chain, final_blk)

