
from utils.crypto.hash import sha3_hex
from gbrick.types.base import BaseVote


class Vote(BaseVote):

    @property
    def creator(self):
        return self.address_creator

    @property
    def hash(self):
        setup = self.__slots__[:-2]
        attr = self.serialize(setup)
        return sha3_hex(','.join(attr).encode())


