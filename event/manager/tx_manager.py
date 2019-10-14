
import aioamqp
import json
import asyncio

from utils.storage import Storage
from utils.util import time_distance
from event.manager.base import BaseManager
from gbrick.validation import validate_transaction
from gbrick.types.deserializer import deserialize_transaction
from weakref import WeakSet

from utils.config import MQ_HOST, MQ_SEED, MQ_PORT, MQ_USER, TX_EXCHANGE, EVENT_NAME


class TransactionManager(BaseManager):
    """ Transaction MQ Manager
    """

    def __init__(self, name):
        self.name = name
        self._task = WeakSet()
        self._event_storage = Storage()

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
        except aioamqp.AmqpClosedConnection as e:
            print('TransactionManager ClosedConnection : ', str(e))
            # TODO:  execption 처리.
            return

        try:
            self._channel = await protocol.channel()

            await self._channel.exchange_declare(exchange_name=TX_EXCHANGE,
                                                 type_name='fanout')

            await self._channel.queue_declare(queue_name=EVENT_NAME(self.name),
                                              exclusive=True)

            await self._channel.queue_bind(exchange_name=TX_EXCHANGE,
                                           queue_name=EVENT_NAME(self.name),
                                           routing_key='')

            await self._channel.basic_consume(self.process_event,
                                              queue_name=EVENT_NAME(self.name),
                                              no_ack=True)
        except (aioamqp.ChannelClosed, aioamqp.AmqpClosedConnection):
            if not transport.is_closing():
                transport.close()

    async def process_event(self, channel, body, envelope, properties):
        self._task.add(asyncio.ensure_future(self._process_event(body)))

    async def _process_event(self, body):
        """ transaction data processing
        :param body: tx-data
        """
        dict_obj = json.loads(body)
        try:
            transaction = deserialize_transaction(dict_obj)
        except ValueError:
            return
        else:
            if time_distance(transaction.timestamp) < 600:
                await validate_transaction(transaction)
                self.storage[transaction.hash] = transaction  # pending.
                await asyncio.sleep(0.0001)

    async def send(self, obj):
        await self._channel.basic_publish(obj.to_json(),
                                          exchange_name=TX_EXCHANGE,
                                          routing_key='')

    def get_list(self, length: int = 60):
        """
        :param length: data-len
        :return: tx-list
        """
        transaction_list = []
        for tx in self.storage.range(length):
            transaction_list.append(tx.copy())
        return transaction_list

    async def exists(self):
        while True:
            await asyncio.sleep(0.01)
            if len(self.storage) >= 1:
                self._evt.set()
                return

    def clear(self, block):
        complete_tx = [tx.hash for tx in block.list_transactions]
        self.storage.delete_keys(complete_tx)

