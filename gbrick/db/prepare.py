
from gbrick.db.base import DB
from gbrick.db import (
    ChainDB, StateDB
)


def prepare_chain_db(db) -> ChainDB:
    return ChainDB(db=db)


def prepare_state_db(db) -> StateDB:
    return StateDB(db=db)


def prepare_database(path_class):
    """ prepare to db class

    :param path path_class: path class
    :return: db_context class
    """

    class DBContext:
        __slots__ = ('chain', 'state')

        def __init__(self, path):
            db_class = (
                prepare_chain_db,
                prepare_state_db,
            )
            for name, path, make_db in zip(path.__slots__[:-2],
                                           path,
                                           db_class):
                base_db = DB(path)
                setattr(self, name, make_db(base_db))

    return DBContext(path_class)

