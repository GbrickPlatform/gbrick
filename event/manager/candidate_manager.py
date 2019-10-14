
import aioamqp
import json
import asyncio
import time

from utils.storage import Storage
from event.manager.base import BaseManager
from gbrick.types.deserializer import deserialize_block
from gbrick.validation import validate_candidate
from utils.exceptions import RoundError
from event.event_context import CandidateContext

from utils.config import MQ_HOST, MQ_SEED, MQ_PORT, MQ_USER, CD_EXCHANGE, EVENT_NAME


class CandidateManager(BaseManager):
    _rep_count = 4
    _terms_consent = 3

    def __init__(self, name):
        self.name = name
        self._event_storage = Storage()

    @property
    def storage(self):
        return self._event_storage

    def set_info(self, count, terms):
        self._rep_count = count
        self._terms_consent = terms

    def set_event(self, evt):
        self._evt = evt

    async def event_run(self):
        try:
            transport, protocol = await aioamqp.connect(host=MQ_HOST,
                                                        port=MQ_PORT,
                                                        login=MQ_USER,
                                                        password=MQ_SEED,
                                                        login_method='PLAIN')
        except aioamqp.AmqpClosedConnection:
            return

        try:
            self._channel = await protocol.channel()

            await self._channel.exchange_declare(exchange_name=CD_EXCHANGE,
                                                 type_name='fanout')

            await self._channel.queue_declare(queue_name=EVENT_NAME(self.name),
                                              exclusive=True)

            await self._channel.queue_bind(exchange_name=CD_EXCHANGE,
                                           queue_name=EVENT_NAME(self.name),
                                           routing_key='')

            await self._channel.basic_consume(self.process_event,
                                              queue_name=EVENT_NAME(self.name),
                                              no_ack=True)
        except (aioamqp.ChannelClosed, aioamqp.AmqpClosedConnection):
            if not transport.is_closing():
                transport.close()
        # except ValidationError:

    async def process_event(self, channel, body, envelope, properties):
        """ block data processing
        :param channel:
        :param body: candidate block data
        :param envelope:
        :param properties:
        :return:
        """
        dict_obj = json.loads(body)
        candidate = deserialize_block(dict_obj)
        await validate_candidate(candidate)
        self.storage[(candidate.height, candidate.creator)] = candidate
        await asyncio.sleep(0)

    async def send(self, obj):
        await self._channel.basic_publish(obj.to_json(),
                                          exchange_name=CD_EXCHANGE,
                                          routing_key='')

    def get(self, height) -> CandidateContext:
        """ return storage that height in storage
        :param height: round height
        :return: candidate context
        >>> storage = { (height, creator): Block, ...}
        >>> get(height)
        height in keys -> return context
        >>> context_object(height, creators, timestamps, blocks)
        height not in keys -> return
        >>> context_object(height, [], [], {})
        """
        blocks = {}
        times = []
        creators = []

        for block in self.storage.range('all'):
            if height == block.header.num_height:
                blk = block.copy()
                blocks[(blk.height, blk.creator)] = blk
                times.append(blk.header.timestamp)
                creators.append(blk.creator)

        context = CandidateContext()
        context.set_height(height)
        context.set_creators(creators)
        context.set_timestamp(times)
        context.set(blocks)
        return context

    async def exists(self):
        n = time.time()
        while True:
            await asyncio.sleep(0.01)
            if len(self.storage) == self._rep_count:
                self._evt.set()
                return

            if time.time() - n >= 3:
                if len(self.storage) >= self._terms_consent:
                    self._evt.set()
                    return
                else:
                    raise RoundError(
                        "candidate manager: is not terms of min {}".format(len(self.storage))
                    )

    def clear(self, block):
        delete_set = []
        if len(self.storage) >= 1:
            for k, v in self.storage.items():
                height, creator = k
                if int(height) <= block.height:
                    delete_set.append(k)
            self.storage.delete_keys(delete_set)



