
import datetime

from utils.address import load_node_base
from utils.crypto.ec import ECSigner
from gbrick.chains.chain import Chain
from gbrick.db.prepare import prepare_database
from event.event import GBrickEvent
from gbrick.nodes.subscriber import Subscriber
from gbrick.nodes.validator import Validator
from utils.util import get_path
from event.syncer.prepare import prepare_syncer
from event.api.v1 import APIv1
from gbrick.api.service import Service
from event.rpc.app import RPC


def prepare_chain(seed, loop, node_dir=None) -> Chain:
    """ Prepare to chain class
    :param str seed: keystore password

    :param EventLoop loop: event loop.
    :param Union[None, str] node_dir: directory path
    :return: Chain class
    >>> prepare_chain('seed', EventLoop, Optional[Union[None, './test']])
    >>> return Chain
    """
    start_time = datetime.datetime.now()
    config_path = get_path(node_dir)

    db_context = prepare_database(config_path)

    node_base, node_key = load_node_base(config_path.node, seed)

    signer = ECSigner(node_key)

    chain = Chain(db_context=db_context,
                  signer=signer,
                  node_base=node_base,
                  start_at=start_time,
                  loop=loop)

    if not chain.block_from_genesis():
        height = chain.height
        header = chain.get_header_from_height(height)
        db_context.state.set_root(header.hash_state_root)

    return chain


def prepare_event(chain: Chain) -> GBrickEvent:
    """ Prepare to event class
    :param Chain chain: chain class
    :return: event class
    """
    count, terms = chain.get_validator_count()
    event = GBrickEvent()
    event.set_info(count, terms)
    return event


def prepare_node(seed, loop, node_dir=None):
    """ Prepare to chain, event, syncer classes
    :param str seed:  keystore password
    :param asyncio.AbstractEventLoop loop: event loop
    :param Union[None, str] node_dir: directory path
    :return: node class
    >>> prepare_node(b'seed', EventLoop, Optional[Union[None, './test/']])
    >>> return Union[Validator, Subscriber]
    """

    chain = prepare_chain(seed, loop, node_dir)  # todo: 여기까지
    event = prepare_event(chain)
    syncer = prepare_syncer(chain, event)

    if chain.is_validator:
        return Validator(chain, event, syncer)
    elif not chain.is_validator:
        return Subscriber(chain, event, syncer)
    else:
        raise TypeError("unexpected node type")


def prepare_api_v1(loop) -> None:
    service = APIv1()
    service.run(loop)


def prepare_api_v2(chain, event) -> None:
    service = Service(chain, event)
    service.start()


def prepare_rpc() -> None:
    rpc = RPC()
    rpc.run()




