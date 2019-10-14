
import asyncio

from utils.exceptions import NotInputSeed
from gbrick.nodes.prepare import (
    prepare_node,
    prepare_api_v1,
    prepare_api_v2,
)


MAIN_CEREMONY = "\n"+"\n".join((
    r" _______ _            _       _       ",
    r"|  ___  | |          |_|     | |      ",
    r"| |   |_| |      ____ _  ____| | __   ",
    r"| |   __| |____ |  __| |/ ___| |/ /   ",
    r"| |  |_ |  __  \| |  | | |   |   |    ",
    r"|  \__| | |__|  | |  | | |___| |\ \   ",
    r" \______|_____ /|_|  |_|\____|_| \_\  ",
)) + "\n"


def prepare_service(logger, loop, parser) -> None:
    """ prepare to gbrick service
    prepare to chain, node, rpc

    Args:
        :logger (Logger): main logger.
        :loop (EventLoop): event loop.
        :parser (ArgumentParser): argument parser.
    Returns:
        None
    """
    logger.info(MAIN_CEREMONY)
    logger.info('starting...  service')

    arguments = parser.parse_args()
    if not arguments.seed:
        raise NotInputSeed("seed not input, please input to seed")

    node = prepare_node(arguments.seed, loop, arguments.node_dir)
    logger.info("login-user   : {}".format(node.chain.nodebase.decode()))

    asyncio.ensure_future(node.run(), loop=loop)

    prepare_api_v1(loop)
    # loop.run_in_executor(None, prepare_api_v2, node.chain, node.event)

