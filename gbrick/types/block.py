
from utils.crypto.hash import sha3_hex
from gbrick.types.base import BaseHeader, BaseBlock
from utils.util import extract_values


class BlockHeader(BaseHeader):

    @property
    def pre_hash(self):
        setup = self.__slots__[:7]
        attr = self.serialize(setup)
        return sha3_hex(','.join(attr).encode())

    @property
    def hash(self):
        setup = self.__slots__[:-2]
        attr = self.serialize(setup)
        return sha3_hex(','.join(attr).encode())


class Block(BaseBlock):

    def to_dict(self):
        obj = super().to_dict()
        ex = extract_values(obj, ['header', 'transaction_list', 'vote_list'])
        obj['header'] = ex.header.to_dict()
        obj['transaction_list'] = [tx.to_dict() for tx in ex.transaction_list]
        obj['vote_list'] = [vt.to_dict() for vt in ex.vote_list]
        return obj

    @property
    def previous(self):
        return self.header.hash_prev_block

    @property
    def height(self):
        return self.header.num_height

    @property
    def creator(self):
        return self.header.address_creator

    @property
    def pre_hash(self):
        header = getattr(self, 'header')
        return header.pre_hash

    @property
    def hash(self):
        header = getattr(self, 'header')
        return header.hash

    def __eq__(self, block):
        return self.pre_hash == block.pre_hash


