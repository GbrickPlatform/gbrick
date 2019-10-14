import aioamqp
import json
import asyncio
import time

from utils.storage import Storage
from event.manager.base import BaseManager
from gbrick.types.deserializer import deserialize_vote
from gbrick.validation import validate_vote
from utils.logger import getLogger
from event.event_context import VoteContext
from utils.exceptions import RoundError

from utils.config import MQ_HOST, MQ_SEED, MQ_PORT, MQ_USER, VT_EXCHANGE, EVENT_NAME


class VoteManager(BaseManager):
    _rep_count = 4
    _terms_consent = 3

    def __init__(self, name):
        self.logger = getLogger('voteManager')
        self.name = name
        self._event_storage = Storage()

    @property
    def storage(self):
        return self._event_storage

    def set_event(self, evt):
        self._evt = evt

    def set_info(self, count, terms):
        self._rep_count = count
        self._terms_consent = terms

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

            await self._channel.exchange_declare(exchange_name=VT_EXCHANGE,
                                                 type_name='fanout')

            await self._channel.queue_declare(queue_name=EVENT_NAME(self.name),
                                              exclusive=True)

            await self._channel.queue_bind(exchange_name=VT_EXCHANGE,
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
        dict_obj = json.loads(body)
        vote = deserialize_vote(dict_obj)
        await validate_vote(vote)
        self.storage[(vote.num_block_height, vote.address_creator)] = vote

    async def send(self, obj):
        await self._channel.basic_publish(obj.to_json(),
                                          exchange_name=VT_EXCHANGE,
                                          routing_key='')

    def get(self, height) -> VoteContext:
        """
        :param height: round height
        :return: vote context
        >>> storage = {(height, vote sender): Vote, ...}
        """
        votes = {}
        creators = []
        log = []
        for vote in self.storage.range('all'):
            if height == vote.num_block_height:
                vt = vote.copy()
                votes[(vt.num_block_height, vt.address_creator)] = vt
                creators.append(vt.address_creator)
                log.append(vt.hash_candidate_block[:8])
        self.logger.debug('vote context: {}'.format(log))

        context = VoteContext()
        context.set_height(height)
        context.set_timestamp(time.time())
        context.set_creators(creators)
        context.set(votes)
        return context

    async def exists(self):
        n = time.time()
        while True:
            await asyncio.sleep(0.01)
            if len(self.storage) == self._rep_count:
                self._evt.set()
                return

            if time.time() - n >= 2:
                if len(self.storage) >= self._terms_consent:
                    self._evt.set()
                    return
                raise RoundError(
                    "vote manager: is not terms of min{}".format(len(self.storage))
                )

    def clear(self, block):
        if len(self.storage) >= 1:
            for k, v in self.storage.items():
                height, creator = k
                if int(height) <= block.height:
                    self.storage.delete(k)

