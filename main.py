
import argparse
import asyncio

from gbrick.main import prepare_service
from utils.logger import getLogger


def argument_parser():
    parse = argparse.ArgumentParser(description='gbrick app.')
    parse.add_argument('-d', '--node_dir', type=str, help="private-key saved directory, "
                                                          "default path to if not input. ")
    parse.add_argument('-s', '--seed', type=str, help="private-key password, "
                                                      "required input information")
    return parse


def app(event_loop):
    # main  -> put arguments.
    logger = getLogger('main')
    parser = argument_parser()

    try:
        prepare_service(logger, event_loop, parser)
    except KeyboardInterrupt:
        logger.info('service end, reason: keyboard interrupt')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app(loop)
    loop.run_forever()
