
from gbrick.types.base import BaseTransaction, BaseReceipt
from utils.crypto.hash import sha3_hex


class Transaction(BaseTransaction):

    @property
    def hash(self):
        setup = self.__slots__[:-2]
        attr = self.serialize(setup)
        return sha3_hex(','.join(attr).encode())


class Receipt(BaseReceipt):

    @property
    def hash(self):
        setup = self.__slots__
        attr = self.serialize(setup)
        return sha3_hex(','.join(attr).encode())


