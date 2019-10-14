
import logging
import os

from logging import (
    Formatter,
    StreamHandler
)

from logging.handlers import TimedRotatingFileHandler
from utils.config import ROOT_DIR


def get_formatter():
    fmt = Formatter(
        '(%(levelname)s)%(asctime)s:' '%(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return fmt


def get_stream_handler(level, fmt):
    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(fmt)
    return handler


def get_file_handler(file, fmt):
    handler = TimedRotatingFileHandler(filename=file,
                                       backupCount=3,
                                       when='midnight')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(fmt)
    return handler


def getLogger(name):
    path = os.path.join(ROOT_DIR, 'logs')
    file = os.path.join(path, str(name) + '.log')
    if not os.path.isdir(path):
        os.mkdir(path)
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    fmt = get_formatter()
    sh = get_stream_handler(logging.INFO, fmt)
    fh = get_file_handler(file, fmt)
    _logger.addHandler(sh)
    _logger.addHandler(fh)

    return _logger

