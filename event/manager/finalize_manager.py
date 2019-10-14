
import aioamqp
import json
import asyncio

from gbrick.types.deserializer import deserialize_block
from gbrick.validation import validate_finalize
from utils.exceptions import FinalizeError
from event.manager.base import BaseManager

from utils.config import MQ_HOST, MQ_SEED, MQ_PORT, MQ_USER, FN_EXCHANGE, EVENT_NAME


class FinalizeManager(BaseManager):

    def __init__(self, name):
        self.name = name
        self._event_storage = []

    @property
    def storage(self):
        return self._event_storage

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

            await self._channel.exchange_declare(exchange_name=FN_EXCHANGE,
                                                 type_name='fanout')

            await self._channel.queue_declare(queue_name=EVENT_NAME(self.name),
                                              exclusive=True)

            await self._channel.queue_bind(exchange_name=FN_EXCHANGE,
                                           queue_name=EVENT_NAME(self.name),
                                           routing_key='')

            await self._channel.basic_consume(self.process_event,
                                              queue_name=EVENT_NAME(self.name),
                                              no_ack=True)
        except (aioamqp.ChannelClosed, aioamqp.AmqpClosedConnection):
            if not transport.is_closing():
                transport.close()

    async def process_event(self, channel, body, envelope, properties):
        dict_obj = json.loads(body)
        block = deserialize_block(dict_obj)
        await validate_finalize(block)
        self.storage.append(block)

    async def send(self, obj):
        await self._channel.basic_publish(obj.to_json(),
                                          exchange_name=FN_EXCHANGE,
                                          routing_key='')

    def get(self, height):
        blk = self.storage.pop(0)

        if blk.height > height:
            # finality problem
            raise FinalizeError(
                "current height: {}, "
                "block height: {}".format(
                    height, blk.height
                )
            )
        elif blk.height < height:
            self.clear(blk)
            blk = self.storage.pop(0)
            if blk.height == height:
                return blk.copy()
            else:
                # sync
                raise FinalizeError

        if blk.height == height:
            return blk.copy()

    async def exists(self):
        while True:
            await asyncio.sleep(0.05)
            if len(self.storage) == 1:
                self._evt.set()
                return
            elif len(self.storage) > 1:
                raise AttributeError

    def clear(self, block):
        if len(self.storage) >= 1:
            for b in self.storage.copy():
                if b.height <= block.height:
                    self.storage.remove(b)



