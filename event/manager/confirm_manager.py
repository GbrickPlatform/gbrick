
import aioamqp
import json
import asyncio
import time

from utils.crypto.hash import sha3_hex
from utils.crypto.ec import verify
from utils.storage import Storage
from event.manager.base import BaseManager
from utils.exceptions import RoundError

from utils.config import MQ_HOST, MQ_SEED, MQ_PORT, MQ_USER, CM_EXCHANGE, EVENT_NAME


class ConfirmManager(BaseManager):
    _rep_count = 4
    _terms_consent = 3

    def __init__(self, name):
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

            await self._channel.exchange_declare(exchange_name=CM_EXCHANGE,
                                                 type_name='fanout')

            await self._channel.queue_declare(queue_name=EVENT_NAME(self.name),
                                              exclusive=True)

            await self._channel.queue_bind(exchange_name=CM_EXCHANGE,
                                           queue_name=EVENT_NAME(self.name),
                                           routing_key='')

            await self._channel.basic_consume(self.process_event,
                                              queue_name=EVENT_NAME(self.name),
                                              no_ack=True)
        except (aioamqp.ChannelClosed, aioamqp.AmqpClosedConnection):
            if not transport.is_closing():
                transport.close()

    async def process_event(self, channel, body, envelope, properties):
        # TODO: sender in validators. how to check validators?
        obj = json.loads(body)
        height, sender, blk_hash, sig = obj
        confirm_set = [height, sender, blk_hash]
        confirm_hash = sha3_hex(','.join(confirm_set))
        await verify(confirm_hash, sig.encode(), sender.encode())

        self.storage[(int(height), sender.encode())] = blk_hash.encode()

    async def send(self, obj):
        await self._channel.basic_publish(json.dumps(obj),
                                          exchange_name=CM_EXCHANGE,
                                          routing_key='')

    def get(self, height):
        """ return storage that height in storage
        :param height: round height
        :return: Union[NoReturn, (set_hash, set_sender)]
        >>> storage = {(height, sedner): block_hash, ...}
        >>> set(hashs), set(senders)
        1. one block selected
        2. block selected above quorum
        3. quorum crash is occur to exception(RoundError)

        """
        confirm_senders = []
        confirm_hash = []
        for k, v in self.storage.items():
            _height, sender = k
            if int(height) == _height:
                confirm_senders.append(sender)
                confirm_hash.append(v)  # candidate hash

        set_confirm_hash = set(confirm_hash)
        set_senders = set(confirm_senders)

        if len(set_senders) < self._terms_consent:
            raise RoundError("confirm all aggregate. "
                             "confirm sender: {}".format(len(set_senders)))

        if len(set_confirm_hash) == 1:
            return set_confirm_hash.pop(), set_senders
        elif len(set_confirm_hash) > 1:
            for set_hash in set_confirm_hash:
                count = confirm_hash.count(set_hash)
                if count >= self._terms_consent:
                    return set_hash, set_senders

        raise RoundError("confirm: all aggregate or nothing. "
                         "{}".format(set_confirm_hash))

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
                else:
                    raise RoundError(
                        "candidate manager: is not terms of min {}".format(len(self.storage))
                    )

    def clear(self, block):
        delete_set = []
        if len(self.storage) >= 1:
            for k, v in self.storage.items():
                height, sender = k
                if int(height) <= block.height:
                    delete_set.append(k)
            self.storage.delete_keys(delete_set)



