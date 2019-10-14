
import os
import datetime
import time
import math
import asyncio

from utils.crypto.hash import sha3_hex
from utils.config import (
    DATABASE, ROOT_DIR, DB_DIR,
    NODE_DIR
)


def async_queue_iterable(async_queue):
    """ async queue iterator
    :param asyncio.Queue async_queue: async queue
    :return: async queue iterable class
    """
    class AsyncQueueIterable:
        def __init__(self, queue):
            self.queue = queue

        async def put(self, item):
            await self.queue.put(item)
            await asyncio.sleep(0)

        async def get(self):
            return await self.queue.get()

        def size(self):
            return self.queue.qsize()

        def __aiter__(self):
            return self

        async def __anext__(self):
            await asyncio.sleep(0)
            return await self.get()

    return AsyncQueueIterable(async_queue)


def extract_values(value, dict_slots):
    """ extract dictionary values
    :param dict value: extract dictionary data
    :param list dict_slots: immutable type field
    :return: extract class
    """
    class Extract:
        __slots__ = tuple((str(k) for k in dict_slots))

        def __init__(self, data):
            for k in dict_slots:
                setattr(self, k, data.get(k))

    return Extract(value)


def get_path(node_directory=None):
    """ necessary path to node
    :param Union[None, str] node_directory: directory path
    :return: path class
    """
    class Path:
        __slots__ = DATABASE + (NODE_DIR, '_path_data')

        def __init__(self, data: dict):
            self._path_data = data
            for k, v in self._path_data.items():
                setattr(self, k, v)

        def __iter__(self):
            for k, v in self._path_data.items():
                yield v

    values = {}
    db_path = os.path.join(ROOT_DIR, DB_DIR)
    if not os.path.isdir(db_path):
        os.mkdir(db_path)

    for dir_path in DATABASE:
        merge_path = os.path.join(db_path, dir_path)
        values[dir_path] = merge_path

    if node_directory is None:
        node_directory = os.path.join(ROOT_DIR, NODE_DIR)
        if not os.path.isdir(node_directory):
            os.mkdir(node_directory)

    elif node_directory:
        if not os.path.isdir(node_directory):
            raise FileNotFoundError

    values[NODE_DIR] = node_directory

    return Path(values)


def _ord(x):
    if isinstance(x, int):
        return x
    else:
        return ord(x)


def bytes_to_int(x):
    k = 0
    for i in x:
        k = k*256 + _ord(i)
    return k


def int_to_bytes32(x):
    return x.to_bytes(32, byteorder='big')


def get_trie_key(value: bytes):
    return sha3_hex(value).decode()


def time_distance(timestamp):
    return math.floor(time.time() - timestamp)


def chain_information(chain, logger):
    mode = 'validator' if chain.is_validator else 'subscriber'
    logger.info("node-mode   : {}".format(mode))
    logger.info("node-uptime : {}".format(chain.uptime))
    logger.info("last-height : {}".format(chain.height))


def uptime(strt):
    date = datetime.datetime.now() - strt
    h, r = divmod(date.seconds, 3600)
    m, s = divmod(r, 60)
    return "%dd-%02d:%02d:%02d" % (date.days, h, m, s)


def chunks(o, e):
    for i in range(0, len(o), e):
        yield o[i:i+e]


def m_tree(p_list: list):
    if len(p_list) == 0:
        return b''

    if len(p_list) == 1:
        return p_list[0]

    sub_tree = []
    for i in chunks(p_list, 2):
        if len(i) == 2:
            sub_tree.append(
                sha3_hex(i[0]+i[1])
            )
        else:
            sub_tree.append(
                sha3_hex(i[0]+i[0])
            )

    return m_tree(sub_tree)


